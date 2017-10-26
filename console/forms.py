import re

from flask_wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length, ValidationError


class NewUserForm(Form):
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired(), Length(min=8)])

    @staticmethod
    def validate_password(form, field):
        data = field.data

        if not re.findall('.*[a-z].*', data):
            msg = '{} should have atleast one lowercase character'.format(field.name)
            raise ValidationError(msg)

        if not re.findall('.*[A-Z].*', data):
            msg = '{} should have atleast one uppercase character'.format(field.name)
            raise ValidationError(msg)

        if not re.findall('.*[0-9].*', data):
            msg = '{} should have atleast one number'.format(field.name)
            raise ValidationError(msg)
