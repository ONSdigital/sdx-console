from flask import Flask

__version__ = "1.1.0"

app = Flask(__name__)
app.config['USE_MLSD'] = True

import console.views  # noqa
