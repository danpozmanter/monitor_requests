"""Tests."""
import sys
import tempfile
import unittest
import mock  # Python 2.x compatibility
import responses
import requests
import requests_mock
from monitor_requests import Monitor


def request_to_be_mocked_news():
    """Mockable function for news.google."""
    return requests.get('https://news.google.com')


def request_to_be_mocked_youtube():
    """Mockable function for youtube."""
    return requests.get('https://youtube.com')


@responses.activate
def mocked_with_library_resp():
    """Test responses."""
    responses.add(
        responses.GET,
        'https://news.google.com',
        body='<html>test data</html>'
    )
    r = request_to_be_mocked_news()
    return r


@requests_mock.Mocker()
def mocked_with_library_req_m(req_mock):
    """Test requests_mock."""
    req_mock.get('https://theonion.com')
    return requests.get('https://theonion.com')


def mocked_with_library_u_m():
    """Test unittest.mock."""
    with mock.patch('{}.request_to_be_mocked_youtube'.format(__name__)) as tbm:
        tbm.return_value = None
        return request_to_be_mocked_youtube()


def request_function():
    """Request call."""
    return requests.request('GET', 'http://google.com')


def get_function():
    """Get call."""
    return requests.get('http://google.com')


def get_function_fb():
    """Get call - facebook."""
    return requests.get('http://facebook.com?param=test')


def get_function_fb_graph():
    """Get call - facebook."""
    return requests.get('http://graph.facebook.com')


class MonitorTestCase(unittest.TestCase):
    """Test Case."""

    def test_monitoring(self):
        """Test monitoring analysis."""
        monitor = Monitor()
        get_function()
        monitor.stop()
        monitor.refresh()
        self.assertEqual(monitor.analysis['total_requests'], 1)
        self.assertTrue(monitor.analysis['duration'] > 0)

    def test_reporting(self):
        """Test reporting to file."""
        monitor = Monitor()
        request_function()
        t, name = tempfile.mkstemp()
        with open(name, 'w') as f:
            monitor.report(output=f)
        with open(name, 'r') as f:
            report_output = f.read()
            self.assertTrue('Total Requests' in report_output)
            self.assertTrue('Domain Count:' in report_output)

    def test_domain_filtering(self):
        """Test domain filtering actually works."""
        monitor = Monitor(domains=['google\.com'])
        get_function()
        get_function_fb()
        get_function_fb_graph()
        monitor.stop()
        monitor.refresh()
        self.assertEqual(monitor.analysis['total_requests'], 1)
        self.assertEqual(monitor.analysis['domains'], set(['google.com']))

    def test_domain_filtering_fb(self):
        """Test domain filtering actually works."""
        monitor = Monitor(domains=['facebook\.com'])
        get_function()
        get_function_fb()
        get_function_fb_graph()
        monitor.stop()
        monitor.refresh()
        self.assertEqual(monitor.analysis['total_requests'], 2)
        self.assertEqual(
            monitor.analysis['domains'],
            set(['facebook.com', 'graph.facebook.com'])
        )

    def test_mock_filtering(self):
        """Test mocked calls are filtered out."""
        monitor = Monitor()
        request_function()
        # TODO: Fix so this works with responses.
        # mocked_with_library_resp()
        mocked_with_library_u_m()
        mocked_with_library_req_m()
        monitor.stop()
        monitor.refresh()
        self.assertEqual(monitor.analysis['total_requests'], 1)
        self.assertEqual(monitor.analysis['domains'], set(['google.com']))

    def test_reporting_stdout(self):
        """Test reporting to stdout."""
        monitor = Monitor()
        request_function()
        monitor.report(output=sys.stdout)
        self.assertEqual(monitor.analysis['domains'], set(['google.com']))


if __name__ == '__main__':
    unittest.main()
