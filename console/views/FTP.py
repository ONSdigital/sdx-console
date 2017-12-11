from datetime import datetime
import base64
import json
import logging.handlers

import flask_security
from flask import Blueprint
from flask import jsonify
from flask import render_template
from structlog import wrap_logger

import console.settings as settings
from console import app
from console.console_ftp import ConsoleFtp
from console.console_ftp import PATHS

logger = wrap_logger(logging.getLogger(__name__))

FTP_bp = Blueprint('FTP_bp', __name__, static_folder='static', template_folder='templates')


def get_ftp_contents():
    ftp_data = {}
    with ConsoleFtp() as ftp:
        ftp_data["pck"] = ftp.get_folder_contents(PATHS["pck"])[0:20]
        ftp_data["index"] = ftp.get_folder_contents(PATHS["index"])[0:20]
        ftp_data["image"] = ftp.get_folder_contents(PATHS["image"])[0:20]
        ftp_data["receipt"] = ftp.get_folder_contents(PATHS["receipt"])[0:20]
        ftp_data["json"] = ftp.get_folder_contents(PATHS["json"])[0:20]

    return ftp_data


def mod_to_iso(file_modified):
    t = datetime.strptime(file_modified, '%Y%m%d%H%M%S')
    return t.isoformat()


def get_file_contents(datatype, filename):
    with ConsoleFtp() as ftp:
        return ftp.get_file_contents(datatype, filename)


@FTP_bp.route('/FTP', methods=['POST', 'GET'])
@flask_security.login_required
def ftp_home():
    return render_template('FTP.html', enable_empty_ftp=settings.ENABLE_EMPTY_FTP)


@FTP_bp.route('/ftp.json')
def ftp_list():
    return jsonify(get_ftp_contents())


@FTP_bp.route('/view/<datatype>/<filename>')
def view_file(datatype, filename):
    if filename.lower().endswith(('jpg', 'png')):
        extension = filename.split(".")[-1]
        b64_image = base64.b64encode(get_file_contents(datatype, filename)).decode()
        return '<img style="width:100%;" src="data:image/' + extension + ';base64,' + b64_image + '" />'
    else:
        return '<pre>' + get_file_contents(datatype, filename).decode("utf-8") + '</pre>'


@FTP_bp.route('/clear')
def clear():
    removed = 0

    with ConsoleFtp() as ftp:

        if app.config['USE_MLSD']:
            for key, path in PATHS.items():
                for fname, _ in ftp._ftp.mlsd(path=path):
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
