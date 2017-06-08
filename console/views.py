from flask import request, render_template, jsonify

from console import app

import operator
from ftplib import FTP
from datetime import datetime
from console.encrypter import Encrypter
from console.queue_publisher import QueuePublisher
import console.settings as settings
from structlog import wrap_logger

import os
import json
import requests
import logging
import logging.handlers
import uuid

from flask_paginate import Pagination

from sdx.common.logger_config import logger_initial_config


PATHS = {
    "pck": settings.SDX_FTP_DATA_PATH,
    "image": settings.SDX_FTP_IMAGE_PATH + "/Images",
    "index": settings.SDX_FTP_IMAGE_PATH + "/Index",
    "receipt": settings.SDX_FTP_RECEIPT_PATH
}

logger_initial_config(service_name='sdx-console')

logger = wrap_logger(logging.getLogger(__name__))


class ConsoleFtp(object):

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._ftp.quit()

    def __init__(self):
        self._ftp = FTP(settings.FTP_HOST)
        self._ftp.login(user=settings.FTP_USER, passwd=settings.FTP_PASS)
        self._mlsd_enabled = True
        try:
            # Perform a simple mlsd test to see if the ftp server has the extra functionality:
            len([fname for fname, fmeta in self._ftp.mlsd(path=PATHS['pck'])])
        except Exception as e:
            logger.error("Exception initialising consoleftp", exception=e)
            app.config['USE_MLSD'] = False
            self._mlsd_enabled = False

    def get_folder_contents(self, path):

        file_list = []

        if self._mlsd_enabled:
            for fname, fmeta in self._ftp.mlsd(path=path):
                if fname not in ('.', '..', '.DS_Store'):
                    meta = {
                        'name': fname,
                        'modify': datetime.strptime(fmeta['modify'], '%Y%m%d%H%M%S').isoformat(),
                        'size': fmeta['size']
                    }
                    file_list.append(meta)

        else:
            pre = []
            self._ftp.dir("{}".format(path), pre.append)
            for unparsed_line in pre:
                bits = unparsed_line.split()
                date_string = ' '.join([bits[0], bits[1]])
                fname = ' '.join(bits[3:])
                # the isdigit() checks this is a file and a directory
                if fname not in ('.', '..', '.DS_Store') and bits[2].isdigit():
                    meta = {
                        'name': fname,
                        'modify': datetime.strptime(date_string, '%m-%d-%y %I:%M%p').isoformat(),
                        'size': int(bits[2])
                    }
                    file_list.append(meta)

        file_list.sort(key=operator.itemgetter('modify'), reverse=True)
        return file_list

    def get_file_contents(self, datatype, filename):
        self._ftp.retrbinary("RETR " + PATHS[datatype] + "/" + filename, open('tmpfile', 'wb').write)
        transferred = open('tmpfile', 'r')
        return transferred.read()


def get_ftp_contents():

    ftp_data = {}
    with ConsoleFtp() as ftp:
        ftp_data["pck"] = ftp.get_folder_contents(PATHS["pck"])[0:10]
        ftp_data["index"] = ftp.get_folder_contents(PATHS["index"])[0:10]
        ftp_data["image"] = ftp.get_folder_contents(PATHS["image"])[0:10]
        ftp_data["receipt"] = ftp.get_folder_contents(PATHS["receipt"])[0:10]

    return ftp_data


def list_surveys():
    return [f for f in os.listdir('console/static/surveys') if os.path.isfile(os.path.join('console/static/surveys', f))]


@app.route('/surveys')
def surveys():
    return json.dumps(list_surveys(), indent=4)


@app.route('/surveys/<survey_id>')
def survey(survey_id):
    with open("console/static/surveys/%s" % survey_id) as json_file:
        file_content = json_file.read()
        json_file.close()
        return file_content


def send_payload(payload, tx_id, no_of_submissions=1):
    logger.debug(" [x] Sending encrypted Payload")

    publisher = QueuePublisher(logger, settings.RABBIT_URLS, settings.RABBIT_QUEUE)
    for i in range(no_of_submissions):
        publisher.publish_message(payload, tx_id)

    logger.debug(" [x] Sent Payload to rabbitmq!")


def mod_to_iso(file_modified):
    t = datetime.strptime(file_modified, '%Y%m%d%H%M%S')
    return t.isoformat()


def get_image(filename):

    filepath, ext = os.path.splitext(filename)

    tmp_image_url = 'static/images/' + filepath + ext
    tmp_image_path = 'console/static/images/' + filepath + ext

    if os.path.exists(tmp_image_path):
        os.unlink(tmp_image_path)

    with ConsoleFtp() as ftp:
        ftp._ftp.retrbinary("RETR " + PATHS['image'] + "/" + filename, open(tmp_image_path, 'wb').write)

    return tmp_image_url


