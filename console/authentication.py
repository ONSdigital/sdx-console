from datetime import timedelta
import logging

from flask import session
from flask_admin import Admin
from flask_admin.contrib import sqla
import flask_security
from structlog import wrap_logger
from wtforms.fields import HiddenField, PasswordField

from console import app
from console import settings
from console.database import db, user_datastore, User, Role


logger = wrap_logger(logging.getLogger(__name__))


def auth_config():
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.DB_URI
    app.config['SECURITY_PASSWORD_HASH'] = settings.SECURITY_PASSWORD_HASH
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['SECURITY_PASSWORD_SALT'] = settings.SECURITY_PASSWORD_SALT
    app.config['WTF_CSRF_ENABLED'] = False


auth_config()


@app.before_request
def session_timeout():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=settings.CONSOLE_LOGIN_TIMEOUT)


class UserAdmin(sqla.ModelView):
    column_exclude_list = ('password',)
    form_excluded_columns = ('password',)
    column_auto_select_related = True

    @staticmethod
    def is_accessible():
        return flask_security.core.current_user.has_role('Admin')

    def scaffold_form(self):
        form_class = super(UserAdmin, self).scaffold_form()
        form_class.password2 = PasswordField('New Password')

        return form_class

    @staticmethod
    def on_model_change(form, model, is_created):
        if len(model.password2):
            model.password = flask_security.utils.encrypt_password(model.password2)


class RoleAdmin(sqla.ModelView):
    @staticmethod
    def is_accessible():
        return flask_security.core.current_user.has_role('Admin')


class LoginFormExtended(flask_security.forms.LoginForm):
    # Overriding LoginForm to remove remember me button
    remember = HiddenField('')


security = flask_security.Security(app, user_datastore, login_form=LoginFormExtended)

admin = Admin(app, template_mode='bootstrap3')
admin.add_view(UserAdmin(User, db.session))
admin.add_view(RoleAdmin(Role, db.session))
