"""Tests."""
import sys
import tempfile
import unittest
import requests
from monitor_requests import Monitor


def request_function():
    """Request call."""
    return requests.request('GET', 'http://google.com')


def get_function():
    """Get call."""
    return requests.get('http://google.com')


class MonitorTestCase(unittest.TestCase):
    """Test Case."""

    def test_monitoring(self):
        """Test monitoring analysis."""
        monitor = Monitor()
        get_function()
        monitor.stop()
        self.assertEqual(monitor.analysis['total_requests'], 1)
        self.assertTrue(monitor.analysis['time'] > 0)

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

    def test_reporting_stdout(self):
        """Test reporting to stdout."""
        monitor = Monitor()
        request_function()
        monitor.report(output=sys.stdout)
        self.assertEqual(monitor.analysis['domains'], set(['google.com']))


if __name__ == '__main__':
    unittest.main()
