import logging
import os

from structlog import wrap_logger


LOGGING_LEVEL = logging.getLevelName(os.getenv('LOGGING_LEVEL', 'DEBUG'))
LOGGING_FORMAT = "%(asctime)s.%(msecs)06dZ|%(levelname)s: sdx-console: %(message)s"

logger = wrap_logger(logging.getLogger(__name__))
DEVELOPMENT_MODE = os.getenv('DEVELOPMENT_MODE', False)

DB_HOST = os.getenv('SDX_CONSOLE_POSTGRES_HOST', '0.0.0.0')
DB_PORT = os.getenv('SDX_CONSOLE_POSTGRES_PORT', '5432')
DB_NAME = os.getenv('SDX_CONSOLE_POSTGRES_NAME', 'postgres')
DB_USER = os.getenv('SDX_CONSOLE_POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('SDX_CONSOLE_POSTGRES_PASSWORD', 'secret')
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

HB_INTERVAL = os.getenv("HB_INTERVAL", 30)

SDX_STORE_URL = os.getenv("SDX_STORE_URL", "http://sdx-store:5000/responses")
SDX_VALIDATE_URL = os.getenv("SDX_VALIDATE_URL", "http://sdx-validate:5000/validate")

FTP_HOST = os.getenv('FTP_HOST', 'pure-ftpd')
FTP_USER = os.getenv('FTP_USER')
FTP_PASS = os.getenv('FTP_PASS')

SDX_FTP_IMAGE_PATH = os.getenv("SDX_FTP_IMAGE_PATH", "EDC_QImages")
SDX_FTP_DATA_PATH = os.getenv("SDX_FTP_DATA_PATH", "EDC_QData")
SDX_FTP_RECEIPT_PATH = os.getenv("SDX_FTP_RECEIPT_PATH", "EDC_QReceipts")
SDX_RESPONSE_JSON_PATH = os.getenv("SDX_RESPONSE_JSON_PATH", "EDC_QJson")


RABBIT_QUEUE = os.getenv('RABBIT_SURVEY_QUEUE', 'survey')
SEFT_CONSUMER_RABBIT_QUEUE = os.getenv('SEFT_CONSUMER_RABBIT_QUEUE', 'Seft.Responses')


RABBIT_URL = 'amqp://{user}:{password}@{hostname}:{port}/{vhost}'.format(
    hostname=os.getenv('RABBITMQ_HOST', 'rabbit'),
    port=os.getenv('RABBITMQ_PORT', 5672),
    user=os.getenv('RABBITMQ_DEFAULT_USER', 'rabbit'),
    password=os.getenv('RABBITMQ_DEFAULT_PASS', 'rabbit'),
    vhost=os.getenv('RABBITMQ_DEFAULT_VHOST', '%2f')
)

RABBIT_URLS = [RABBIT_URL]
