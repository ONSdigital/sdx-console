import console.settings as settings

import logging
import logging.handlers
from structlog import wrap_logger

from threading import Timer


logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
logger = wrap_logger(logging.getLogger(__name__))


def heartbeat(logger=logger, heartbeats=0):
    logger.info("Heartbeat " + str(heartbeats))
    heartbeats += 1
    Timer(30.0, heartbeat, [logger, heartbeats]).start()

heartbeat()
