from flask.ext import security
from flask.ext.sqlalchemy import SQLAlchemy
from flask_security.forms import RegisterForm

from console import app
from console import settings


db = SQLAlchemy(app)

app.config['SQLALCHEMY_DATABASE_URI'] = settings.DB_URI
app.config['SECRET_KEY'] = settings.SECRET_KEY

role_users = db.Table('roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model, security.RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, security.UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=role_users, backref=db.backref('users', lazy='dynamic'))


user_datastore = security.SQLAlchemyUserDatastore(db, User, Role)
security = security.Security(app, user_datastore)
