import logging

import flask_security
import requests
from flask import Blueprint, render_template, request
from structlog import wrap_logger

from console import settings
from console.helpers.exceptions import ClientError, ServiceError
from console.views.home import send_data

logger = wrap_logger(logging.getLogger(__name__))

decrypt_bp = Blueprint('decrypt_bp', __name__, static_folder='static', template_folder='templates')


@decrypt_bp.route('/decrypt', strict_slashes=False, methods=['POST', 'GET'])
@flask_security.login_required
def decrypt():
    audited_logger = logger.bind(user=flask_security.core.current_user.email)
    if request.method == "POST":
        data = request.form.get('EncryptedData')
        url = settings.SDX_DECRYPT_URL
        decrypted_data = ""

        try:
            audited_logger.info("Posting data to sdx-decrypt")
            decrypt_response = send_data(logger=audited_logger, url=url,
                                         data=data, request_type="POST")
        except ClientError:
            error = 'Client error'
        except ServiceError:
            error = 'Service error'
        except requests.exceptions.ConnectionError:
            error = 'Connection error'
        else:
            decrypted_data = decrypt_response.text
            error = ""

        return render_template('decrypt.html',
                               decrypted_data=decrypted_data,
                               error=error,
                               current_user=flask_security.core.current_user)

    else:
        return render_template('decrypt.html', current_user=flask_security.core.current_user)
