from datetime import timedelta
import logging

from flask import Flask
from flask import session
from flask_admin import Admin
import flask_security
from flask_security import SQLAlchemySessionUserDatastore
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from structlog import wrap_logger
from wtforms.fields import HiddenField

from console import settings
from console.database import db_session, init_db
from console.models import FlaskUser, Role, RoleAdmin, UserAdmin
from console.helpers.exceptions import UserCreationError, UserExistsError


class LoginFormExtended(flask_security.forms.LoginForm):
    # Overriding LoginForm to remove remember me button
    remember = HiddenField('')


__version__ = "2.0.0"

logger = wrap_logger(logging.getLogger(__name__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DB_URI
app.config['SECURITY_PASSWORD_HASH'] = settings.SECURITY_PASSWORD_HASH
app.config['SECRET_KEY'] = settings.SECRET_KEY
app.config['SECURITY_PASSWORD_SALT'] = settings.SECURITY_PASSWORD_SALT
app.config['WTF_CSRF_ENABLED'] = False

user_datastore = SQLAlchemySessionUserDatastore(db_session, FlaskUser, Role)
security = flask_security.Security(app, user_datastore, login_form=LoginFormExtended)

admin = Admin(app, template_mode='bootstrap3')
admin.add_view(UserAdmin(FlaskUser, db_session))
admin.add_view(RoleAdmin(Role, db_session))


def create_initial_users():
    logger.info("Creating initial roles and users")
    try:
        user_datastore.find_or_create_role(name='Admin', description='Edit Roles/Users')
        db_session.commit()

        user_datastore.find_or_create_role(name='SDX-Developer',
                                           description='Usual console functionality')
        encrypted_password = flask_security.utils.hash_password(
            settings.CONSOLE_INITIAL_ADMIN_PASSWORD)
        db_session.commit()

        if not user_datastore.get_user('admin'):
            user_datastore.create_user(email='admin', password=encrypted_password)
            db_session.commit()

        user_datastore.add_role_to_user('admin', 'Admin')
        db_session.commit()
    except IntegrityError as e:
        logger.error('A user/role already exists', error=e)
        db_session.rollback()
    except SQLAlchemyError as e:
        logger.error("Error creating initial users and roles", error=e)
        db_session.rollback()


def create_dev_user(email, password):
    logger.info("Creating SDX-Developer %s" % email)
    try:
        encrypted_password = flask_security.utils.hash_password(password)
        if not user_datastore.get_user(email):
            user_datastore.create_user(email=email, password=encrypted_password)
            db_session.commit()
        else:
            raise UserExistsError
        user_datastore.add_role_to_user(email, 'SDX-Developer')
        db_session.commit()
    except IntegrityError as e:
        logger.error('This user already exists', error=e)
        db_session.rollback()
        raise UserExistsError
    except SQLAlchemyError as e:
        logger.error("Error creating user", error=e)
        db_session.rollback()
        raise UserCreationError


@app.before_request
def session_timeout():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=settings.CONSOLE_LOGIN_TIMEOUT)


@app.before_first_request
def before_first_request():
    init_db()
    create_initial_users()
    db_session.commit()


import console.views  # noqa
