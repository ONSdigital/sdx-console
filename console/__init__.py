from flask import Flask

__version__ = "1.5.1"

app = Flask(__name__)
app.config['USE_MLSD'] = True

import console.views  # noqa
