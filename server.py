import logging
import os
from threading import Timer

from structlog import wrap_logger

from console import __version__
from console import app
from console import settings


logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
logger = wrap_logger(logging.getLogger(__name__))


class HeartbeatTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)
        if self._timer:
            self._timer.join()

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


def heartbeat(logger=logger):
    logger.info("Heartbeat")


if __name__ == '__main__':
    logger.info("Starting server: version='{}'".format(__version__))
    port = int(settings.PORT)
    hb = HeartbeatTimer(settings.HB_INTERVAL, heartbeat, logger)
    app.run(debug=True, host='0.0.0.0', port=port)
