from server import app
import unittest

from testfixtures import log_capture
from time import sleep


class TestConsole(unittest.TestCase):

    def setUp(self):
        # creates a test client
        self.app = app.test_client()
        # propagate the exceptions to the test client
        self.app.testing = True

    @log_capture()
    def test_heartbeat(self, l):
        sleep(30.0)
        l.check(
            ('console.views', 'INFO', "event='Heartbeat 1'")
        )
