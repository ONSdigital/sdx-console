from datetime import datetime
import json
import logging.handlers
import os
import uuid

import requests
from flask import Blueprint
from flask import jsonify
from flask import render_template
from flask import request
from structlog import wrap_logger

import console.settings as settings
from console import app
from console.console_ftp import ConsoleFtp, PATHS
from console.encrypter import Encrypter
from console.queue_publisher import QueuePublisher

logger = wrap_logger(logging.getLogger(__name__))

submit_bp = Blueprint('submit_bp', __name__, static_folder='static', template_folder='templates')


def get_ftp_contents():

    ftp_data = {}
    with ConsoleFtp() as ftp:
        ftp_data["pck"] = ftp.get_folder_contents(PATHS["pck"])[0:10]
        ftp_data["index"] = ftp.get_folder_contents(PATHS["index"])[0:10]
        ftp_data["image"] = ftp.get_folder_contents(PATHS["image"])[0:10]
        ftp_data["receipt"] = ftp.get_folder_contents(PATHS["receipt"])[0:10]

    return ftp_data


def list_surveys():
    return [f for f in os.listdir('console/static/surveys') if os.path.isfile(os.path.join('console/static/surveys', f))]


def send_payload(payload, tx_id, no_of_submissions=1):
    logger.debug(" [x] Sending encrypted Payload")

    publisher = QueuePublisher(logger, settings.RABBIT_URLS, settings.RABBIT_QUEUE)
    for i in range(no_of_submissions):
        publisher.publish_message(payload, tx_id)

    logger.debug(" [x] Sent Payload to rabbitmq!")


def mod_to_iso(file_modified):
    t = datetime.strptime(file_modified, '%Y%m%d%H%M%S')
    return t.isoformat()


def get_image(filename):

    filepath, ext = os.path.splitext(filename)

    tmp_image_url = 'static/images/' + filepath + ext
    tmp_image_path = 'console/static/images/' + filepath + ext

    if os.path.exists(tmp_image_path):
        os.unlink(tmp_image_path)

    with ConsoleFtp() as ftp:
        ftp._ftp.retrbinary("RETR " + PATHS['image'] + "/" + filename, open(tmp_image_path, 'wb').write)

    return tmp_image_url


def get_file_contents(datatype, filename):

    with ConsoleFtp() as ftp:
        return ftp.get_file_contents(datatype, filename)


@submit_bp.route('/submit', methods=['POST', 'GET'])
def submit():

    if request.method == 'POST':

        data = request.get_data().decode('UTF8')

        logger.debug(" [x] Encrypting data")

        unencrypted_json = json.loads(data)

        no_of_submissions = int(unencrypted_json['quantity'])

        encrypter = Encrypter()

        for i in range(0, no_of_submissions):
            # If submitting more than one then randomise the tx_id
            if no_of_submissions > 1:
                tx_id = str(uuid.uuid4())
                unencrypted_json['survey']['tx_id'] = tx_id
                logger.info("Auto setting tx_id", tx_id=tx_id)
            else:
                tx_id = unencrypted_json['survey']['tx_id']

            payload = encrypter.encrypt(unencrypted_json['survey'])
            send_payload(payload, tx_id, 1)  # let the loop handle the submission

        return data
    else:

        return render_template('submit.html',
                               enable_empty_ftp=settings.ENABLE_EMPTY_FTP)


def client_error(error=None):
    logger.error(error)
    message = {
        'status': 400,
        'message': error,
        'uri': request.url
    }
    resp = jsonify(message)
    resp.status_code = 400

    return resp


def get_paginate_info(ru_ref):
    # This is a little hacky as pagination.start or
    # pagination.end does not work in the view.
    info = "Found <b>{total}</b>,"
    if ru_ref:
        info += " matching ru_ref: <b>{0}</b>,".format(ru_ref)
    info += " displaying <b>{start} - {end}</b>"
    return info


@app.route('/validate', methods=['POST', 'GET'])
def validate():
    if request.method == 'POST':

        payload = request.get_data()

        logger.debug("Validating json...")

        logger.debug("Validate URL: {}".format(settings.SDX_VALIDATE_URL))

        r = requests.post(settings.SDX_VALIDATE_URL, data=payload)

        return jsonify(json.loads(r.text))
    else:

        ftp_data = get_ftp_contents()

        return render_template('decrypt.html', ftp_data=json.dumps(ftp_data))


@app.route('/ftp.json')
def ftp_list():
    return jsonify(get_ftp_contents())


@app.route('/view/<datatype>/<filename>')
def view_file(datatype, filename):
    if filename.lower().endswith(('jpg', 'png')):
        return '<img style="width:100%;" src="/' + get_image(filename) + '" />'
    else:
        return '<pre>' + get_file_contents(datatype, filename) + '</pre>'


@app.route('/clear')
def clear():
    removed = 0

    with ConsoleFtp() as ftp:

        if app.config['USE_MLSD']:
            for key, path in PATHS.items():
                for fname, fmeta in ftp._ftp.mlsd(path=path):
                    if fname not in ('.', '..'):
                        ftp._ftp.delete(path + "/" + fname)
                        removed += 1
        else:
            for key, path in PATHS.items():
                for fname, fmeta in ftp._ftp.nlst(path):
                    if fname not in ('.', '..'):
                        ftp._ftp.delete(path + "/" + fname)
                        removed += 1

        return json.dumps({"removed": removed})


@app.route('/surveys')
def surveys():
    return json.dumps(list_surveys(), indent=4)
