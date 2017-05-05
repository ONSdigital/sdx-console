from console import app
import logging
import os
import sys

from console import __version__

logger = logging.getLogger(__name__)


def _get_value(key):
    value = os.getenv(key)
    if not value:
        raise ValueError("No value set for " + key)


def check_default_env_vars():

    env_vars = ["EQ_PUBLIC_KEY", "EQ_PRIVATE_KEY", "EQ_PRIVATE_KEY_PASSWORD", "PRIVATE_KEY", "PRIVATE_KEY_PASSWORD",
                "SDX_VALIDATE_URL", "SDX_STORE_URL", "FTP_HOST", "FTP_USER", "FTP_PASS", "SDX_FTP_IMAGE_PATH",
                "SDX_FTP_DATA_PATH", "SDX_FTP_RECEIPT_PATH", "ENABLE_EMPTY_FTP", "RABBIT_SURVEY_QUEUE",
                "RABBITMQ_HOST", "RABBITMQ_PORT", "RABBITMQ_DEFAULT_USER", "RABBITMQ_DEFAULT_PASS",
                "RABBITMQ_DEFAULT_VHOST", "RABBITMQ_HOST2", "RABBIT_PORT2"]

    missing_env_var = False

    for i in env_vars:
        try:
            _get_value(i)
        except ValueError as e:
            logger.error("Unable to start service", error=e)
            missing_env_var = True

    if missing_env_var is True:
        sys.exit(1)


if __name__ == '__main__':
    logger.info("Starting server: version='{}'".format(__version__))
    check_default_env_vars()
    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
