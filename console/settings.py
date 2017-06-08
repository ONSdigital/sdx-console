import logging
import os

from sdx.common.logger_config import logger_initial_config


logger_initial_config(service_name='sdx-console')
logger = logging.getLogger(__name__)

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

PORT = os.getenv("PORT", 5000)

HB_INTERVAL = os.getenv("HB_INTERVAL", 30)

SDX_DECRYPT_URL = os.getenv("SDX_DECRYPT_URL", "http://sdx-decrypt:5000/decrypt")
SDX_STORE_URL = os.getenv("SDX_STORE_URL", "http://sdx-store:5000/")

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
RABBIT_SURVEY_QUEUE = os.getenv('RABBIT_SURVEY_QUEUE', 'survey')
