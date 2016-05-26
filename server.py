from flask import Flask, request, render_template

from ftplib import FTP
from datetime import datetime
from encrypter import Encrypter

import os
import pika
import json
import settings

app = Flask(__name__)

PATHS = {
    'pck': "EDC_QData",
    'image': "EDC_QImages/Images",
    'index': "EDC_QImages/Index",
    'receipt': "EDC_QReceipts"
}


def login_to_ftp():
    ftp = FTP(settings.FTP_HOST)
    ftp.login(user=settings.FTP_USER, passwd=settings.FTP_PASS)

    return ftp


def list_surveys():
    return [f for f in os.listdir('static/surveys') if os.path.isfile(os.path.join('static/surveys', f))]


@app.route('/surveys')
def surveys():
    return json.dumps(list_surveys(), indent=4)


@app.route('/surveys/<survey_id>')
def survey(survey_id):
    with open("static/surveys/%s" % survey_id) as json_file:
        file_content = json_file.read()
        json_file.close()
        return file_content


def send_payload(payload, no_of_submissions=1):
    app.logger.debug(" [x] Sending encrypted Payload")

    app.logger.debug(payload)

    connection = pika.BlockingConnection(pika.URLParameters(settings.RABBIT_URL))

    channel = connection.channel()

    channel.queue_declare(queue=settings.RABBIT_QUEUE)

    for i in range(no_of_submissions):
        channel.basic_publish(exchange='',
                              routing_key=settings.RABBIT_QUEUE,
                              body=payload)

    app.logger.debug(" [x] Sent Payload to rabbitmq!")

    connection.close()


def mod_to_iso(file_modified):
    t = datetime.strptime(file_modified, '%Y%m%d%H%M%S')
    return t.isoformat()


def get_image(filename):

    filepath, ext = os.path.splitext(filename)

    tmp_image_path = 'static/images/' + filepath + ext

    if os.path.exists(tmp_image_path):
        os.unlink(tmp_image_path)

    ftp.retrbinary("RETR " + PATHS['image'] + "/" + filename, open(tmp_image_path, 'wb').write)

    return tmp_image_path


def get_file_contents(datatype, filename):
    ftp.retrbinary("RETR " + PATHS[datatype] + "/" + filename, open('tmpfile', 'wb').write)

    transferred = open('tmpfile', 'r')

    return transferred.read()


def get_folder_contents(path):
    data = []

    # for fname, fmeta in ftp.mlsd(path=path):
    #     if fname not in ('.', '..'):
    #         fmeta['modify'] = mod_to_iso(fmeta['modify'])
    #         fmeta['filename'] = fname

    #         data.append(fmeta)

    return data


def get_ftp_contents():

        ftp_data = {}
        ftp_data['pck'] = get_folder_contents(PATHS['pck'])
        ftp_data['index'] = get_folder_contents(PATHS['index'])
        ftp_data['image'] = get_folder_contents(PATHS['image'])
        ftp_data['receipt'] = get_folder_contents(PATHS['receipt'])

        return ftp_data


@app.route('/', methods=['POST', 'GET'])
def submit():
    if request.method == 'POST':

        app.logger.debug("Rabbit URL: {}".format(settings.RABBIT_URL))

        data = request.get_data().decode('UTF8')

        app.logger.debug(" [x] Encrypting data: {}".format(data))

        unencrypted_json = json.loads(data)

        no_of_submissions = int(unencrypted_json['quantity'])

        encrypter = Encrypter()
        payload = encrypter.encrypt(unencrypted_json['survey'])

        send_payload(payload, no_of_submissions)

        return data
    else:

        ftp_data = get_ftp_contents()
        surveys = list_surveys()

        return render_template('index.html', ftp_data=json.dumps(ftp_data),
                               surveys=surveys)


@app.route('/decrypt', methods=['POST', 'GET'])
def decrypt():
    if request.method == 'POST':

        app.logger.debug("Rabbit URL: {}".format(settings.RABBIT_URL))

        payload = request.get_data().decode('UTF8')

        send_payload(payload)

        return payload
    else:

        ftp_data = get_ftp_contents()

        return render_template('decrypt.html', ftp_data=json.dumps(ftp_data))


@app.route('/list')
def list():

    ftp_data = get_ftp_contents()

    return json.dumps(ftp_data)


@app.route('/view/<datatype>/<filename>')
def view_file(datatype, filename):
    if filename.lower().endswith(('jpg', 'png')):
        return '<img style="width:100%;" src="/' + get_image(filename) + '" />'
    else:
        return '<pre>' + get_file_contents(datatype, filename) + '</pre>'


@app.route('/clear')
def clear():
    removed = 0

    for key, path in PATHS.items():
        for fname, fmeta in ftp.mlsd(path=path):
            if fname not in ('.', '..'):
                ftp.delete(path + "/" + fname)
                removed += 1

    return json.dumps({"removed": removed})

if __name__ == '__main__':
    ftp = login_to_ftp()
    app.run(debug=True, host='0.0.0.0')
