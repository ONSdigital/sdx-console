import logging

from flask import Blueprint
from flask import jsonify
from flask import render_template
from flask import request
import flask_security
import requests
from structlog import wrap_logger

from console.helpers.exceptions import ClientError, ResponseError, ServiceError

logger = wrap_logger(logging.getLogger(__name__))

home_bp = Blueprint('home_bp', __name__, static_folder='static', template_folder='templates')


@home_bp.route('/home', strict_slashes=False, methods=['GET', 'POST'])
@flask_security.login_required
def home():
    return render_template('home.html',
                           current_user=flask_security.core.current_user,
                           request=request)


@home_bp.errorhandler(ResponseError)
def handle_invalid_usage(error):
    json_error = {"message": error.message, "status_code": error.status_code}
    return jsonify(json_error)


@home_bp.route('/healthcheck', strict_slashes=False, methods=['GET'])
def healthcheck():
    return jsonify({'status': 'OK'})


def send_data(logger, url, data=None, json=None, request_type="POST"):
    response_logger = logger.bind(url=url)
    try:
        if request_type == "POST":
            response_logger.info("Sending POST request")
            if data:
                r = requests.post(url, data=data)
            elif json:
                r = requests.post(url, json=json)
        elif request_type == "GET":
            response_logger.info("Sending GET request")
            r = requests.get(url)
    except requests.exceptions.ConnectionError as e:
        response_logger.error("Failed to connect to service", response="Connection error")
        raise e

    if 199 < r.status_code < 300:
        logger.info('Returned from service', response=r.reason, status_code=r.status_code)
    elif 399 < r.status_code < 500:
        logger.error('Returned from service', response=r.reason, status_code=r.status_code)
        raise ClientError(url=url, message=r.reason, status_code=r.status_code)
    elif r.status_code > 499:
        logger.error('Returned from service', response=r.reason, status_code=r.status_code)
        raise ServiceError(url=url, message=r.reason, status_code=r.status_code)

    return r
