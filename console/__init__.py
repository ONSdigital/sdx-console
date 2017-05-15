from flask import Flask

__version__ = "2.0.0"

app = Flask(__name__)

import console.views  # noqa
from console import authentication  # noqa
