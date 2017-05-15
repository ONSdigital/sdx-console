from datetime import timedelta
import logging

from flask import session
from flask_admin import Admin
from flask_admin.contrib import sqla
import flask_security
from flask_sqlalchemy import SQLAlchemy
from structlog import wrap_logger
from wtforms.fields import HiddenField, PasswordField

from console import app
from console import settings

logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
logger = wrap_logger(logging.getLogger(__name__))

db = SQLAlchemy(app)


def auth_config():
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.DB_URI
    app.config['SECURITY_PASSWORD_HASH'] = settings.SECURITY_PASSWORD_HASH
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['SECURITY_PASSWORD_SALT'] = settings.SECURITY_PASSWORD_SALT
    app.config['WTF_CSRF_ENABLED'] = False

auth_config()

role_users = db.Table('roles_users',
                      db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                      db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model, flask_security.RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)


class User(db.Model, flask_security.UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=role_users, backref=db.backref('users', lazy='dynamic'))

    def __str__(self):
        return self.email

    def __hash__(self):
        return hash(self.email)


def create_tables():
    logger.info("Creaing tables")
    db.create_all()


def create_initial_users():
    user_datastore.find_or_create_role(name='Admin', description='Edit Roles/Users')
    user_datastore.find_or_create_role(name='SDX-Developer', description='Usual console functionality')

    encrypted_password = flask_security.utils.encrypt_password('password')

    if not user_datastore.get_user('admin'):
        user_datastore.create_user(email='admin', password=encrypted_password)
    if not user_datastore.get_user('dev'):
        user_datastore.create_user(email='dev', password=encrypted_password)
    if not user_datastore.get_user('none'):
        user_datastore.create_user(email='none', password=encrypted_password)
    db.session.commit()

    user_datastore.add_role_to_user('admin', 'Admin')
    user_datastore.add_role_to_user('dev', 'SDX-Developer')
    db.session.commit()


@app.before_first_request
def before_first_request():
    create_tables()
    create_initial_users()


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
    def is_accessible(self):
        return flask_security.core.current_user.has_role('Admin')


class LoginFormExtended(flask_security.forms.LoginForm):
    # Overriding LoginForm to remove remember me button
    remember = HiddenField('')


user_datastore = flask_security.SQLAlchemyUserDatastore(db, User, Role)
security = flask_security.Security(app, user_datastore, login_form=LoginFormExtended)

admin = Admin(app, template_mode='bootstrap3')
admin.add_view(UserAdmin(User, db.session))
admin.add_view(RoleAdmin(Role, db.session))
