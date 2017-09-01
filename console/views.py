import ast
import json
import logging
import math

from datetime import datetime
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
import flask_security
import requests
from sqlalchemy import func
from sqlalchemy.exc import DataError, SQLAlchemyError
from structlog import wrap_logger

from console.database import db, SurveyResponse, create_dev_user
from console.forms import NewUserForm
from console import app
from console import settings
from console.helpers.exceptions import ClientError, ResponseError, ServiceError


logger = wrap_logger(logging.getLogger(__name__))


@app.errorhandler(ResponseError)
def handle_invalid_usage(error):
    json_error = {"message": error.message, "status_code": error.status_code}
    return jsonify(json_error)


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({'status': 'OK'})


@app.route('/', methods=['GET'])
def home():
    return "home"


def send_data(logger, url, data=None, json=None, request_type="POST"):
    response_logger = logger.bind(url=url)
    try:
        if request_type == "POST":
            response_logger.info("Sending POST request")
            if data:
                r = requests.post(url, data=data)
            elif json:
                r = requests.post(url, json=json)
        elif request_type == "GET":
            response_logger.info("Sending GET request")
            r = requests.get(url)
    except requests.exceptions.ConnectionError as e:
        response_logger.error("Failed to connect to service", response="Connection error")
        raise e

    if 199 < r.status_code < 300:
        logger.info('Returned from service', response=r.reason, status_code=r.status_code)
    elif 399 < r.status_code < 500:
        logger.error('Returned from service', response=r.reason, status_code=r.status_code)
        raise ClientError(url=url, message=r.reason, status_code=r.status_code)
    elif r.status_code > 499:
        logger.error('Returned from service', response=r.reason, status_code=r.status_code)
        raise ServiceError(url=url, message=r.reason, status_code=r.status_code)

    return r


@app.route('/decrypt', methods=['POST', 'GET'])
@flask_security.login_required
def decrypt():
    audited_logger = logger.bind(user=flask_security.core.current_user.email)
    if request.method == "POST":
        data = request.form.get('EncryptedData')
        url = settings.SDX_DECRYPT_URL
        decrypted_data = ""

        try:
            audited_logger.info("Posting data to sdx-decrypt")
            decrypt_response = send_data(logger=audited_logger, url=url, data=data, request_type="POST")
        except ClientError:
            error = 'Client error'
        except ServiceError:
            error = 'Service error'
        except requests.exceptions.ConnectionError:
            error = 'Connection error'
        else:
            decrypted_data = decrypt_response.text
            error = ""

        return render_template('decrypt.html', decrypted_data=decrypted_data, error=error)

    else:
        return render_template('decrypt.html')


def get_filtered_responses(logger, valid, tx_id, ru_ref, survey_id, datetime_earliest, datetime_latest):
    logger.info('Retrieving responses from sdx-store')
    try:
        q = db.session.query(SurveyResponse)
        if valid == "invalid":
            q = q.filter(SurveyResponse.invalid)
        elif valid == "valid":
            q = q.filter(not SurveyResponse.invalid)
        if tx_id != '':
            q = q.filter(SurveyResponse.tx_id == tx_id)
        if ru_ref != '':
            q = q.filter(SurveyResponse.data["metadata"]["ru_ref"].astext == ru_ref)
        if survey_id != '':
            q = q.filter(SurveyResponse.data["survey_id"].astext == survey_id)
        dt_column = func.date(SurveyResponse.data["submitted_at"].astext)
        if datetime_earliest:
            year = int(datetime_earliest[:4])
            month = int(datetime_earliest[5:7])
            day = int(datetime_earliest[8:10])
            hour = int(datetime_earliest[11:13])
            minute = int(datetime_earliest[14])
            q = q.filter(dt_column > datetime(year, month, day, hour, minute))
        if datetime_latest:
            year = int(datetime_latest[:4])
            month = int(datetime_latest[5:7])
            day = int(datetime_latest[8:10])
            hour = int(datetime_latest[11:13])
            minute = int(datetime_latest[14])
            q = q.filter(dt_column < datetime(year, month, day, hour, minute))
        filtered_data = q.all()
    except DataError as e:
        logger.error("Invalid search term", error=e)
        return []
    except SQLAlchemyError as e:
        logger.error("Database error", error=e)
        return []

    return filtered_data


