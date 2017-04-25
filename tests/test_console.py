import server
import unittest
from time import sleep

from testfixtures import log_capture


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
