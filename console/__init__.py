from datetime import timedelta
import logging

from flask import Flask
from flask import session
from flask_sqlalchemy import SQLAlchemy
from structlog import wrap_logger
from ftplib import FTP

from console import settings


__version__ = "2.2.0"
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
app.config['DEVELOPMENT_MODE'] = settings.DEVELOPMENT_MODE
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
db = SQLAlchemy(app)

try:
    logger.info("Checking if FTP server supports MLSD")
    ftp = FTP(settings.FTP_HOST)
    ftp.login(user=settings.FTP_USER, passwd=settings.FTP_PASS)
    len([fname for fname, fmeta in ftp.mlsd(path=settings.SDX_FTP_DATA_PATH)])
except Exception:
    logger.exception("MLSD command not availible in the FTP server, will use LIST instead")
    app.config['USE_MLSD'] = False
else:
    logger.info("MLSD will be used to communicate with the FTP server")
    app.config['USE_MLSD'] = True


@app.before_request
def session_timeout():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=settings.CONSOLE_LOGIN_TIMEOUT)


import console.views  # noqa
