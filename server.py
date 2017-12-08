import logging

from flask import redirect
from flask import url_for
from structlog import wrap_logger

from console import __version__
from console import app
from console import settings

logger = wrap_logger(logging.getLogger(__name__))


@app.route('/')
def localhost_to_submit():
    return redirect(url_for('submit_bp.submit'))

if __name__ == '__main__':
    logger.info("Starting server: version='{}'".format(__version__))
    port = int(settings.PORT)
    app.run(debug=True, host='0.0.0.0', port=port)
