import logging

from flask import Blueprint, render_template
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))

info_bp = Blueprint('info_bp', __name__, static_folder='static', template_folder='templates')


@info_bp.route('/info', strict_slashes=False, methods=['GET'])
def get_info_page():
    return render_template('info.html')
