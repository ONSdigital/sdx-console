import logging
import requests

from flask import redirect
from flask import render_template
from flask import request
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import flask_security
from flask_sqlalchemy import SQLAlchemy
from structlog import wrap_logger

from console import app
from console.authentication import db, user_datastore, User, Role, UserAdmin, RoleAdmin
from console import settings
from console.helpers.exceptions import ClientError, ServiceError

logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
logger = wrap_logger(logging.getLogger(__name__))


@app.route('/', methods=['GET'])
@flask_security.login_required
def login():
    return redirect('/decrypt')


def send_data(url, data):
    try:
        r = requests.post(url, data)
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
def decrypt():
    if request.method == "POST":
        data = request.form['EncryptedData']
        url = settings.SDX_DECRYPT_URL
        decrypted_data = ""

        try:
            logger.info("Posting data to sdx-decrypt")
            decrypt_response = send_data(url, data)
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

admin = Admin(app, template_mode='bootstrap3')
# admin.add_view(ModelView(User, db.session))
admin.add_view(UserAdmin(User, db.session))
admin.add_view(RoleAdmin(Role, db.session))
