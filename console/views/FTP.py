import base64
import logging.handlers

import flask_security
from flask import Blueprint, render_template
from structlog import wrap_logger

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
    return render_template('FTP.html', contents=contents)


@FTP_bp.route('/FTP/<datatype>', methods=['POST', 'GET'])
@flask_security.login_required
def ftp_pcks(datatype):
    if datatype not in ['pck', 'image', 'index', 'receipt', 'json']:
        return render_template('FTP.html')

    with ConsoleFtp() as ftp:
        contents = ftp.get_folder_contents(PATHS[datatype])[0:20]
    return render_template('FTP.html', contents=contents)


@FTP_bp.route('/view/<datatype>/<filename>')
@flask_security.login_required
def view_file(datatype, filename):
    if filename.lower().endswith(('jpg', 'png')):
        extension = filename.split(".")[-1]
        b64_image = base64.b64encode(get_file_contents(datatype, filename)).decode()
        return '<img style="width:100%;" src="data:image/' + extension + ';base64,' + b64_image + '" />'
    else:
        return '<pre>' + get_file_contents(datatype, filename).decode("utf-8") + '</pre>'
