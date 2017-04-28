from requests import Response
import server
# from time import sleep
import unittest
from unittest import mock

# from testfixtures import log_capture


class TestConsole(unittest.TestCase):

    def setUp(self):
        self.app = server.app.test_client()
        self.app.testing = True
        self.hb = server.HeartbeatTimer(5, server.heartbeat, server.logger)

    def tearDown(self):
        self.hb.stop()

    @log_capture()
    def test_heartbeat(self, l):
        sleep(10.0)
        l.check(
            ('server', 'INFO', "event='Heartbeat'")
        )

    def test_decrypt_page(self):
        r = Response()
        with mock.patch('console.views.send_data') as send_mock:
            send_mock.return_value = r
            r.headers = "{'content-type' : 'application/json'}"
            r.data = "{'test_json': 'test'}"
            self.app.post('/decrypt', headers={'content-type': 'application/json'}, data={'EncryptedData': 'Test'})
            self.assert_template_used('decrypt.html')
