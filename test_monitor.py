import sys
import tempfile
import unittest
import requests
from monitor_requests import Monitor

def request_function():
    return requests.request('GET', 'http://google.com')

def get_function():
    return requests.get('http://google.com')

class MonitorTestCase(unittest.TestCase):

    def test_monitoring(self):
        monitor = Monitor()
        result = get_function()
        monitor.stop()
        self.assertEqual(monitor.analysis['total_requests'], 1)
        self.assertTrue(monitor.analysis['time'] > 0)

    def test_reporting(self):
        monitor = Monitor()
        result = request_function()
        monitor.stop()
        t, name = tempfile.mkstemp()
        with open(name, 'w') as f:
            monitor.report(output=f)
        with open(name, 'r') as f:
            report_output = f.read()
            self.assertTrue('Total Requests' in report_output)
            self.assertTrue('Domain Count:' in report_output)

    def test_reporting_stdout(self):
        monitor = Monitor()
        result = request_function()
        monitor.stop()
        monitor.report(output=sys.stdout)
        self.assertEqual(monitor.analysis['domains'], set(['google.com',]))

if __name__ == '__main__':
    unittest.main()