def get_file_contents(datatype, filename):

    with ConsoleFtp() as ftp:
        return ftp.get_file_contents(datatype, filename)


@app.route('/', methods=['POST', 'GET'])
def submit():

    if request.method == 'POST':

        data = request.get_data().decode('UTF8')

        logger.debug(" [x] Encrypting data")

        unencrypted_json = json.loads(data)

        no_of_submissions = int(unencrypted_json['quantity'])

        encrypter = Encrypter()

        for i in range(0, no_of_submissions):
            # If submitting more than one then randomise the tx_id
            if no_of_submissions > 1:
                tx_id = str(uuid.uuid4())
                unencrypted_json['survey']['tx_id'] = tx_id
                logger.info("Auto setting tx_id", tx_id=tx_id)
            else:
                tx_id = unencrypted_json['survey']['tx_id']

            payload = encrypter.encrypt(unencrypted_json['survey'])
            send_payload(payload, tx_id, 1)  # let the loop handle the submission

        return data
    else:

        return render_template('index.html',
                               enable_empty_ftp=settings.ENABLE_EMPTY_FTP)


def client_error(error=None):
    logger.error(error)
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
def store(invalid=False):
    if request.method == 'POST':
        mongo_id = request.get_data().decode('UTF8')
        result = requests.post(settings.SDX_STORE_URL + 'queue', json={"id": mongo_id})
        return mongo_id if result.status_code is 200 else result

    else:
        return fetch_responses_from_store(invalid=False)


@app.route('/store/invalid', methods=['GET'])
def store_invalid():
    return fetch_responses_from_store(invalid=True)


def fetch_responses_from_store(invalid=False):
    params = {}
    params['page'] = request.args.get('page', type=int, default=1)
    params['per_page'] = request.args.get('per_page', type=int, default=25)
    params['ru_ref'] = request.args.get('ru_ref', type=str, default="")

    request_url = '{}{}'.format(settings.SDX_STORE_URL, 'responses')
    if invalid:
        invalid = True
        request_url = '{}{}'.format(settings.SDX_STORE_URL, 'invalid-responses')
    result = requests.get(request_url, params)
    content = result.content.decode('UTF8')
    data = json.loads(content)
    count = data['total_hits']

    display = get_paginate_info(params['ru_ref'])
    pagination = Pagination(page=params['page'], total=count, record_name='submissions',
                            css_framework='bootstrap3', per_page=params['per_page'],
                            display_msg=display)
    return render_template('store.html', data=data,
                           ru_ref=params['ru_ref'], pagination=pagination, invalid=invalid)


@app.route('/decrypt', methods=['POST', 'GET'])
def decrypt():
    if request.method == 'POST':

        payload = request.get_data().decode('UTF8')

        send_payload(payload, tx_id=None)

        return payload
    else:

        ftp_data = get_ftp_contents()

        return render_template('decrypt.html', ftp_data=json.dumps(ftp_data))


@app.route('/validate', methods=['POST', 'GET'])
def validate():
    if request.method == 'POST':

        payload = request.get_data()

        logger.debug("Validating json...")

        logger.debug("Validate URL: {}".format(settings.SDX_VALIDATE_URL))

        r = requests.post(settings.SDX_VALIDATE_URL, data=payload)

        return jsonify(json.loads(r.text))
    else:

        ftp_data = get_ftp_contents()

        return render_template('decrypt.html', ftp_data=json.dumps(ftp_data))


@app.route('/ftp.json')
def ftp_list():
    return jsonify(get_ftp_contents())


@app.route('/view/<datatype>/<filename>')
def view_file(datatype, filename):
    if filename.lower().endswith(('jpg', 'png')):
        return '<img style="width:100%;" src="/' + get_image(filename) + '" />'
    else:
        return '<pre>' + get_file_contents(datatype, filename) + '</pre>'


@app.route('/clear')
def clear():
    removed = 0

    with ConsoleFtp() as ftp:

        if app.config['USE_MLSD']:
            for key, path in PATHS.items():
                for fname, fmeta in ftp._ftp.mlsd(path=path):
                    if fname not in ('.', '..'):
                        ftp._ftp.delete(path + "/" + fname)
                        removed += 1
        else:
            for key, path in PATHS.items():
                for fname, fmeta in ftp._ftp.nlst(path):
                    if fname not in ('.', '..'):
                        ftp._ftp.delete(path + "/" + fname)
                        removed += 1

        return json.dumps({"removed": removed})
