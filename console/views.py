import logging
import requests

from datetime import datetime
from flask import render_template
from flask import request
import flask_security
from sqlalchemy import cast, DateTime
from sqlalchemy.exc import SQLAlchemyError
from structlog import wrap_logger

from console.database import db, SurveyResponse
from console import app
from console import settings
from console.helpers.exceptions import ClientError, ServiceError

logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
logger = wrap_logger(logging.getLogger(__name__))


@app.route('/', methods=['GET'])
@flask_security.login_required
def home():
    return "stuff"


def send_data(url, data=None, request_type="POST"):
    try:
        if request_type == "POST":
            logger.info("POSTING DATA")
            r = requests.post(url, data)
        else:
            r = requests.get(url)
    except requests.exceptions.ConnectionError as e:
        logger.error('Could not connect to ' + url, response="Connection error")
        raise e

    if 199 < r.status_code < 300:
        logger.info('Returned from ' + url, response=r.reason, status_code=r.status_code)
    elif 399 < r.status_code < 500:
        logger.error('Returned from ' + url, response=r.reason, status_code=r.status_code)
        raise ClientError
    elif r.status_code > 499:
        logger.error('Returned from ' + url, response=r.reason, status_code=r.status_code)
        raise ServiceError

    return r


@app.route('/decrypt', methods=['POST', 'GET'])
@flask_security.roles_required('SDX-Developer')
def decrypt():
    logger.bind(user=flask_security.core.current_user.email)
    if request.method == "POST":
        data = request.form['EncryptedData']
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


# def get_all_responses():
#     try:
#         data = SurveyResponse.query.all()
#     except SQLAlchemyError:
#         logger.error('SQLAlchemyError')
#     return data
#
#
# def get_store_responses(tx_id, ru_ref, survey_id, datetime_earliest, datetime_latest):
#     responses = get_all_responses()
#     store_data = []
#     for response in responses:
#         store_data.append(response.data)
#
#     filtered_data = []
#     for data in store_data:
#         if (tx_id == '') or (data['tx_id'] == tx_id):
#             if (ru_ref == '') or (data['metadata']['ru_ref'] == ru_ref):
#                 if (survey_id == '') or (data['survey_id'] == survey_id):
#                     filtered_data.append(data)
#
#     datetime_earliest_f = datetime.strptime(datetime_earliest, "%Y-%m-%dT%H:%M")
#     datetime_latest_f = datetime.strptime(datetime_latest, "%Y-%m-%dT%H:%M")
#
#     final_data = []
#     for data in filtered_data:
#         data_datetime_string = data['submitted_at'][:19]
#         data_datetime = datetime.strptime(data_datetime_string, "%Y-%m-%dT%H:%M:%S")
#         if (data_datetime > datetime_earliest_f) and (data_datetime < datetime_latest_f):
#             final_data.append(data)
#
#     return final_data

def get_filtered_responses(tx_id, ru_ref, survey_id, datetime_earliest, datetime_latest):
    q = db.session.query(SurveyResponse)
    if tx_id != None and tx_id != '':
        q = q.filter(SurveyResponse.tx_id == tx_id)
    if ru_ref != None and ru_ref != '':
        logger.info('hit1')
        q = q.filter(SurveyResponse.data["metadata"]["ru_ref"].astext == ru_ref)
    if survey_id != None and survey_id != '':
        logger.info('hit2')
        q = q.filter(SurveyResponse.data["survey_id"].astext == survey_id)
    if datetime_earliest != None and datetime_earliest != '':
        datetime_earliest_f = datetime.strptime(datetime_earliest, "%Y-%m-%dT%H:%M")
        q = q.filter(cast(SurveyResponse.data["submitted_at"], DateTime) < datetime_earliest_f)
    return q.all()


@app.route('/store', methods=['GET'])
@flask_security.roles_required('SDX-Developer')
def store():
    tx_id = request.args.get('tx_id', type=str, default=None)
    ru_ref = request.args.get('ru_ref', type=str, default=None)
    survey_id = request.args.get('survey_id', type=str, default=None)
    datetime_earliest = request.args.get('datetime_earliest', type=str, default=None)
    datetime_latest = request.args.get('datetime_latest', type=str, default=None)

    store_data = get_filtered_responses(tx_id, ru_ref, survey_id, datetime_earliest, datetime_latest)
    logger.info('testtest1' + str(store_data))
    return render_template('store.html', data=store_data)
