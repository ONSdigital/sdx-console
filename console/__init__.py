from flask import Flask

app = Flask(__name__)
app.config['USE_MLSD'] = True

import console.views  # noqa
