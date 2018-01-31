import json
import os
import unittest
from unittest import mock

import requests
import testing.postgresql

from console import app
from console import db
from console import logger
from console import views
from console.helpers.exceptions import ClientError, ServiceError
from console.models import SurveyResponse, create_initial_users
import console.settings
import server


Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=False)


class TestConsole(unittest.TestCase):

    def setUp(self):
        self.app = server.app.test_client()
        self.app.testing = True
        self.render_templates = False

    def test_send_data_200(self):
        r = requests.Response()
        with mock.patch('requests.post') as mock_post:
            mock_post.return_value = r
            r.status_code = 200
            response = views.submit.send_data(logger, "", data=123)
            self.assertEqual(response.status_code, 200)

    def test_send_data_400(self):
        r = requests.Response()
        with mock.patch('requests.post') as mock_post:
            mock_post.return_value = r
            r.status_code = 400
            with self.assertRaises(ClientError):
                views.submit.send_data(logger, "", data=123)

    def test_send_data_404(self):
        r = requests.Response()
        with mock.patch('requests.post') as mock_post:
            mock_post.return_value = r
            r.status_code = 404
            with self.assertRaises(ClientError):
                views.submit.send_data(logger, "", data=123)

    def test_send_data_500(self):
        r = requests.Response()
        with mock.patch('requests.post') as mock_post:
            mock_post.return_value = r
            r.status_code = 500
            with self.assertRaises(ServiceError):
                views.submit.send_data(logger, "", data=123)


def get_test_data():
    site_root = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(site_root, 'test_data', 'test_response_1.json')
    with open(json_url) as json_data:
        responses_json = [json.load(json_data)]

    return responses_json


def submit_test_responses():
    responses_json = get_test_data()
    with app.app_context():
        for response in responses_json:
            tx_id = response['tx_id']
            invalid = 'f'
            data = response
            response_data = SurveyResponse(tx_id=tx_id,
                                           invalid=invalid,
                                           data=data)
            db.session.merge(response_data)
            db.session.commit()


@testing.postgresql.skipIfNotInstalled
class TestAuthentication(unittest.TestCase):

    def setUp(self):
        self.app = server.app.test_client()
        self.app.testing = True
        self.render_templates = False
        self.postgresql = Postgresql()
        console.settings.DB_URI = self.postgresql.url()
        app.config['SQLALCHEMY_DATABASE_URI'] = console.settings.DB_URI

        with app.app_context():
            db.create_all()
            create_initial_users()
            db.session.commit()

    def tearDown(self):
        Postgresql.clear_cache()
        self.postgresql.stop()

    def login(self, email, password):
        return self.app.post('/login', data={'email': email, 'password': password})

    def test_get_login_page(self):
        response = self.app.get('/login', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Email Address', response.data)

    def test_login_success(self):
        self.login('admin', 'admin')
        response = self.app.get('/submit', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged in as: admin', response.data)

    def test_login_invalid_password(self):
        response = self.login('admin', 'passwrd')
        self.assertIn(b'Invalid password', response.data)

    def test_login_invalid_user(self):
        response = self.login('admi', 'admin')
        self.assertIn(b'Specified user does not exist', response.data)

    def test_logout(self):
        response = self.app.get('/logout', follow_redirects=True)
        self.assertIn(b'You are not logged in.', response.data)

    def test_click_store_tab_require_login(self):
        response = self.app.get('/store', follow_redirects=True)
        self.assertIn(b'Please log in to access this page.', response.data)

    def test_click_FTP_tab_require_login(self):
        response = self.app.get('/FTP', follow_redirects=True)
        self.assertIn(b'Please log in to access this page.', response.data)

    def test_click_add_user_tab_require_login(self):
        response = self.app.get('/add_user', follow_redirects=True)
        self.assertIn(b'Please log in to access this page.', response.data)

    def test_admin_access_to_add_new_user(self):
        self.login('admin', 'admin')
        response = self.app.get('/add_user', follow_redirects=True)
        self.assertIn(b'Add a new SDX developer user', response.data)

    def test_admin_access_reject_to_add_new_user(self):
        response = self.app.get('/add_user', follow_redirects=True)
        self.assertIn(b'Please log in to access this page.', response.data)


@testing.postgresql.skipIfNotInstalled
class TestStore(unittest.TestCase):

    def setUp(self):
        self.app = server.app.test_client()
        self.app.testing = True
        self.render_templates = False
        self.postgresql = Postgresql()
        console.settings.DB_URI = self.postgresql.url()
        app.config['SQLALCHEMY_DATABASE_URI'] = console.settings.DB_URI

        with app.app_context():
            db.create_all()
            create_initial_users()
            db.session.commit()

        TestAuthentication.login(self, 'admin', 'admin')
        submit_test_responses()

    def tearDown(self):
        Postgresql.clear_cache()
        self.postgresql.stop()

    def test_display_data(self):
        response = self.app.get('/store', follow_redirects=True)
        self.assertIn(b'Logged in as:', response.data)
        self.assertIn(b'Valid:', response.data)

    def test_search_all_success(self):
        response = self.app.get('/store/page/1?tx_id=&ru_ref=&survey_id=&datetime_earliest=&datetime_latest=',
                                follow_redirects=True)
        self.assertIn(b'tx_id', response.data)
        self.assertIn(b'ru_ref', response.data)
        self.assertIn(b'Reprocess', response.data)

    def test_tx_id_search_fail(self):
        response = self.app.get('/store/page/1?tx_id=a000a00a-a000-000a-a00a-aa0a0a000000',
                                follow_redirects=True)
        self.assertIn(b'tx_id: a000a00a-a000-000a-a00a-aa0a0a000000', response.data)
        self.assertNotIn(b'reprocess-tx_id', response.data)

    def test_ru_ref_search_success(self):
        response = self.app.get('/store/page/1?ru_ref=12345678901a',
                                follow_redirects=True)
        self.assertIn(b'ru_ref: 12345678901a', response.data)

    def test_ru_ref_search_fail(self):
        response = self.app.get('/store/page/1?ru_ref=12345678901f',
                                follow_redirects=True)
        self.assertIn(b'ru_ref: 12345678901f', response.data)
        self.assertNotIn(b'reprocess-tx_id', response.data)

    def test_datetime_search_success(self):
        response = self.app.get('/store/page/1?datetime_earliest=2015-01-01&datetime_latest=2020-01-01',
                                follow_redirects=True)
        self.assertIn(b'reprocess-tx_id', response.data)

    def test_datetime_search_fail(self):
        response = self.app.get('/store/page/1?datetime_earliest=2020-01-01&datetime_latest=2020-01-01',
                                follow_redirects=True)
        self.assertIn(b'datetime_earliest: 2020-01-01', response.data)
        self.assertIn(b'datetime_latest: 2020-01-01', response.data)
        self.assertNotIn(b'reprocess-tx_id', response.data)
