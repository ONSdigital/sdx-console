import pytest
from wtforms.validators import ValidationError

from console import app
from console.forms import NewUserForm, StoreForm


class TestNewUserForm:

    @staticmethod
    def test_validate_password_no_lowercase():
        """Tests that a ValidationError is thrown when a password has no lower case characters in it"""
        with app.app_context():
            form = NewUserForm()
            form.email.data = "person@email.com"
            form.password.data = "ABCD1234"
            with pytest.raises(ValidationError) as excinfo:
                form.validate_password(form, form.password)
            assert 'password should have atleast one lowercase character' in str(excinfo.value)

    @staticmethod
    def test_validate_password_no_uppercase():
        """Tests that a ValidationError is thrown when a password has no upper case characters in it"""
        with app.app_context():
            form = NewUserForm()
            form.email.data = "person@email.com"
            form.password.data = "abcd1234"
            with pytest.raises(ValidationError) as excinfo:
                form.validate_password(form, form.password)
            assert 'password should have atleast one uppercase character' in str(excinfo.value)

    @staticmethod
    def test_validate_password_no_number():
        """Tests that a ValidationError is thrown when a password has no numbers in it"""
        with app.app_context():
            form = NewUserForm()
            form.email.data = "person@email.com"
            form.password.data = "ABCDabcd"
            with pytest.raises(ValidationError) as excinfo:
                form.validate_password(form, form.password)
            assert 'password should have atleast one number' in str(excinfo.value)


class TestStoreForm:

    @staticmethod
    def test_validate_tx_id_with_invalid_tx_id():
        """Tests that a ValidationError is thrown when tx_id isn't a valid UUID"""
        with app.app_context():
            form = StoreForm()
            form.tx_id.data = "abc"
            with pytest.raises(ValidationError) as excinfo:
                form.validate_tx_id(form, form.tx_id)
            assert 'Invalid UUID.' in str(excinfo.value)
