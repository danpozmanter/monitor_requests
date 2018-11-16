"""Simple server tests."""
# coding=utf-8
import json
from tornado.testing import AsyncHTTPTestCase
from monitor_requests.server import make_app


class ApiTestCase(AsyncHTTPTestCase):
    """Test case."""

    def get_app(self):
        """Override get_app."""
        self.app = make_app()
        return self.app

    def test_get(self):
        """Test basic get."""
        response = self.fetch('/', method='GET')
        self.assertEqual(response.code, 200)

    def test_post(self):
        """Test basic post."""
        response = self.fetch(
            '/',
            body=json.dumps({
                'url': 'http://google.com/?whatever',
                'method': 'GET',
                'domain': 'google.com',
                'response_content': '<html>example</html>',
                'response_status_code': 200,
                'duration': 2.1,
                'traceback_list': ['a', 'b']
            }),
            method='POST'
        )
        self.assertEqual(response.code, 200)

    def test_post_and_retrieve(self):
        """Test basic post and get."""
        response = self.fetch(
            '/',
            body=json.dumps({
                'url': 'http://google.com/?whatever',
                'method': 'GET',
                'domain': 'google.com',
                'response_content': u'<html>exampleθ</html>',
                'response_status_code': 200,
                'duration': 2.1,
                'traceback_list': ['a', 'b']
            }),
            method='POST'
        )
        self.assertEqual(response.code, 200)
        response = self.fetch('/', method='GET')
        self.assertEqual(response.code, 200)
