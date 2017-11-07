import logging
import os

from sdx.common.logger_config import logger_initial_config
from structlog import wrap_logger


def get_key(key_name):
    """
    TODO remove these once the encrypted key story is finished
    :return:
    """
    key = open(key_name, 'r')
    contents = key.read()
    return contents

logger_initial_config(service_name='sdx-console')
logger = wrap_logger(logging.getLogger(__name__))

DB_HOST = os.getenv('POSTGRES_HOST', '0.0.0.0')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_NAME', 'postgres')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'secret')
DB_URI = 'postgresql://{}:{}@{}:{}/{}'.format(DB_USER,
                                              DB_PASSWORD,
                                              DB_HOST,
                                              DB_PORT,
                                              DB_NAME)

SECURITY_PASSWORD_HASH = os.getenv('CONSOLE_PASSWORD_HASH', 'bcrypt')
SECRET_KEY = os.getenv('CONSOLE_SECRET_KEY', 'secretwords')
SECURITY_PASSWORD_SALT = os.getenv('CONSOLE_PASSWORD_SALT', '1ab')
CONSOLE_LOGIN_TIMEOUT = os.getenv('CONSOLE_LOGIN_TIMEOUT', 10)
CONSOLE_INITIAL_ADMIN_PASSWORD = os.getenv('CONSOLE_INITIAL_ADMIN_PASSWORD', 'admin')

SQLALCHEMY_DATABASE_URI = DB_URI
WTF_CSRF_ENABLED = False

PORT = os.getenv("PORT", 5000)

ENABLE_EMPTY_FTP = os.getenv('ENABLE_EMPTY_FTP', 0)

HB_INTERVAL = os.getenv("HB_INTERVAL", 30)

SDX_STORE_URL = os.getenv("SDX_STORE_URL", "http://sdx-store:5000/responses")
SDX_VALIDATE_URL = os.getenv("SDX_VALIDATE_URL", "http://sdx-validate:5000/validate")

FTP_PATH = os.getenv('FTP_PATH', 'pure-ftpd')
FTP_USER = os.getenv('FTP_USER')
FTP_PASS = os.getenv('FTP_PASS')

SDX_FTP_IMAGE_PATH = os.getenv("SDX_FTP_IMAGE_PATH", "EDC_QImages")
SDX_FTP_DATA_PATH = os.getenv("SDX_FTP_DATA_PATH", "EDC_QData")
SDX_FTP_RECEIPT_PATH = os.getenv("SDX_FTP_RECEIPT_PATH", "EDC_QReceipts")

RABBIT_QUEUE = os.getenv('RABBIT_SURVEY_QUEUE', 'survey')

RABBIT_URL = 'amqp://{user}:{password}@{hostname}:{port}/{vhost}'.format(
    hostname=os.getenv('RABBITMQ_HOST', 'rabbit'),
    port=os.getenv('RABBITMQ_PORT', 5672),
    user=os.getenv('RABBITMQ_DEFAULT_USER', 'rabbit'),
    password=os.getenv('RABBITMQ_DEFAULT_PASS', 'rabbit'),
    vhost=os.getenv('RABBITMQ_DEFAULT_VHOST', '%2f')
)

RABBIT_URL2 = 'amqp://{user}:{password}@{hostname}:{port}/{vhost}'.format(
    hostname=os.getenv('RABBITMQ_HOST2', 'rabbit'),
    port=os.getenv('RABBITMQ_PORT2', 5672),
    user=os.getenv('RABBITMQ_DEFAULT_USER', 'rabbit'),
    password=os.getenv('RABBITMQ_DEFAULT_PASS', 'rabbit'),
    vhost=os.getenv('RABBITMQ_DEFAULT_VHOST', '%2f')
)

RABBIT_URLS = [RABBIT_URL, RABBIT_URL2]