def reprocess_transaction(logger, json_data):
    logger.info("Reprocessing transaction", tx_id=json_data["tx_id"])
    if json_data.get("invalid"):
        del json_data["invalid"]
    validate_response = send_data(logger=logger, url=settings.SDX_VALIDATE_URL, json=json_data, request_type="POST")
    if validate_response != 200:
        json_data['invalid'] = "True"
    send_data(logger=logger, url=settings.SDX_STORE_URL, json=json_data, request_type="POST")


@app.route('/store/', defaults={'page': 0}, methods=['GET', 'POST'])
@app.route('/store/<page>', methods=['GET', 'POST'])
@flask_security.login_required
def store(page):
    audited_logger = logger.bind(user=flask_security.core.current_user.email)
    if request.method == 'POST':
        json_survey_data = request.form.get('json_data')
        if not json_survey_data:
            json_survey_data = request.form.get('json_data_list')
            if not json_survey_data:
                return url_for('store')
            json_survey_data = ast.literal_eval(json_survey_data)

        if isinstance(json_survey_data, list):
            audited_logger.info("Reprocessing multiple transactions")
            for json_data in json_survey_data:
                reprocess_transaction(audited_logger, json_data)
        else:
            json_single_data = json.loads(json_survey_data.replace("'", '"'))
            reprocess_transaction(audited_logger, json_single_data)
        return redirect(url_for('store'))

    else:
        valid = request.args.get('valid', type=str, default='')
        tx_id = request.args.get('tx_id', type=str, default='')
        ru_ref = request.args.get('ru_ref', type=str, default='')
        survey_id = request.args.get('survey_id', type=str, default='')
        datetime_earliest = request.args.get('datetime_earliest', type=str, default='')
        datetime_latest = request.args.get('datetime_latest', type=str, default='')
        store_data = get_filtered_responses(audited_logger, valid, tx_id, ru_ref, survey_id, datetime_earliest, datetime_latest)
        audited_logger.info("Successfully retireved responses")
        json_list = [item.data for item in store_data]
        no_pages = math.ceil(round(float(len(json_list) / 20)))

        return render_template('store.html', data=json_list, no_pages=no_pages, page=int(page))


@app.route('/storetest', methods=['GET'])
def storetest():

    def create_test_data(number):
        test_data = json.dumps(
            {
                "collection": {
                    "exercise_sid": "hfjdskf",
                    "instrument_id": "ce2016",
                    "period": "0616"
                },
                "data": {
                    "1": "2",
                    "2": "4",
                    "3": "2",
                    "4": "Y"
                },
                "metadata": {
                    "ru_ref": "12345678901a",
                    "user_id": "789473423"
                },
                "origin": "uk.gov.ons.edc.eq",
                "submitted_at": "2017-04-27T14:23:13+00:00",
                "survey_id": "1",
                "tx_id": "f088d89d-a367-876e-f29f-ae8f1a26" + str(number),
                "type": "uk.gov.ons.edc.eq:surveyresponse",
                "version": "0.0.1"
            })
        return test_data
    for i in range(1000, 1250):
        test_data = create_test_data(str(i))
        send_data(logger=logger, url=settings.SDX_STORE_URL, data=test_data, request_type="POST")

    return "data sent"


@app.route('/adduser', methods=['GET', 'POST'])
@flask_security.roles_required('Admin')
def add_user():
    form = NewUserForm()
    if request.method == 'POST':
        create_dev_user(form.email.data, form.password.data)
        return redirect(url_for('decrypt'))
    else:
        return render_template('adduser.html', form=form)