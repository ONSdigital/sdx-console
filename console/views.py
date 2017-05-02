import logging
import requests

from flask import render_template
from flask import request
from structlog import wrap_logger

from console import app
from console import settings

logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
logger = wrap_logger(logging.getLogger(__name__))


def send_data(url, data):
    r = requests.post(url, data)
    if r.status_code == 400:
        logger.error('Could not connect to ' + url, status_code=r.status_code)
        raise Exception('404 Error')
    else:
        logger.info('Returned from ' + url, status_code=r.status_code)
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
        except:
            errormsg = 'Could not connect to sdx-decrypt'
            return render_template('decrypt.html', decrypted_data=errormsg)
        decrypted_data = decrypt_response.text
        return render_template('decrypt.html', decrypted_data=decrypted_data)

    else:
        return render_template('decrypt.html')
