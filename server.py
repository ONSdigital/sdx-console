from console import app
import logging
import os

from console import __version__

from sdx.common.logger_config import logger_initial_config

logger_initial_config(service_name='sdx-console')
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Starting server: version='{}'".format(__version__))
    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
