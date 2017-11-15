from datetime import datetime
import json
import logging.handlers
import os

import flask_security
from flask import Blueprint
from flask import jsonify
from flask import render_template
from flask import request
from structlog import wrap_logger

import console.settings as settings
from console import app
from console.console_ftp import ConsoleFtp, PATHS
from sdc.rabbit import QueuePublisher

logger = wrap_logger(logging.getLogger(__name__))

FTP_bp = Blueprint('FTP_bp', __name__, static_folder='static', template_folder='templates')


def get_ftp_contents():

    ftp_data = {}
    with ConsoleFtp() as ftp:
        ftp_data["pck"] = ftp.get_folder_contents(PATHS["pck"])[0:20]
        ftp_data["index"] = ftp.get_folder_contents(PATHS["index"])[0:20]
        ftp_data["image"] = ftp.get_folder_contents(PATHS["image"])[0:20]
        ftp_data["receipt"] = ftp.get_folder_contents(PATHS["receipt"])[0:20]

    return ftp_data


def list_surveys():
    return [f for f in os.listdir('console/static/surveys') if os.path.isfile(os.path.join('console/static/surveys', f))]


def send_payload(payload, tx_id, no_of_submissions=1):
    logger.debug(" [x] Sending encrypted Payload")

    publisher = QueuePublisher(settings.RABBIT_URLS, settings.RABBIT_QUEUE)
    for _ in range(no_of_submissions):
        publisher.publish_message(payload, headers={'tx_id': tx_id})

    logger.debug(" [x] Sent Payload to rabbitmq!")


def mod_to_iso(file_modified):
    t = datetime.strptime(file_modified, '%Y%m%d%H%M%S')
    return t.isoformat()


def get_image(filename):

    filepath, ext = os.path.splitext(filename)

    tmp_image_url = 'static/images/{}/{}'.format(filepath, ext)
    tmp_image_path = 'console/static/images/{}/{}'.format(filepath, ext)

    if os.path.exists(tmp_image_path):
        os.unlink(tmp_image_path)

    with ConsoleFtp() as ftp:
        ftp._ftp.retrbinary("RETR " + PATHS['image'] + filename, open(tmp_image_path, 'wb').write)

    return tmp_image_url


def get_file_contents(datatype, filename):

    with ConsoleFtp() as ftp:
        return ftp.get_file_contents(datatype, filename)


@FTP_bp.route('/FTP', methods=['POST', 'GET'])
@flask_security.login_required
def ftp_home():
    return render_template('FTP.html', enable_empty_ftp=settings.ENABLE_EMPTY_FTP)


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


@FTP_bp.route('/ftp.json')
def ftp_list():
    return jsonify(get_ftp_contents())


@FTP_bp.route('/clear')
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
