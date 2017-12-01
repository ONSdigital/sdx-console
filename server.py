import logging

from flask import redirect
from flask import url_for
from structlog import wrap_logger

from console import __version__
from console import app
from console import settings
from console.settings import LOGGING_FORMAT
from console.settings import LOGGING_LEVEL

logger = wrap_logger(logging.getLogger(__name__))


@app.route('/')
def localhost_to_submit():
    return redirect(url_for('submit_bp.submit'))

if __name__ == '__main__':
    logging.basicConfig(format=LOGGING_FORMAT,
                        datefmt="%Y-%m-%dT%H:%M:%S",
                        level=LOGGING_LEVEL)
    logging.getLogger("sdc.rabbit").setLevel(logging.DEBUG)
    logger.info("Starting server: version='{}'".format(__version__))
    port = int(settings.PORT)
    app.run(debug=True, host='0.0.0.0', port=port)
