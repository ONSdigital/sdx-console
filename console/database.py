import logging

import flask_security
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import JSONB, UUID
from structlog import wrap_logger

from console import app
from console import settings


logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
logger = wrap_logger(logging.getLogger(__name__))

db = SQLAlchemy(app)

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


class SurveyResponse(db.Model):
    __tablename__ = 'responses'
    tx_id = db.Column("tx_id",
                      UUID,
                      primary_key=True)

    ts = db.Column("ts",
                   db.TIMESTAMP(timezone=True),
                   server_default=db.func.now(),
                   onupdate=db.func.now())

    invalid = db.Column("invalid",
                        db.Boolean,
                        default=False)

    data = db.Column("data", JSONB)

    def __init__(self, tx_id, invalid, data):
        self.tx_id = tx_id
        self.invalid = invalid
        self.data = data

    def __repr__(self):
        return '<SurveyResponse {}>'.format(self.tx_id)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


def create_tables():
    logger.info("Creating tables")
    try:
        db.create_all()
    except SQLAlchemyError:
        logger.error('SQLAlchemyError')


user_datastore = flask_security.SQLAlchemyUserDatastore(db, User, Role)


def create_initial_users():
    try:
        user_datastore.find_or_create_role(name='Admin', description='Edit Roles/Users')
        user_datastore.find_or_create_role(name='SDX-Developer', description='Usual console functionality')
    except SQLAlchemyError:
        logger.error('SQLAlchemyError')

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
