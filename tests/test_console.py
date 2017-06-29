import json
import os
import server
from time import sleep
import unittest
from unittest import mock

import requests
from testfixtures import log_capture
import testing.postgresql

from console import app
from console import views
from console.database import db, SurveyResponse
from console.helpers.exceptions import ClientError, ServiceError
from console.views import logger


class TestConsole(unittest.TestCase):

    def setUp(self):
        self.app = server.app.test_client()
        self.app.testing = True
        self.render_templates = False
        self.hb = server.HeartbeatTimer(5, server.heartbeat, server.logger)

    def tearDown(self):
        self.hb.stop()

    @log_capture()
    def test_heartbeat(self, l):
        sleep(10.0)
        l.check(('server', 'INFO', "event='Heartbeat'"))

    def test_send_data_200(self):
        r = requests.Response()
        with mock.patch('requests.post') as mock_post:
            mock_post.return_value = r
            r.status_code = 200
            response = views.send_data(logger, "", data=123)
            self.assertEqual(response.status_code, 200)

    def test_send_data_400(self):
        r = requests.Response()
        with mock.patch('requests.post') as mock_post:
            mock_post.return_value = r
            r.status_code = 400
            with self.assertRaises(ClientError):
                views.send_data(logger, "", data=123)

    def test_send_data_404(self):
        r = requests.Response()
        with mock.patch('requests.post') as mock_post:
            mock_post.return_value = r
            r.status_code = 404
            with self.assertRaises(ClientError):
                views.send_data(logger, "", data=123)

    def test_send_data_500(self):
        r = requests.Response()
        with mock.patch('requests.post') as mock_post:
            mock_post.return_value = r
            r.status_code = 500
            with self.assertRaises(ServiceError):
                views.send_data(logger, "", data=123)


Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)


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


class TestAuthentication(unittest.TestCase):

    def setUp(self):
        self.postgres = Postgresql()
        Postgresql.clear_cache()
        self.app = server.app.test_client()
        self.app.testing = True
        self.render_templates = False

    def tearDown(self):
        Postgresql.clear_cache()
        self.postgres.stop()

    def login(self, email, password):
        return self.app.post('/login',
                             data=dict(email=email, password=password))

    def test_login_success(self):
        response = self.login('admin', 'password')
        self.assertIn(b'<a href="/">/</a>', response.data)

    def test_login_invalid_password(self):
        response = self.login('admin', 'passwrd')
        self.assertIn(b'Invalid password', response.data)

    def test_login_invalid_user(self):
        response = self.login('admi', 'password')
        self.assertIn(b'Specified user does not exist', response.data)

    def test_logout(self):
        self.login('dev', 'password')
        response = self.app.get('/logout', follow_redirects=True)
        self.assertIn(b'home', response.data)

    def test_decrypt_access(self):
        self.login('dev', 'password')
        response = self.app.get('/decrypt', follow_redirects=True)
        self.assertIn(b'Data to be decrypyted', response.data)

    def test_decrypt_access_reject(self):
        response = self.app.get('/decrypt', follow_redirects=True)
        self.assertIn(b'home', response.data)

    def test_admin_access(self):
        self.login('admin', 'password')
        response = self.app.get('/admin/user', follow_redirects=True)
        self.assertIn(b'User - Admin', response.data)

    def test_admin_access_reject(self):
        response = self.app.get('/admin/user', follow_redirects=True)
        self.assertEqual(403, response.status_code)


class TestStore(unittest.TestCase):

    def setUp(self):
        self.postgres = Postgresql()
        Postgresql.clear_cache()
        self.app = server.app.test_client()
        self.app.testing = True
        self.render_templates = False
        TestAuthentication.login(self, 'dev', 'password')
        submit_test_responses()

    def tearDown(self):
        Postgresql.clear_cache()
        self.postgres.stop()

    def test_display_data(self):
        response = self.app.get('/store', follow_redirects=True)
        self.assertIn(b'f088d89d-a367-876e-f29f-ae8f1a260000', response.data)

    def test_tx_id_search_success(self):
        response = self.app.get('/store?tx_id=f088d89d-a367-876e-f29f-ae8f1a260000',
                                follow_redirects=True)
        self.assertIn(b'f088d89d-a367-876e-f29f-ae8f1a260000', response.data)

    def test_tx_id_search_fail(self):
        response = self.app.get('/store?tx_id=f088d89d-a367-876e-f29f-ae8f1a260001',
                                follow_redirects=True)
        self.assertNotIn(b'f088d89d-a367-876e-f29f-ae8f1a260000', response.data)

    def test_ru_ref_search_success(self):
        response = self.app.get('/store?ru_ref=12345678901a',
                                follow_redirects=True)
        self.assertIn(b'f088d89d-a367-876e-f29f-ae8f1a260000', response.data)

    def test_ru_ref_search_fail(self):
        response = self.app.get('/store?ru_ref=12345678901f',
                                follow_redirects=True)
        self.assertNotIn(b'f088d89d-a367-876e-f29f-ae8f1a260000', response.data)

    def test_datetime_search_success(self):
        response = self.app.get('/store?datetime_earliest=2015-01-01T01%3A01&datetime_latest=2020-01-01T01%3A01',
                                follow_redirects=True)
        self.assertIn(b'f088d89d-a367-876e-f29f-ae8f1a260000', response.data)

    def test_datetime_search_fail(self):
        response = self.app.get('/store?datetime_earliest=2020-01-01T01%3A01&datetime_latest=2020-01-01T01%3A01',
                                follow_redirects=True)
        self.assertNotIn(b'f088d89d-a367-876e-f29f-ae8f1a260000', response.data)
