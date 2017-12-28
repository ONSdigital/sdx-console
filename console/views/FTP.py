import base64
import json
import logging.handlers

import flask_security
from flask import Blueprint, render_template
from structlog import wrap_logger

import console.settings as settings
from console import app
from console.console_ftp import ConsoleFtp, PATHS

logger = wrap_logger(logging.getLogger(__name__))

FTP_bp = Blueprint('FTP_bp', __name__, static_folder='static', template_folder='templates')


def get_file_contents(datatype, filename):
    with ConsoleFtp() as ftp:
        return ftp.get_file_contents(datatype, filename)


@FTP_bp.route('/FTP', methods=['POST', 'GET'])
@flask_security.login_required
def ftp_home():
    with ConsoleFtp() as ftp:
        contents = ftp.get_folder_contents(PATHS["pck"])[0:20]
    return render_template('FTP.html', enable_empty_ftp=settings.ENABLE_EMPTY_FTP, contents=contents)


@FTP_bp.route('/FTP/<datatype>', methods=['POST', 'GET'])
@flask_security.login_required
def ftp_pcks(datatype):
    if datatype not in ['pck', 'image', 'index', 'receipt', 'json']:
        return render_template('FTP.html', enable_empty_ftp=settings.ENABLE_EMPTY_FTP)

    with ConsoleFtp() as ftp:
        contents = ftp.get_folder_contents(PATHS[datatype])[0:20]
    return render_template('FTP.html', enable_empty_ftp=settings.ENABLE_EMPTY_FTP, contents=contents)


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
