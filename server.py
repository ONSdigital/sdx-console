import logging
from flask import jsonify

from structlog import wrap_logger
from console import __version__
from console import app
from console import settings


logger = wrap_logger(logging.getLogger(__name__))

if __name__ == '__main__':
    logger.info("Starting server: version='{}'".format(__version__))
    port = int(settings.PORT)
    app.run(debug=True, host='0.0.0.0', port=port)

