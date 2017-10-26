import logging

from flask import Blueprint
from flask import render_template
from flask import request
import flask_security
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))

test_bp = Blueprint('test_bp', __name__, static_folder='static', template_folder='templates')


@test_bp.route('/test', strict_slashes=False, methods=['GET', 'POST'])
def test():
    return render_template('test.html',
                           current_user=flask_security.core.current_user,
                           request=request)
