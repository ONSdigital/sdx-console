from flask import Flask, request, render_template
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
from ftplib import FTP
from datetime import datetime

import os
import requests
import base64
import pika
import json

POSIE_URL = os.getenv('POSIE_URL', 'http://posie:5000')

FTP_HOST = os.getenv('FTP_HOST', 'pure-ftpd')
FTP_USER = os.getenv('FTP_USER')
FTP_PASS = os.getenv('FTP_PASS')

RABBIT_HOST = os.getenv('RABBIT_HOST', 'rabbit')
RABBIT_PORT = os.getenv('RABBIT_PORT', 5672)

RABBIT_USER = os.getenv('RABBIT_USER', 'rabbit')
RABBIT_PASS = os.getenv('RABBIT_PASS', 'rabbit')
RABBIT_QUEUE = os.getenv('RABBIT_QUEUE', 'survey')

key_url = "{}/key".format(POSIE_URL)
import_url = "{}/decrypt".format(POSIE_URL)
public_key = None

app = Flask(__name__)


def login_to_ftp():
    ftp = FTP(FTP_HOST)
    ftp.login(user=FTP_USER, passwd=FTP_PASS)
    ftp.set_pasv(False)

    return ftp


def mod_to_iso(file_modified):
    t = datetime.strptime(file_modified, '%Y%m%d%H%M%S')
    return t.isoformat()


def get_key():
    global public_key

    r = requests.get(key_url)

    key_string = base64.b64decode(r.text)

    public_key = serialization.load_der_public_key(
        key_string,
        backend=default_backend()
    )


def get_image(filename):
    ftp = login_to_ftp()

    filepath, ext = os.path.splitext(filename)

    tmp_image_path = 'static/images/' + filepath + ext

    if os.path.exists(tmp_image_path):
        os.unlink(tmp_image_path)

    ftp.retrbinary("RETR " + filename, open(tmp_image_path, 'wb').write)

    return tmp_image_path


def get_file_contents(filename):
    ftp = login_to_ftp()

    ftp.retrbinary("RETR " + filename, open('tmpfile', 'wb').write)

    transferred = open('tmpfile', 'r')

    return transferred.read()


def get_ftp():
    ftp = FTP(FTP_HOST)
    ftp.login(user=FTP_USER, passwd=FTP_PASS)
    ftp.set_pasv(False)

    data = []

    for fname, fmeta in ftp.mlsd():
        if fname not in ('.', '..'):
            fmeta['modify'] = mod_to_iso(fmeta['modify'])
            fmeta['filename'] = fname

            data.append(fmeta)

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

        credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)

        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=RABBIT_HOST,
            port=int(RABBIT_PORT),
            credentials=credentials
        ))

        channel = connection.channel()

        channel.queue_declare(queue=RABBIT_QUEUE)

        channel.basic_publish(exchange='',
                              routing_key=RABBIT_QUEUE,
                              body=payload)

        print(" [x] Sent Payload to rabbitmq!")

        connection.close()

        return unencrypted
    else:
        if not public_key:
            get_key()

        ftp_data = get_ftp()

        return render_template('index.html', ftp_data=ftp_data)


@app.route('/list')
def list():
    return get_ftp()


@app.route('/view/<filename>')
def view_file(filename):
    if filename.endswith(('jpg', 'png')):
        return '<img style="width:100%;" src="/' + get_image(filename) + '" />'
    else:
        return '<pre>' + get_file_contents(filename) + '</pre>'


@app.route('/clear')
def clear():
    ftp = login_to_ftp()

    removed = 0

    for fname in ftp.nlst():
        ftp.delete(fname)
        removed += 1

    return json.dumps({"removed": removed})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
