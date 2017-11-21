import re

from flask_wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length, ValidationError, Regexp


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

class StoreForm(Form):
    tx_id = StringField('tx_id', validators=[
        Length(max=36),
        Regexp('^[0-9a-f\-]{36}$|^$', message="Field can only contain hexadecimal characters (0-9a-f) and dash (-)"),
        Regexp('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|^$', message="Field must be in the form {8}-{4}-{4}-{4}-{12}"),
    ])
