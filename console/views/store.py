import json
import logging
import math

from datetime import datetime
from flask import Blueprint
from flask import render_template
from flask import request
import flask_security
from sqlalchemy import func
from sqlalchemy.exc import DataError
from sqlalchemy.exc import SQLAlchemyError
from structlog import wrap_logger

from console import settings
from console.database import db_session
from console.forms import StoreForm
from console.models import SurveyResponse
from console.views.submit import send_data
from sdc.rabbit import QueuePublisher

logger = wrap_logger(logging.getLogger(__name__))

store_bp = Blueprint('store_bp', __name__, static_folder='static', template_folder='templates')


def get_filtered_responses(logger, valid, tx_id, ru_ref, survey_id, datetime_earliest, datetime_latest):
    logger.info('Retrieving responses from sdx-store')
    try:
        q = db_session.query(SurveyResponse)
        if valid == "invalid":
            q = q.filter(SurveyResponse.invalid)
        elif valid == "valid":
            q = q.filter(not SurveyResponse.invalid)
        if tx_id != '':
            q = q.filter(SurveyResponse.tx_id == tx_id)
        if ru_ref != '':
            q = q.filter(SurveyResponse.data["metadata"]["ru_ref"].astext == ru_ref)
        if survey_id != '':
            q = q.filter(SurveyResponse.data["survey_id"].astext == survey_id)
        dt_column = func.date(SurveyResponse.data["submitted_at"].astext)
        if datetime_earliest:
            year = int(datetime_earliest[:4])
            month = int(datetime_earliest[5:7])
            day = int(datetime_earliest[8:10])
            hour = int(datetime_earliest[11:13])
            minute = int(datetime_earliest[14])
            q = q.filter(dt_column > datetime(year, month, day, hour, minute))
        if datetime_latest:
            year = int(datetime_latest[:4])
            month = int(datetime_latest[5:7])
            day = int(datetime_latest[8:10])
            hour = int(datetime_latest[11:13])
            minute = int(datetime_latest[14])
            q = q.filter(dt_column < datetime(year, month, day, hour, minute))
        filtered_data = q.all()
    except DataError as e:
        logger.error("Invalid search term", error=e)
        return []
    except SQLAlchemyError as e:
        logger.error("Database error", error=e)
        return []

    return filtered_data


def reprocess(tx_id):
    logger.debug('Reprocess function')
    publisher = QueuePublisher(
        settings.RABBIT_URLS,
        'sdx-survey-notification-durable'
    )

    publisher.publish_message(tx_id, headers={'tx_id': tx_id})


@store_bp.route('/reprocess', strict_slashes=False, methods=['POST'])
@flask_security.login_required
def reprocess_submission():
    tx_ids = request.form.getlist('reprocess-tx_id')
    data = []
    for tx_id in tx_ids:
        logger.debug('Begin reprocessing tx_id: {}'.format(tx_id))
        data.append(tx_id)
        reprocess(tx_id)

    return render_template('reprocess.html', data=data)


@store_bp.route('/store', strict_slashes=False, defaults={'page': 0}, methods=['GET'])
@store_bp.route('/store/<page>', strict_slashes=False, methods=['GET'])
@flask_security.login_required
def store(page):
    audited_logger = logger.bind(user=flask_security.core.current_user.email)

    valid = request.args.get('valid', type=str, default='')
    tx_id = request.args.get('tx_id', type=str, default='')
    ru_ref = request.args.get('ru_ref', type=str, default='')
    survey_id = request.args.get('survey_id', type=str, default='')
    datetime_earliest = request.args.get('datetime_earliest', type=str, default='')
    datetime_latest = request.args.get('datetime_latest', type=str, default='')

    form = StoreForm(tx_id=tx_id)
    if form.validate():
        store_data = get_filtered_responses(
            audited_logger, valid, tx_id, ru_ref, survey_id, datetime_earliest, datetime_latest)
    else:
        # If validation unsuccessful, pretend it was an empty search to give user
        # more than an empty results table to look at
        store_data = get_filtered_responses(audited_logger, '', '', '', '', '', '')

    audited_logger.info("Successfully retrieved responses")

    json_list = [item.data for item in store_data]

    no_pages = math.ceil(round(float(len(json_list) / 20)))

    return render_template('store.html',
                           data=json_list,
                           no_pages=no_pages,
                           page=int(page),
                           current_user=flask_security.core.current_user,
                           form=form)


@store_bp.route('/storetest', strict_slashes=False, methods=['GET'])
def storetest():
    def create_test_data(number):
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
                "survey_id": "1",
                "tx_id": "f088d89d-a367-876e-f29f-ae8f1a26" + str(number),
                "type": "uk.gov.ons.edc.eq:surveyresponse",
                "version": "0.0.1"
            })
        return test_data

    for i in range(1000, 1250):
        test_data = create_test_data(str(i))
        send_data(logger=logger,
                  url=settings.SDX_STORE_URL,
                  data=test_data,
                  request_type="POST")

    return "data sent"
