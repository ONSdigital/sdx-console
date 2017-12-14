import json
import logging

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
from console.forms import StoreForm
from console.models import SurveyResponse
from console.views.submit import send_data
from sdc.rabbit import QueuePublisher

logger = wrap_logger(logging.getLogger(__name__))

store_bp = Blueprint('store_bp', __name__, static_folder='static', template_folder='templates')

TRANSACTIONS_PER_PAGE = 20


def get_filtered_responses(logger, valid, tx_id, ru_ref, survey_id, datetime_earliest, datetime_latest, page_num):
    logger.info('Retrieving responses from sdx-store')
    try:
        q = SurveyResponse.query

        if valid == "invalid":
            q = q.filter(SurveyResponse.invalid)
        elif valid == "valid":
            #  NOQA comment is used because == False is the correct syntax, but flake8 disagrees
            q = q.filter(SurveyResponse.invalid == False)  # NOQA
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
        filtered_data = q.paginate(per_page=TRANSACTIONS_PER_PAGE, page=page_num, error_out=True)

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


@store_bp.route('/store', strict_slashes=False, methods=['GET'])
@flask_security.login_required
def store_home():
    return render_template('store.html',
                           current_user=flask_security.core.current_user,
                           form=StoreForm())


@store_bp.route('/store/page/<int:page_num>', strict_slashes=False, methods=['GET'])
@flask_security.login_required
def store(page_num):
    audited_logger = logger.bind(user=flask_security.core.current_user.email)
    valid = request.args.get('valid', type=str, default='')
    tx_id = request.args.get('tx_id', type=str, default='')
    ru_ref = request.args.get('ru_ref', type=str, default='')
    survey_id = request.args.get('survey_id', type=str, default='')
    datetime_earliest = request.args.get('datetime_earliest', type=str, default='')
    datetime_latest = request.args.get('datetime_latest', type=str, default='')
    search_query = {
        "tx_id": tx_id,
        "ru_ref": ru_ref,
        "survey_id": survey_id,
        "datetime_earliest": datetime_earliest,
        "datetime_latest": datetime_latest
    }

    # These two variables are either empty, or datetime objects.  A separate variable had
    # to be used as we need the string representation of the date for the database filter and a
    # datetime representation of the date for the StoreForm object.
    datetime_earliest_value = None
    datetime_latest_value = None
    if datetime_earliest:
        datetime_earliest_value = datetime.strptime(datetime_earliest, '%Y-%m-%dT%H:%M')
    if datetime_latest:
        datetime_latest_value = datetime.strptime(datetime_latest, '%Y-%m-%dT%H:%M')

    form = StoreForm(
        valid=valid,
        tx_id=tx_id,
        ru_ref=ru_ref,
        survey_id=survey_id,
        datetime_earliest=datetime_earliest_value,
        datetime_latest=datetime_latest_value
    )

    if form.validate():
        pagnated_store_data = get_filtered_responses(
            audited_logger, valid, tx_id, ru_ref, survey_id, datetime_earliest, datetime_latest, page_num)
    else:
        pagnated_store_data = []

    audited_logger.info("Successfully retrieved responses")

    audited_logger.info("Search query: {}".format(search_query))

    return render_template('store_data.html',
                           data=pagnated_store_data,
                           search_query=search_query,
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
