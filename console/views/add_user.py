import logging

from flask import Blueprint
from flask import render_template
from flask import request
import flask_security
from structlog import wrap_logger

from console import create_dev_user
from console.forms import NewUserForm
from console.helpers.exceptions import UserCreationError, UserExistsError

logger = wrap_logger(logging.getLogger(__name__))

add_user_bp = Blueprint('add_user_bp', __name__, static_folder='static', template_folder='templates')


@add_user_bp.route('/add_user', strict_slashes=False, methods=['GET', 'POST'])
@flask_security.roles_required('Admin')
def add_user():
    form = NewUserForm()
    if request.method == 'POST' and form.validate():
        success = False
        try:
            create_dev_user(form.email.data, form.password.data)
            success = True
        except UserCreationError:
            form.errors['Database'] = ["Error creating user"]
        except UserExistsError:
            form.errors['User'] = ["This user already exists"]

        return render_template('add_user.html', form=form, success=success, user=form.email.data)

    else:
        return render_template('add_user.html', form=form)
