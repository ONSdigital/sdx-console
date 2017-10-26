import logging

from flask import Blueprint
from flask import jsonify
from flask import render_template
import flask_security
from structlog import wrap_logger

from console.helpers.exceptions import ResponseError

logger = wrap_logger(logging.getLogger(__name__))

logout_bp = Blueprint('logout_bp', __name__, static_folder='static', template_folder='templates')


@logout_bp.route('/logout', strict_slashes=False, methods=['GET', 'POST'])
def logout():
    flask_security.utils.logout_user()
    return render_template('logout.html')


@logout_bp.errorhandler(ResponseError)
def handle_invalid_usage(error):
    json_error = {"message": error.message, "status_code": error.status_code}
    return jsonify(json_error)
