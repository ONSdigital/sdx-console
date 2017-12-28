import json
import logging.handlers
import os
import uuid

import flask_security
import requests
import yaml
from flask import Blueprint
from flask import jsonify
from flask import render_template
from flask import request
from structlog import wrap_logger

import console.settings as settings
from console.helpers.exceptions import ClientError, ServiceError
from sdc.crypto.encrypter import encrypt
from sdc.crypto.key_store import KeyStore
from sdc.rabbit import QueuePublisher

logger = wrap_logger(logging.getLogger(__name__))

submit_bp = Blueprint('submit_bp', __name__, static_folder='static', template_folder='templates')


def list_surveys():
    return sorted([f for f in os.listdir('console/static/surveys') if os.path.isfile(os.path.join('console/static/surveys', f))])


def send_payload(payload, tx_id, no_of_submissions=1):
    logger.debug(" [x] Sending encrypted Payload")

    publisher = QueuePublisher(settings.RABBIT_URLS, settings.RABBIT_QUEUE)
    for _ in range(no_of_submissions):
        publisher.publish_message(payload, headers={'tx_id': tx_id})

    logger.debug(" [x] Sent Payload to rabbitmq!")


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


@submit_bp.route('/submit', methods=['POST', 'GET'])
@flask_security.login_required
def submit():
    if request.method == 'POST':
        data = request.get_data().decode('UTF8')

        logger.debug(" [x] Encrypting data")

        unencrypted_json = json.loads(data)

        no_of_submissions = int(unencrypted_json['quantity'])

        with open("./keys.yml") as file:
            secrets_from_file = yaml.safe_load(file)

        key_store = KeyStore(secrets_from_file)

        tx_id = unencrypted_json['survey']['tx_id']

        for _ in range(0, no_of_submissions):
            # If submitting more than one then randomise the tx_id
            if tx_id is None:
                tx_id = str(uuid.uuid4())
                unencrypted_json['survey']['tx_id'] = tx_id
                logger.info("Auto setting tx_id", tx_id=tx_id)

            payload = encrypt(unencrypted_json['survey'], key_store, 'submission')
            send_payload(payload, tx_id, 1)  # let the loop handle the submission

        return data
    else:
        return render_template('submit.html', enable_empty_ftp=settings.ENABLE_EMPTY_FTP)


@submit_bp.route('/validate', methods=['POST', 'GET'])
def validate():
    if request.method == 'POST':
        payload = request.get_data()

        logger.debug("Validating json...")

        logger.debug("Validate URL: {}".format(settings.SDX_VALIDATE_URL))

        r = requests.post(settings.SDX_VALIDATE_URL, data=payload)

        return jsonify(json.loads(r.text))
    else:
        logger.info('Failed validation')
        return render_template('submit.html')


@submit_bp.route('/surveys')
def surveys():
    return json.dumps(list_surveys(), indent=4)
