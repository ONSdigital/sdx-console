from flask import Flask

app = Flask(__name__)
app.config['USE_MLSD'] = False

import console.views  # noqa
