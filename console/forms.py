from flask_wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired


class NewUserForm(Form):
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])