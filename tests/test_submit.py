import unittest

import server
from console.views.submit import list_surveys


class TestConsoleSubmit(unittest.TestCase):

    def setUp(self):
        self.app = server.app.test_client()
        self.app.testing = True
        self.render_templates = False

    def test_list_surveys(self):
        response = list_surveys()
        surveys = [
            "009.0167.json",
            "009.0201.json",
            "009.0255.json",
            "023.0102.json",
            "023.0112.json",
            "023.0203.json",
            "023.0205.json",
            "023.0213.json",
            "023.0215.json",
            "134.0005.json",
            "139.0001.json",
            "144.0001.json",
            "lms.1.json",
        ]

        self.assertEqual(surveys, response)

    def test_list_surveys_get(self):
        response = self.app.get("/surveys", follow_redirects=True)
        self.assertIn(b"023.0102.json", response.data)
        self.assertIn(b"023.0112.json", response.data)
        self.assertIn(b"023.0203.json", response.data)
        self.assertIn(b"023.0205.json", response.data)
