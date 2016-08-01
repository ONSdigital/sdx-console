from flask import Flask, request, render_template, jsonify

from ftplib import FTP
from datetime import datetime
from encrypter import Encrypter
from structlog import wrap_logger

import os
import pika
import json
import settings
import requests
import logging
import logging.handlers

from flask_paginate import Pagination

app = Flask(__name__)

PATHS = {
    'pck': "EDC_QData",
    'image': "EDC_QImages/Images",
    'index': "EDC_QImages/Index",
    'receipt': "EDC_QReceipts"
}

app.config['USE_MLSD'] = True

logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
logger = wrap_logger(logging.getLogger(__name__))


def login_to_ftp():
    ftp = FTP(settings.FTP_HOST)
    ftp.login(user=settings.FTP_USER, passwd=settings.FTP_PASS)

    try:
        # Perform a simple mlsd test
        len([fname for fname, fmeta in ftp.mlsd(path=PATHS['pck'])])
    except:
        app.config['USE_MLSD'] = False

    logger.debug("Setting mlsd:" + str(app.config['USE_MLSD']))

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
    logger.debug(" [x] Sending encrypted Payload")

    logger.debug(payload)

    connection = pika.BlockingConnection(pika.URLParameters(settings.RABBIT_URL))

    channel = connection.channel()

    channel.queue_declare(queue=settings.RABBIT_QUEUE, durable=True)

    for i in range(no_of_submissions):
        channel.basic_publish(exchange='',
                              routing_key=settings.RABBIT_QUEUE,
                              body=payload)

    logger.debug(" [x] Sent Payload to rabbitmq!")

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

    if app.config['USE_MLSD']:
        for fname, fmeta in ftp.mlsd(path=path):
            if fname not in ('.', '..'):
                fmeta['modify'] = mod_to_iso(fmeta['modify'])
                fmeta['filename'] = fname
                data.append(fmeta)
    else:
        for fname in ftp.nlst(path):
            fmeta = {}
            if fname not in ('.', '..'):
                fmeta['filename'] = fname

                data.append(fmeta)

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

        logger.debug("Rabbit URL: {}".format(settings.RABBIT_URL))

        data = request.get_data().decode('UTF8')

        logger.debug(" [x] Encrypting data: {}".format(data))

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


def client_error(error=None):
    logger.error(error, request=request.data.decode('UTF8'))
    message = {
        'status': 400,
        'message': error,
        'uri': request.url
    }
    resp = jsonify(message)
    resp.status_code = 400

    return resp


def get_paginate_info(ru_ref):
    # This is a little hacky as pagination.start or
    # pagination.end does not work in the view.
    info = "Found <b>{total}</b>,"
    if ru_ref:
        info += " matching ru_ref: <b>{0}</b>,".format(ru_ref)
    info += " displaying <b>{start} - {end}</b>"
    return info


@app.route('/store', methods=['POST', 'GET'])
def store():
    if request.method == 'POST':
        mongo_id = request.get_data().decode('UTF8')
        result = requests.post(settings.STORE_ENDPOINT + 'queue', json={"id": mongo_id})
        return mongo_id if result.status_code is 200 else result

    else:
        params = {}
        params['page'] = request.args.get('page', type=int, default=1)
        params['per_page'] = request.args.get('per_page', type=int, default=25)
        params['ru_ref'] = request.args.get('ru_ref', type=str, default="")

        result = requests.get(settings.STORE_ENDPOINT + 'responses', params)
        content = result.content.decode('UTF8')
        data = json.loads(content)
        count = data['total_hits']

        display = get_paginate_info(params['ru_ref'])
        pagination = Pagination(page=params['page'], total=count, record_name='submissions',
                                css_framework='bootstrap3', per_page=params['per_page'],
                                display_msg=display)
        return render_template('store.html', data=data, ru_ref=params['ru_ref'], pagination=pagination)


@app.route('/decrypt', methods=['POST', 'GET'])
def decrypt():
    if request.method == 'POST':

        logger.debug("Rabbit URL: {}".format(settings.RABBIT_URL))

        payload = request.get_data().decode('UTF8')

        send_payload(payload)

        return payload
    else:

        ftp_data = get_ftp_contents()

        return render_template('decrypt.html', ftp_data=json.dumps(ftp_data))


@app.route('/validate', methods=['POST', 'GET'])
def validate():
    if request.method == 'POST':

        payload = request.get_data()

        logger.debug("Validating json...{}".format(payload))

        logger.debug("Validate URL: {}".format(settings.VALIDATE_ENDPOINT))

        r = requests.post(settings.VALIDATE_ENDPOINT, data=payload)

        return jsonify(json.loads(r.text))
    else:

        ftp_data = get_ftp_contents()

        return render_template('decrypt.html', ftp_data=json.dumps(ftp_data))


@app.route('/list')
def list():

    ftp_data = get_ftp_contents()

    return jsonify(ftp_data)


@app.route('/view/<datatype>/<filename>')
def view_file(datatype, filename):
    if filename.lower().endswith(('jpg', 'png')):
        return '<img style="width:100%;" src="/' + get_image(filename) + '" />'
    else:
        return '<pre>' + get_file_contents(datatype, filename) + '</pre>'


@app.route('/clear')
def clear():
    removed = 0

    if app.config['USE_MLSD']:
        for key, path in PATHS.items():
            for fname, fmeta in ftp.mlsd(path=path):
                if fname not in ('.', '..'):
                    ftp.delete(path + "/" + fname)
                    removed += 1
    else:
        for key, path in PATHS.items():
            for fname, fmeta in ftp.nlst(path):
                if fname not in ('.', '..'):
                    ftp.delete(path + "/" + fname)
                    removed += 1

    return json.dumps({"removed": removed})

if __name__ == '__main__':
    ftp = login_to_ftp()
    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
