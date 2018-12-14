import logging.handlers
import time
import uuid
import yaml
import base64
import os

import flask_security
from flask import Blueprint, render_template, request
from structlog import wrap_logger
from sdc.rabbit import QueuePublisher
from sdc.rabbit.exceptions import PublishMessageError
from sdc.crypto.encrypter import encrypt
from sdc.crypto.key_store import KeyStore

import console.settings as settings

logger = wrap_logger(logging.getLogger(__name__))

SEFT_bp = Blueprint('SEFT_bp', __name__, static_folder='static', template_folder='templates')


def send_payload(payload, tx_id):
    logger.info("About to send SEFT payload", tx_id=tx_id)

    publisher = QueuePublisher(settings.RABBIT_URLS, settings.SEFT_CONSUMER_RABBIT_QUEUE)
    try:
        publisher.publish_message(payload, headers={'tx_id': tx_id})
    except PublishMessageError:
        logger.exception("Failed to put SEFT payload on queue", tx_id=tx_id)

    logger.info("SEFT payload successfully placed onto rabbit queue", tx_id=tx_id)


def convert_file_object_to_string_base64(file):
    """
    Convert a file object to a string
    :param file: The file to convert
    :return: String
    """
    return base64.b64encode(file).decode()


@SEFT_bp.route('/SEFT', methods=['GET', 'POST'])
@flask_security.login_required
def get_seft():
    messages = []
    if request.method == 'POST':
        seft_file = request.files['file']
        if seft_file.filename == '':
            messages.append('No selected file')
            logger.info("No selected file")
        _, file_extension = os.path.splitext(seft_file.filename)
        if file_extension not in ['.xls', '.xlsx']:
            messages.append('Incorrect file extension')
            logger.info("Incorrect file extension")

        if messages:
            return render_template('SEFT.html', messages=messages)

        tx_id = str(uuid.uuid4())
        case_id = str(uuid.uuid4())
        ru_ref = "12345678901A"
        # The submission will be put into a folder of the same name in the FTP server
        survey_ref = "survey_ref"

        _, file_extension = os.path.splitext(seft_file.filename)
        file_as_string = convert_file_object_to_string_base64(seft_file.stream.read())

        time_date_stamp = time.strftime("%Y%m%d%H%M%S")
        file_name = "{ru_ref}_{exercise_ref}_" \
                    "{survey_ref}_{time_date_stamp}{file_format}".format(ru_ref=ru_ref,
                                                                         exercise_ref="exercise_ref",
                                                                         survey_ref=survey_ref,
                                                                         time_date_stamp=time_date_stamp,
                                                                         file_format=file_extension)

        logger.info("Generated filename for file going to FTP", file_name=file_name, case_id=case_id, tx_id=tx_id)
        message_json = {
            'filename': file_name,
            'file': file_as_string,
            'case_id': case_id,
            'survey_id': survey_ref
        }

        with open("./seft-keys.yml") as file:
            secrets_from_file = yaml.safe_load(file)

        key_store = KeyStore(secrets_from_file)
        payload = encrypt(message_json, key_store, 'inbound')

        send_payload(payload, tx_id)
        messages.append('File queued successfully')

    return render_template('SEFT.html', messages=messages)
