import requests
import server
from time import sleep
import unittest
from unittest import mock

from testfixtures import log_capture
import testing.postgresql

from console import views
from console.helpers.exceptions import ClientError, ServiceError


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

    @log_capture()
    def test_send_data_200(self, l):
        r = requests.Response()
        rt = requests.Response()
        rt.status_code = 200
        with mock.patch('requests.post') as mock_post:
            mock_post.return_value = r
            r.status_code = 200
            response = views.send_data("", "")
            self.assertEqual(response.status_code, rt.status_code)

    def test_send_data_400(self):
        r = requests.Response()
        with mock.patch('requests.post') as mock_post:
            mock_post.return_value = r
            r.status_code = 400
            with self.assertRaises(ClientError):
                views.send_data("", "")

    def test_send_data_404(self):
        r = requests.Response()
        with mock.patch('requests.post') as mock_post:
            mock_post.return_value = r
            r.status_code = 404
            with self.assertRaises(ClientError):
                views.send_data("", "")

    def test_send_data_500(self):
        r = requests.Response()
        with mock.patch('requests.post') as mock_post:
            mock_post.return_value = r
            r.status_code = 500
            with self.assertRaises(ServiceError):
                views.send_data("", "")

    def test_send_data_no_endpoint(self):
        with self.assertRaises(requests.exceptions.ConnectionError):
            views.send_data("http://sdx-decrypt/", "")


Postgresql = testing.postgresql.PostgresqlFactory(cache_initialized_db=True)


class TestAuthentication(unittest.TestCase):

    def setUp(self):
        self.postgres = Postgresql()
        self.app = server.app.test_client()
        self.app.testing = True
        self.render_templates = False

    def tearDown(self):
        self.postgres.stop()

    def login(self, username, password):
        return self.app.post('/login',
                             data=dict(username=username, password=password))

    def test_login_success(self):
        response = self.login('admin', 'password')
        self.assertIn(b'<a href="/">/</a>', response.data)

    def test_login_invalid_password(self):
        response = self.login('admin', 'passwrd')
        self.assertIn(b'Invalid password', response.data)

    def test_login_invalid_user(self):
        response = self.login('admi', 'password')
        self.assertIn(b'Specified user does not exist', response.data)

    def test_decrypt_access(self):
        self.login('dev', 'password')
        response = self.app.get('/decrypt', follow_redirects=True)
        self.assertIn(b'Data to be decrypyted', response.data)

    def test_decrypt_access_reject(self):
        self.login('none', 'password')
        response = self.app.get('/decrypt', follow_redirects=True)
        self.assertIn(b'stuff', response.data)

    def test_admin_access(self):
        self.login('admin', 'password')
        response = self.app.get('/admin/user', follow_redirects=True)
        self.assertIn(b'User - Admin', response.data)

    def test_admin_access_reject(self):
        self.login('none', 'password')
        response = self.app.get('/admin/user', follow_redirects=True)
        self.assertEqual(403, response.status_code)
