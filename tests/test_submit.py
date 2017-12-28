import unittest
from unittest.mock import Mock

import server
from console.views.submit import list_surveys, send_payload, send_data


class TestConsoleSubmit(unittest.TestCase):

    def setUp(self):
        self.app = server.app.test_client()
        self.app.testing = True
        self.render_templates = False

    def test_list_surveys(self):
        response = list_surveys()
        surveys = ['023.0102.json', '023.0112.json', '023.0203.json',
                   '023.0205.json', '023.0213.json', '023.0215.json',
                   '134.0005.json', '139.0001.json', '144.0001.json']
        self.assertEqual(surveys, response)

    def test_list_surveys_get(self):
        response = self.app.get('/surveys', follow_redirects=True)
        self.assertIn(b'023.0102.json', response.data)
        self.assertIn(b'023.0112.json', response.data)
        self.assertIn(b'023.0203.json', response.data)
        self.assertIn(b'023.0205.json', response.data)

    def test_send_payload(self):
        mock_payload = Mock(send_payload, return_value='mock value')
        self.assertEqual(mock_payload(1), 'mock value')

    def test_send_data(self):
        mock_send_data = Mock(send_data, return_value='mock value')
        self.assertEqual(mock_send_data(1), 'mock value')

    # def test_submit_page_get(self):
    #     response = self.app.get('/submit', follow_redirects=True)
    #     self.assertIn('something', response.data)
    #
    # def test_submit_page_post(self):
    #     response = self.app.get('/submit', follow_redirects=True)
    #     self.assertIn('something', response.data)
    #
    # def test_validate_page_get(self):
    #     response = self.app.get('/validate', follow_redirects=True)
    #     self.assertIn('something', response.data)
    #
    # def test_validate_page_post(self):
    #     response = self.app.get('/validate', follow_redirects=True)
    #     self.assertIn('something', response.data)
