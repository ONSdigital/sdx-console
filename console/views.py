from flask import request, render_template, jsonify

from console import app

import console.settings as settings
from structlog import wrap_logger

import json
import logging
import logging.handlers
import time


logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
logger = wrap_logger(logging.getLogger(__name__))

def heartbeat():
    heartbeats = 0
    while True:
        logger.info("Heartbeat " + str(heartbeats))
        heartbeats += 1
        time.sleep(30.0)

heartbeat()
