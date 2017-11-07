import os
import logging
import json

from sdx.common.logger_config import logger_initial_config


logger_initial_config(service_name='sdx-console')

logger = logging.getLogger(__name__)


def get_key(key_name):
    """
    TODO remove these once the encrypted key story is finished
    :return:
    """
    key = open(key_name, 'r')
    contents = key.read()
    return contents

EQ_JWT_LEEWAY_IN_SECONDS = 120

# EQ's jwt_test_keys
EQ_PUBLIC_KEY = get_key(os.getenv('EQ_PUBLIC_KEY', "jwt_test_keys/sdc-submission-signing-sr-public-key.pem"))
EQ_PRIVATE_KEY = get_key(os.getenv('EQ_PRIVATE_KEY', "jwt_test_keys/sdc-submission-signing-sr-private-key.pem"))

# Posies jwt_test_keys
PRIVATE_KEY = get_key(os.getenv('PRIVATE_KEY', "jwt_test_keys/sdc-submission-encryption-sdx-private-key.pem"))

SDX_VALIDATE_URL = os.getenv('SDX_VALIDATE_URL', 'http://sdx-validate:5000/validate')
SDX_STORE_URL = os.getenv('SDX_STORE_URL', 'http://sdx-store:5000/')

FTP_HOST = os.getenv('FTP_HOST', 'pure-ftpd')
FTP_USER = os.getenv('FTP_USER')
FTP_PASS = os.getenv('FTP_PASS')

SDX_FTP_IMAGE_PATH = os.getenv("SDX_FTP_IMAGE_PATH", "EDC_QImages")
SDX_FTP_DATA_PATH = os.getenv("SDX_FTP_DATA_PATH", "EDC_QData")
SDX_FTP_RECEIPT_PATH = os.getenv("SDX_FTP_RECEIPT_PATH", "EDC_QReceipts")

ENABLE_EMPTY_FTP = os.getenv('ENABLE_EMPTY_FTP', 0)

RABBIT_QUEUE = os.getenv('RABBIT_SURVEY_QUEUE', 'survey')

if os.getenv("CF_DEPLOYMENT", False):
    vcap_services = os.getenv("VCAP_SERVICES")
    parsed_vcap_services = json.loads(vcap_services)
    rabbit_config = parsed_vcap_services.get('rabbitmq')

    RABBIT_URL = rabbit_config[0].get('credentials').get('uri')
    RABBIT_URL2 = rabbit_config[1].get('credentials').get('uri') if len(rabbit_config) > 1 else RABBIT_URL
else:
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
