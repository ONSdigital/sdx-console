import json
import logging

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

from console.database import db, SurveyResponse
from console import app
from console import settings
from console.helpers.exceptions import ClientError, ExceptionReturn, ServiceError


logger = wrap_logger(logging.getLogger(__name__))


@app.errorhandler(ExceptionReturn)
def handle_invalid_usage(error):
    json_error = {"message": error.message, "status_code": error.status_code}
    return jsonify(json_error)


@app.route('/', methods=['GET'])
@flask_security.login_required
def home():
    return redirect(url_for('store'))


def send_data(url, data=None, json=None, request_type=None):
    try:
        if request_type == "POST":
            logger.info("Posting data to " + url)
            if data:
                r = requests.post(url, data=data)
            elif json:
                r = requests.post(url, json=json)
        else:
            logger.info("Sending GET request to " + url)
            r = requests.get(url)
    except requests.exceptions.ConnectionError as e:
        logger.error('Could not connect to ' + url, response="Connection error")
        raise e

    if 199 < r.status_code < 300:
        logger.info('Returned from ' + url, response=r.reason, status_code=r.status_code)
    elif 399 < r.status_code < 500:
        logger.error('Returned from ' + url, response=r.reason, status_code=r.status_code)
        raise ClientError(message=r.reason, status_code=r.status_code)
    elif r.status_code > 499:
        logger.error('Returned from ' + url, response=r.reason, status_code=r.status_code)
        raise ServiceError(message=r.reason, status_code=status_code)

    return r


@app.route('/decrypt', methods=['POST', 'GET'])
@flask_security.roles_required('SDX-Developer')
def decrypt():
    logger.bind(user=flask_security.core.current_user.email)
    if request.method == "POST":
        data = request.form.get('EncryptedData')
        url = settings.SDX_DECRYPT_URL
        decrypted_data = ""

        try:
            logger.info("Posting data to sdx-decrypt", user=flask_security.core.current_user.email)
            decrypt_response = send_data(url, data, "POST")
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


def get_filtered_responses(tx_id, ru_ref, survey_id, datetime_earliest, datetime_latest):
    logger.info('Retrieving responses from store')
    try:
        q = db.session.query(SurveyResponse)
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


def reprocess_transaction(json_data):
    logger.info('Reprocessing transaction', tx_id=json_data["tx_id"])
    if json_data.get("invalid"):
        del json_data["invalid"]
    validate_response = send_data(url=settings.SDX_VALIDATE_URL, json=json_data, request_type="POST")
    store_response = send_data(url=settings.SDX_STORE_URL, json=json_data, request_type="POST")

@app.route('/store/', methods=['GET', 'POST'])
@app.route('/store/<page>', methods=['GET', 'POST'])
@flask_security.roles_required('SDX-Developer')
def store(page=0):
    if request.method == 'POST':
        json_survey_data = request.form.get('json_data')
        if not json_survey_data:
            json_survey_data = request.form.get('json_data_list')
            if not json_survey_data:
                return url_for('store')
            json_survey_data = eval(json_survey_data)

        if isinstance(json_survey_data, list):
            logger.info('Reprocessing all results')
            for json_data in json_survey_data:
                reprocess_transaction(json_data)
        else:
            json_data = json.loads(json_survey_data.replace("'", '"'))
            reprocess_transaction(json_data)
        return redirect(url_for('store'))

    else:
        tx_id = request.args.get('tx_id', type=str, default='')
        ru_ref = request.args.get('ru_ref', type=str, default='')
        survey_id = request.args.get('survey_id', type=str, default='')
        datetime_earliest = request.args.get('datetime_earliest', type=str, default='')
        datetime_latest = request.args.get('datetime_latest', type=str, default='')

        store_data = get_filtered_responses(tx_id, ru_ref, survey_id, datetime_earliest, datetime_latest)

        json_list = [item.data for item in store_data]
        # no_pages = len(json_list)

        return render_template('store.html', data=json_list, no_pages=10, page=int(page))
