import re
import uuid

from flask_wtf import Form
from wtforms import StringField, PasswordField, RadioField
from wtforms.fields.html5 import DateTimeLocalField
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


class StoreForm(Form):
    valid = RadioField('valid', choices=[('', 'Both'), ('valid', 'Valid'), ('invalid', 'Invalid')])
    tx_id = StringField('tx_id')
    ru_ref = StringField('ru_ref')
    survey_id = StringField('survey_id')
    datetime_earliest = DateTimeLocalField('datetime_earliest', format='%Y-%m-%dT%H:%M')
    datetime_latest = DateTimeLocalField('datetime_latest', format='%Y-%m-%dT%H:%M')

    @staticmethod
    def validate_tx_id(form, field):
        data = field.data

        # First if handles the empty string.  Using the UUID() and Optional() rules
        # were attempted but we couldn't get it to work so this is a workaround.
        if data:
            try:
                uuid.UUID(field.data)
            except ValueError:
                raise ValidationError('Invalid UUID.')
