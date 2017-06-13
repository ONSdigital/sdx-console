import json
import logging
import uuid

from datetime import datetime
from flask import render_template
from flask import request
import flask_security
import requests
from sqlalchemy import func
from sqlalchemy.exc import DataError, SQLAlchemyError
from structlog import wrap_logger

from console.database import db, SurveyResponse
from console import app
from console import settings
from console.encrypter import Encrypter
from console.helpers.exceptions import ClientError, ServiceError
from console.queue_publisher import QueuePublisher


logger = wrap_logger(logging.getLogger(__name__))


@app.route('/', methods=['GET'])
@flask_security.login_required
def home():
    return "stuff"


def send_data(url, data=None, request_type="POST"):
    try:
        if request_type == "POST":
            logger.info("Posting data to " + url)
            r = requests.post(url, data)
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


def get_filtered_responses(tx_id, ru_ref, survey_id, datetime_earliest, datetime_latest):
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


def encrypt_data(unencrypted_json):
    encrypter = Encrypter()
    encrypted_data = encrypter.encrypt(unencrypted_json)

    return encrypted_data


def get_publisher():
    urls = settings.RABBIT_URLS
    queue = settings.RABBIT_SURVEY_QUEUE
    collect_publisher = QueuePublisher(logger, urls, queue)

    return collect_publisher


def store_result(publisher, json_string):
    tx_id = str(uuid.uuid4())
    json_string['tx_id'] = tx_id
    json_string['survey_id'] = str(json_string['survey_id'])
    encrypted_data = encrypt_data(json_string)

    publisher.publish_message(encrypted_data, headers={'tx_id': tx_id})


@app.route('/store', methods=['GET', 'POST'])
@flask_security.roles_required('SDX-Developer')
def store():
    if request.method == 'POST':
        collect_publisher = get_publisher()
        collect_publisher._connect()

        json_string = request.form['json_data']
        corrected_json_string = json_string.replace("'", '"')
        unencrypted_json = json.loads(corrected_json_string)

        if isinstance(unencrypted_json, list):
            for string in unencrypted_json:
                store_result(collect_publisher, string)
        else:
            store_result(collect_publisher, unencrypted_json)

        collect_publisher._disconnect()

        return render_template('store.html')

    else:
        tx_id = request.args.get('tx_id', type=str, default='')
        ru_ref = request.args.get('ru_ref', type=str, default='')
        survey_id = request.args.get('survey_id', type=str, default='')
        datetime_earliest = request.args.get('datetime_earliest', type=str, default='')
        datetime_latest = request.args.get('datetime_latest', type=str, default='')

        store_data = get_filtered_responses(tx_id, ru_ref, survey_id, datetime_earliest, datetime_latest)

        json_array = []
        for item in store_data:
            json_data = item.data
            json_array.append(json_data)

        return render_template('store.html', data=json_array)
