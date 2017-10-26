from flask_admin.contrib import sqla
import flask_security
from flask_security import RoleMixin
from flask_security.forms import PasswordField
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer
from sqlalchemy import String, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.expression import func

from console.database import Base


class RolesUsers(Base):
    __tablename__ = 'roles_users'
    id = Column(Integer(), primary_key=True)
    user_id = Column('user_id', Integer(), ForeignKey('flaskuser.id'))
    role_id = Column('role_id', Integer(), ForeignKey('role.id'))


class Role(Base, RoleMixin):
    __tablename__ = 'role'
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))


class RoleAdmin(sqla.ModelView):
    @staticmethod
    def is_accessible():
        return flask_security.core.current_user.has_role('Admin')


class FlaskUser(Base, flask_security.UserMixin):
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


class SurveyResponse(Base):
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
