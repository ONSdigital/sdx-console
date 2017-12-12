from datetime import timedelta
import logging

from flask import Flask
from flask import session
from flask_sqlalchemy import SQLAlchemy
from structlog import wrap_logger

from console import settings


__version__ = "2.0.0"
logging.basicConfig(format=settings.LOGGING_FORMAT,
                    datefmt="%Y-%m-%dT%H:%M:%S",
                    level=settings.LOGGING_LEVEL)
logging.getLogger("sdc.rabbit").setLevel(logging.DEBUG)
logger = wrap_logger(logging.getLogger(__name__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DB_URI
app.config['SECURITY_PASSWORD_HASH'] = settings.SECURITY_PASSWORD_HASH
app.config['SECRET_KEY'] = settings.SECRET_KEY
app.config['SECURITY_PASSWORD_SALT'] = settings.SECURITY_PASSWORD_SALT
app.config['WTF_CSRF_ENABLED'] = False
app.config['USE_MLSD'] = True
app.config['DEVELOPMENT_MODE'] = settings.DEVELOPMENT_MODE
db = SQLAlchemy(app)


@app.before_request
def session_timeout():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=settings.CONSOLE_LOGIN_TIMEOUT)


import console.views  # noqa
