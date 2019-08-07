import re
import uuid

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, RadioField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Length, ValidationError


class NewUserForm(FlaskForm):
    
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


class StoreForm(FlaskForm):
    valid = RadioField('valid', choices=[('', 'Both'), ('valid', 'Valid'), ('invalid', 'Invalid')])
    tx_id = StringField('tx_id')
    ru_ref = StringField('ru_ref')
    survey_id = StringField('survey_id')
    datetime_earliest = DateField('datetime_earliest', format='%Y-%m-%d')
    datetime_latest = DateField('datetime_latest', format='%Y-%m-%d')

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
