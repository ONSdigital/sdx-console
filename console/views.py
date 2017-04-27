import logging
import os
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
    return r.status_code

@app.route('/decrypt', methods=['POST', 'GET'])
def decrypt():
    if request.method == "POST":
        logger.info("POSTing data to sdx-decrypt")

        data = request.get_data()
        url = settings.SDX_DECRYPT_URL

        decrypted_data = send_data(url, data)

        return decrypted_data

    else:
        return render_template('decrypt.html')
