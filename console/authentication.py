from flask_admin.contrib import sqla
import flask_security
from flask_sqlalchemy import SQLAlchemy
from flask_security.forms import RegisterForm
from wtforms.fields import PasswordField

from console import app
from console import settings


db = SQLAlchemy(app)

app.config['SQLALCHEMY_DATABASE_URI'] = settings.DB_URI
app.config['SECRET_KEY'] = settings.SECRET_KEY

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

class UserAdmin(sqla.ModelView):
    column_exclude_list = ('password',)
    form_excluded_columns = ('password',)
    column_auto_select_related = True

    def is_accessible(self):
        return flask_security.core.current_user.has_role('Admin')

    def scaffold_form(self):
        form_class = super(UserAdmin, self).scaffold_form()
        form_class.password2 = PasswordField('New Password')

        return form_class

    def on_model_change(self, form, model, is_created):
        if len(model.password2):
            model.password = flask_security.utils.encrypt_password(model.password2)

class RoleAdmin(sqla.ModelView):
    def is_accessible(self):
        return flask_security.core.current_user.has_role('Admin')


user_datastore = flask_security.SQLAlchemyUserDatastore(db, User, Role)
security = flask_security.Security(app, user_datastore)
