from flask import Flask, request, render_template
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
from ftplib import FTP

import os
import requests
import base64
import pika
import json

POSIE_URL = os.getenv('POSIE_URL')
FTP_HOST = os.getenv('FTP_HOST')
FTP_USER = os.getenv('FTP_USER')
FTP_PASS = os.getenv('FTP_PASS')

RABBIT_HOST = os.getenv('RABBIT_HOST')
RABBIT_PORT = os.getenv('RABBIT_PORT')

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


def get_ftp():
    ftp = FTP(FTP_HOST)
    ftp.login(user=FTP_USER, passwd=FTP_PASS)
    ftp.set_pasv(False)

    data = []

    for fname, fmeta in ftp.mlsd():
        if fname not in ('.', '..'):
            data.append(fname)

    return json.dumps(data)


@app.route('/', methods=['POST', 'GET'])
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
            host=RABBIT_HOST,
            port=int(RABBIT_PORT)
        ))

        channel = connection.channel()

        channel.queue_declare(queue='survey')

        channel.basic_publish(exchange='',
                              routing_key='survey',
                              body=payload)

        print(" [x] Sent Payload to rabbitmq!")

        connection.close()

        return unencrypted
    else:
        ftp_data = get_ftp()

        return render_template('index.html', ftp_data=ftp_data)


@app.route('/viewer')
def view():
    return get_ftp()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
