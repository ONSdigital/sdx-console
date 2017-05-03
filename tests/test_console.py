import requests
import server
from time import sleep
import unittest
from unittest import mock

from testfixtures import log_capture

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
