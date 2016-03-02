from flask import Flask, request, render_template
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
from ftplib import FTP

import os
import requests
import base64
import pika

POSIE_URL = os.getenv('POSIE_URL', 'http://posie:5000')
FTP_USER = os.getenv('FTP_USER', '')
FTP_PASSWORD = os.getenv('FTP_PASSWORD', '')

key_url = "{}/key".format(POSIE_URL)
import_url = "{}/decrypt".format(POSIE_URL)
public_key = ""

app = Flask(__name__)

r = requests.get(key_url)

key_string = base64.b64decode(r.text)

public_key = serialization.load_der_public_key(
    key_string,
    backend=default_backend()
)


@app.route('/submitter', methods=['POST', 'GET'])
def submit():
    if request.method == 'POST':
        unencrypted = request.get_data()

        print(" [x] Encrypting data: {}".format(unencrypted))

        ciphertext = public_key.encrypt(
            unencrypted,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None
            )
        )

        payload = base64.b64encode(ciphertext)

        print(" [x] Encrypted Payload")

        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='rabbit'
        ))

        channel = connection.channel()

        channel.queue_declare(queue='survey')

        channel.basic_publish(exchange='',
                              routing_key='survey',
                              body=payload)

        print(" [x] Sent Payload to rabbitmq!")

        connection.close()

        return ''
    else:
        return render_template('index.html')


@app.route('/viewer')
def view():
    ftp = FTP('pure-ftpd')
    ftp.login(user=FTP_USER, passwd=FTP_PASSWORD)

    return ftp.dir()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
