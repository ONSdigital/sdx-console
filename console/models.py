import flask_security
import logging
from flask_admin import Admin
from flask_admin.contrib import sqla
from flask_security import RoleMixin
from flask_security import SQLAlchemySessionUserDatastore
from flask_security.forms import PasswordField
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer
from sqlalchemy import String, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.expression import func
from structlog import wrap_logger
from wtforms import HiddenField

from console import db, app, settings
from console.helpers.exceptions import UserExistsError, UserCreationError

logger = wrap_logger(logging.getLogger(__name__))


class RolesUsers(db.Model):
    __tablename__ = 'roles_users'
    id = Column(Integer(), primary_key=True)
    user_id = Column('user_id', Integer(), ForeignKey('flaskuser.id'))
    role_id = Column('role_id', Integer(), ForeignKey('role.id'))


class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))


class RoleAdmin(sqla.ModelView):
    @staticmethod
    def is_accessible():
        return flask_security.core.current_user.has_role('Admin')


class FlaskUser(db.Model, flask_security.UserMixin):
    __tablename__ = 'flaskuser'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    password = Column(String(255))
    active = Column(Boolean())
    confirmed_at = Column(DateTime())
    roles = relationship('Role', secondary='roles_users',
                         backref=backref('flaskuser', lazy='dynamic'))

    def __str__(self):
        return self.email

    def __hash__(self):
        return hash(self.email)


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


class SurveyResponse(db.Model):
    __tablename__ = 'responses'
    tx_id = Column("tx_id",
                   UUID,
                   primary_key=True)

    ts = Column("ts",
                TIMESTAMP(timezone=True),
                server_default=func.now(),
                onupdate=func.now())

    invalid = Column("invalid",
                     Boolean,
                     default=False)

    data = Column("data", JSONB)

    def __init__(self, tx_id, invalid, data):
        self.tx_id = tx_id
        self.invalid = invalid
        self.data = data

    def __repr__(self):
        return '<SurveyResponse {}>'.format(self.tx_id)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class LoginFormExtended(flask_security.forms.LoginForm):
    # Overriding LoginForm to remove remember me button
    remember = HiddenField('')
    
    
user_datastore = SQLAlchemySessionUserDatastore(db.session, FlaskUser, Role)
security = flask_security.Security(app, user_datastore, login_form=LoginFormExtended)

admin = Admin(app, template_mode='bootstrap3')
admin.add_view(UserAdmin(FlaskUser, db.session))
admin.add_view(RoleAdmin(Role, db.session))


def create_initial_users():
    logger.info("Creating initial roles and users")
    try:
        user_datastore.find_or_create_role(name='Admin', description='Edit Roles/Users')
        db.session.commit()

        user_datastore.find_or_create_role(name='SDX-Developer',
                                           description='Usual console functionality')
        encrypted_password = flask_security.utils.hash_password(
            settings.CONSOLE_INITIAL_ADMIN_PASSWORD)
        db.session.commit()

        if not user_datastore.get_user('admin'):
            user_datastore.create_user(email='admin', password=encrypted_password)
            db.session.commit()

        user_datastore.add_role_to_user('admin', 'Admin')
        db.session.commit()
    except IntegrityError as e:
        logger.error('A user/role already exists', error=e)
        db.session.rollback()
    except SQLAlchemyError as e:
        logger.error("Error creating initial users and roles", error=e)
        db.session.rollback()


def create_dev_user(email, password):
    logger.info("Creating SDX-Developer %s" % email)
    try:
        encrypted_password = flask_security.utils.hash_password(password)
        if not user_datastore.get_user(email):
            user_datastore.create_user(email=email, password=encrypted_password)
            db.session.commit()
        else:
            raise UserExistsError
        user_datastore.add_role_to_user(email, 'SDX-Developer')
        db.session.commit()
    except IntegrityError as e:
        logger.error('This user already exists', error=e)
        db.session.rollback()
        raise UserExistsError
    except SQLAlchemyError as e:
        logger.error("Error creating user", error=e)
        db.session.rollback()
        raise UserCreationError


@app.before_first_request
def before_first_request():
    if settings.DEVELOPMENT_MODE:
        create_initial_users()
        db.session.commit()
