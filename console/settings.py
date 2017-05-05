import os
import logging

logger = logging.getLogger(__name__)

LOGGING_FORMAT = "%(asctime)s|%(levelname)s: sdx-console: %(message)s"
LOGGING_LEVEL = logging.getLevelName(os.getenv('LOGGING_LEVEL', 'DEBUG'))


def get_key(key_name):
    """
    TODO remove these once the encrypted key story is finished
    :return:
    """
    logger.debug("Opening file %", key_name)
    key = open(key_name, 'r')
    contents = key.read()
    logger.debug("Key is %s", contents)
    return contents


EQ_JWT_LEEWAY_IN_SECONDS = 120

# EQ's keys
EQ_PUBLIC_KEY = get_key(os.getenv('EQ_PUBLIC_KEY'))
EQ_PRIVATE_KEY = get_key(os.getenv('EQ_PRIVATE_KEY'))
EQ_PRIVATE_KEY_PASSWORD = os.getenv("EQ_PRIVATE_KEY_PASSWORD")

# Posies keys
PRIVATE_KEY = get_key(os.getenv('PRIVATE_KEY'))
PRIVATE_KEY_PASSWORD = os.getenv("PRIVATE_KEY_PASSWORD")

SDX_VALIDATE_URL = os.getenv('SDX_VALIDATE_URL')
SDX_STORE_URL = os.getenv('SDX_STORE_URL')

FTP_HOST = os.getenv('FTP_HOST')
FTP_USER = os.getenv('FTP_USER')
FTP_PASS = os.getenv('FTP_PASS')

SDX_FTP_IMAGE_PATH = os.getenv("SDX_FTP_IMAGE_PATH")
SDX_FTP_DATA_PATH = os.getenv("SDX_FTP_DATA_PATH")
SDX_FTP_RECEIPT_PATH = os.getenv("SDX_FTP_RECEIPT_PATH")

ENABLE_EMPTY_FTP = os.getenv('ENABLE_EMPTY_FTP')

RABBIT_QUEUE = os.getenv('RABBIT_SURVEY_QUEUE')

RABBIT_URL = 'amqp://{user}:{password}@{hostname}:{port}/{vhost}'.format(
    hostname=os.getenv('RABBITMQ_HOST'),
    port=os.getenv('RABBITMQ_PORT'),
    user=os.getenv('RABBITMQ_DEFAULT_USER'),
    password=os.getenv('RABBITMQ_DEFAULT_PASS'),
    vhost=os.getenv('RABBITMQ_DEFAULT_VHOST')
)

RABBIT_URL2 = 'amqp://{user}:{password}@{hostname}:{port}/{vhost}'.format(
    hostname=os.getenv('RABBITMQ_HOST2'),
    port=os.getenv('RABBITMQ_PORT2'),
    user=os.getenv('RABBITMQ_DEFAULT_USER'),
    password=os.getenv('RABBITMQ_DEFAULT_PASS'),
    vhost=os.getenv('RABBITMQ_DEFAULT_VHOST')
)

RABBIT_URLS = [RABBIT_URL, RABBIT_URL2]
