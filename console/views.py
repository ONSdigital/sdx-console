import logging
import requests

from flask import render_template
from flask import request
from structlog import wrap_logger

from console import app
from console import settings
from console.helpers.exceptions import ClientError, ServiceError

logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
logger = wrap_logger(logging.getLogger(__name__))


def send_data(url, data):
    try:
        r = requests.post(url, data)
    except requests.exceptions.ConnectionError as e:
        logger.error('Could not connect to sdx-decrypt', response="connection error")
        raise e
        return

    if (r.status_code > 199 and r.status_code < 300):
        logger.info('Returned from ' + url, response="ok", status_code=r.status_code)
    elif (r.status_code > 399 and r.status_code < 500):
        logger.error('Could not decrypt message', response="client error", status_code=r.status_code)
        raise ClientError
    elif r.status_code > 499:
        logger.error('Could not decrypt message', response="service error", status_code=r.status_code)
        raise ServiceError

    return r


@app.route('/decrypt', methods=['POST', 'GET'])
def decrypt():
    if request.method == "POST":
        data = request.form['EncryptedData']
        url = settings.SDX_DECRYPT_URL
        decrypt_response = requests.Response()

        try:
            logger.info("Posting data to sdx-decrypt")
            decrypt_response = send_data(url, data)
        except ClientError:
            return render_template('decrypt.html', decrypted_data='Client error')
        except ServiceError:
            return render_template('decrypt.html', decrypted_data='Server error')
        except requests.exceptions.ConnectionError:
            return render_template('decrypt.html', decrypted_data='Could not connect to sdx-decrypt')

        decrypted_data = decrypt_response.text
        return render_template('decrypt.html', decrypted_data=decrypted_data)

    else:
        return render_template('decrypt.html')
