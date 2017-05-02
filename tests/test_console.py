from requests import Response
import server
from time import sleep
import unittest
from unittest import mock

from testfixtures import log_capture

from console import views


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
        r = Response()
        rt = Response()
        rt.status_code = 200
        with mock.patch('requests.post') as mock_post:
            mock_post.return_value = r
            r.status_code = 200
            response = views.send_data("test", "")
            self.assertEqual(response.status_code, rt.status_code)

    def test_send_data_404(self):
        r = Response()
        with mock.patch('requests.post') as mock_post:
            mock_post.return_value = r
            r.status_code = 404
            with self.assertRaises(Exception) as context:
                views.send_data("", "")

            self.assertTrue('404 Error' in str(context.exception))
