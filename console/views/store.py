import ast
import json
import logging
import math

from datetime import datetime
from flask import Blueprint
from flask import render_template
from flask import request
from flask import url_for
import flask_security
from sqlalchemy import func
from sqlalchemy.exc import DataError
from sqlalchemy.exc import SQLAlchemyError
from structlog import wrap_logger
from werkzeug.utils import redirect

from console import settings
from console.database import db_session
from console.models import SurveyResponse
from console.views.home import send_data
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


def reprocess_transaction(logger, json_data):
    logger.info("Reprocessing transaction", tx_id=json_data["tx_id"])
    if json_data.get("invalid"):
        del json_data["invalid"]

    validate_response = send_data(logger=logger,
                                  url=settings.SDX_VALIDATE_URL,
                                  json=json_data,
                                  request_type="POST")

    logger.debug(validate_response)

    if validate_response != 200:
        json_data['invalid'] = "True"

    send_data(logger=logger,
              url=settings.SDX_STORE_URL,
              json=json_data,
              request_type="POST")


def reprocess(tx_id):
    logger.info('reprocess function')
    publisher = QueuePublisher(
        settings.RABBIT_URLS,
        'sdx-survey-notification-durable'
    )

    publisher.publish_message(tx_id, headers={'tx_id': tx_id})


@store_bp.route('/reprocess', strict_slashes=False, methods=['POST'])
@flask_security.login_required
def reprocess_submission():
    logger.debug('Begin reprocess debug')
    logger.error('Begin reprocess error')
    # json_survey_data = request.form.get('tx_id')
    # json_single_data = json.loads(json_survey_data.replace("'", '"'))
    # json_data_tx_id = json_survey_data

    reprocess("f088d89d-a367-876e-f29f-ae8f1a261000")

    return "data reprocessed", 200


@store_bp.route('/store', strict_slashes=False, defaults={'page': 0}, methods=['GET'])
@store_bp.route('/store/<page>', strict_slashes=False, methods=['GET', 'POST'])
@flask_security.login_required
def store(page):
    audited_logger = logger.bind(user=flask_security.core.current_user.email)
    # if request.method == 'POST':
    #     json_survey_data = request.form.get('json_data')
    #     if not json_survey_data:
    #         json_survey_data = request.form.get('json_data_list')
    #         if not json_survey_data:
    #             return url_for('store_bp.store')
    #         json_survey_data = ast.literal_eval(json_survey_data)
    #
    #     if isinstance(json_survey_data, list):
    #         try:
    #             audited_logger.info("Reprocessing multiple transactions")
    #             for json_data in json_survey_data:
    #                 json_single_data = json.loads(json_data.replace("'", '"'))
    #                 reprocess_transaction(audited_logger, json_single_data)
    #                 logger.debug("Reprocessed multiple transactions successfully")
    #         except:
    #             logger.error("Failed reprocessing multiple transactions")
    #     else:
    #         try:
    #             audited_logger.info("Reprocessing transaction")
    #             json_single_data = json.loads(json_survey_data.replace("'", '"'))
    #             reprocess_transaction(audited_logger, json_single_data)
    #             logger.debug("Reprocessed transactions successfully")
    #         except:
    #             logger.error('Failed reprocessing transaction')
    #     return redirect(url_for('store_bp.store'))
    #
    # else:
    valid = request.args.get('valid', type=str, default='')
    tx_id = request.args.get('tx_id', type=str, default='')
    ru_ref = request.args.get('ru_ref', type=str, default='')
    survey_id = request.args.get('survey_id', type=str, default='')
    datetime_earliest = request.args.get('datetime_earliest', type=str, default='')
    datetime_latest = request.args.get('datetime_latest', type=str, default='')
    store_data = get_filtered_responses(
        audited_logger, valid, tx_id, ru_ref, survey_id, datetime_earliest, datetime_latest)
    audited_logger.info("Successfully retrieved responses")
    json_list = [item.data for item in store_data]
    logger.debug(json_list)
    no_pages = math.ceil(round(float(len(json_list) / 20)))

    return render_template('store.html',
                           data=json_list,
                           no_pages=no_pages,
                           page=int(page),
                           current_user=flask_security.core.current_user)


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
