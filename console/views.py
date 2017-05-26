import logging
import requests
import json

from flask import render_template
from flask import request
import flask_security
from sqlalchemy.dialects.postgresql import JSONB, UUID
from structlog import wrap_logger

from console.authentication import db
from console import app
from console import settings
from console.helpers.exceptions import ClientError, ServiceError

logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
logger = wrap_logger(logging.getLogger(__name__))


@app.route('/', methods=['GET'])
@flask_security.login_required
def home():
    return "stuff"


def send_data(url, data=None, request_type="POST"):
    try:
        if request_type == "POST":
            logger.info("POSTING DATA")
            r = requests.post(url, data)
        else:
            r = requests.get(url)
    except requests.exceptions.ConnectionError as e:
        logger.error('Could not connect to ' + url, response="Connection error")
        raise e

    if 199 < r.status_code < 300:
        logger.info('Returned from ' + url, response=r.reason, status_code=r.status_code)
    elif 399 < r.status_code < 500:
        logger.error('Returned from ' + url, response=r.reason, status_code=r.status_code)
        raise ClientError
    elif r.status_code > 499:
        logger.error('Returned from ' + url, response=r.reason, status_code=r.status_code)
        raise ServiceError

    return r


@app.route('/decrypt', methods=['POST', 'GET'])
@flask_security.roles_required('SDX-Developer')
def decrypt():
    logger.bind(user=flask_security.core.current_user.email)
    if request.method == "POST":
        data = request.form['EncryptedData']
        url = settings.SDX_DECRYPT_URL
        decrypted_data = ""

        try:
            logger.info("Posting data to sdx-decrypt", user=flask_security.core.current_user.email)
            decrypt_response = send_data(url, data, "POST")
        except ClientError:
            error = 'Client error'
        except ServiceError:
            error = 'Service error'
        except requests.exceptions.ConnectionError:
            error = 'Connection error'
        else:
            decrypted_data = decrypt_response.text
            error = ""

        return render_template('decrypt.html', decrypted_data=decrypted_data, error=error)

    else:
        return render_template('decrypt.html')


class SurveyResponse(db.Model):
    __tablename__ = 'responses'
    tx_id = db.Column("tx_id",
                      UUID,
                      primary_key=True)

    ts = db.Column("ts",
                   db.TIMESTAMP(timezone=True),
                   server_default=db.func.now(),
                   onupdate=db.func.now())

    invalid = db.Column("invalid",
                        db.Boolean,
                        default=False)

    data = db.Column("data", JSONB)

    def __init__(self, tx_id, invalid, data):
        self.tx_id = tx_id
        self.invalid = invalid
        self.data = data

    def __repr__(self):
        return '<SurveyResponse {}>'.format(self.tx_id)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


def get_store_responses(tx_id, ru_ref, survey_id):
    responses = SurveyResponse.query.all()

    store_data = []
    for response in responses:
        store_data.append(response.data)

    final_data = []
    for data in store_data:
        if (tx_id == '') or (data['tx_id'] == tx_id):
            if (ru_ref == '') or (data['metadata']['ru_ref'] == ru_ref):
                if (survey_id == '') or (data['survey_id'] == survey_id):
                    final_data.append(data)

    return final_data


@app.route('/store', methods=['GET'])
def store():
    tx_id = request.args.get('tx_id', type=str, default='')
    ru_ref = request.args.get('ru_ref', type=str, default='')
    survey_id = request.args.get('survey_id', type=str, default='')
    date_earliest = request.args.get('date_earliest', type=str, default='01/01/2000')
    store_data = get_store_responses(tx_id, ru_ref, survey_id)

    return render_template('store.html', data=store_data)


@app.route('/storetest', methods=['GET'])
def storetest():
    test_data = json.dumps(
        {
            "collection": {
                "exercise_sid": "hfjdskf",
                "instrument_id": "ce2016",
                "period": "0616"
            },
            "data": {
                "1": "2",
                "2": "4",
                "3": "2",
                "4": "Y"
            },
            "metadata": {
                "ru_ref": "12345678901a",
                "user_id": "789473423"
            },
            "origin": "uk.gov.ons.edc.eq",
            "submitted_at": "2017-04-27T14:23:13+00:00",
            "survey_id": "0",
            "tx_id": "f088d89d-a367-876e-f29f-ae8f1a26191d",
            "type": "uk.gov.ons.edc.eq:surveyresponse",
            "version": "0.0.1"
        })

    test_data2 = json.dumps(
        {
            "collection": {
                "exercise_sid": "hfjdskf",
                "instrument_id": "ce2016",
                "period": "0616"
            },
            "data": {
                "1": "2",
                "2": "4",
                "3": "2",
                "4": "Y"
            },
            "metadata": {
                "ru_ref": "12345678901a",
                "user_id": "789473423"
            },
            "origin": "uk.gov.ons.edc.eq",
            "submitted_at": "2017-04-27T14:23:13+00:00",
            "survey_id": "0",
            "tx_id": "f088d89d-a367-876e-f29f-ae8f1a26191e",
            "type": "uk.gov.ons.edc.eq:surveyresponse",
            "version": "0.0.1"
        })

    send_data(settings.SDX_STORE_URL + "responses", data=test_data, request_type="POST")
    send_data(settings.SDX_STORE_URL + "responses", data=test_data2, request_type="POST")

    return "data sent"
