import os
import logging

from sdx.common.logger_config import logger_initial_config
from structlog import wrap_logger

logger_initial_config(service_name='sdx-console')
logger = wrap_logger(logging.getLogger(__name__))


class BaseConfig(object):
    DEBUG = False
    TESTING = False
    PORT = os.getenv("PORT")

    # Database Config
    DB_HOST = os.getenv('POSTGRES_HOST', '0.0.0.0')
    DB_PORT = os.getenv('POSTGRES_PORT', '5432')
    DB_NAME = os.getenv('POSTGRES_NAME', 'postgres')
    DB_USER = os.getenv('POSTGRES_USER', 'postgres')
    DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'secret')
    SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}:{}/{}'.format(DB_USER,
                                                                   DB_PASSWORD,
                                                                   DB_HOST,
                                                                   DB_PORT,
                                                                   DB_NAME)

    # Flask - Security
    SECURITY_PASSWORD_HASH = os.getenv('CONSOLE_PASSWORD_HASH', 'bcrypt')
    SECRET_KEY = os.getenv('CONSOLE_SECRET_KEY', 'secretwords')
    SECURITY_PASSWORD_SALT = os.getenv('CONSOLE_PASSWORD_SALT', '1ab')
    CONSOLE_LOGIN_TIMEOUT = os.getenv('CONSOLE_LOGIN_TIMEOUT', 10)
    CONSOLE_INITIAL_ADMIN_PASSWORD = os.getenv('CONSOLE_INITIAL_ADMIN_PASSWORD')

    # Auth config
    WTF_CSRF_ENABLED = False

    # Rabbit Heartbeat
    HB_INTERVAL = os.getenv("HB_INTERVAL", 30)
    SDX_STORE_URL = os.getenv("SDX_STORE_URL", "http://sdx-store:5000/responses")
    SDX_VALIDATE_URL = os.getenv("SDX_VALIDATE_URL", "http://sdx-validate:5000/validate")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = True


class TestingConfig(BaseConfig):
    DEBUG = False
    TESTING = True
