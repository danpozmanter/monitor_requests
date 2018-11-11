"""Monitor Requests."""
import datetime
import re
import sys
import traceback
from requests.utils import urlparse

__version__ = '0.1.0'


class Monitor(object):
    """Monitor class to handle patching."""

    METHODS = ('delete', 'get', 'head', 'options', 'patch', 'post', 'put')

    def __init__(self, domain_patterns=[]):
        """Initialize Monitor, hot patch requests."""
        import requests
        self.stock_requests_method = requests.request
        self.domain_patterns = [
            re.compile(domain_pattern) for domain_pattern in domain_patterns
        ]
        self.analysis = {'total_requests': 0, 'domains': set(), 'time': 0}
        self.logged_requests = {}

        def mock_request(method, url, **kwargs):
            self._log_request(url)
            start = datetime.datetime.now()
            response = self.stock_requests_method(method, url, **kwargs)
            self.analysis['time'] += (
                datetime.datetime.now() - start).total_seconds()
            return response
        requests.request = mock_request
        for method in self.METHODS:
            stock_method_name = 'stock_{}'.format(method)
            setattr(self, stock_method_name, getattr(requests, method))
            setattr(requests, method, self._generate_request_method(
                stock_method_name))

    def _generate_request_method(self, stock_method_name):
        """Generate mock functions for http methods.

        :param stock_method_name: String.
        :return: Mocked request method
        """
        def mock_request_method(url, **kwargs):
            self._log_request(url)
            start = datetime.datetime.now()
            response = getattr(self, stock_method_name)(url, **kwargs)
            self.analysis['time'] += (
                datetime.datetime.now() - start).total_seconds()
            return response
        return mock_request_method

    def _check_domain(self, domain):
        return [
            pattern.match(domain) for pattern in self.domain_patterns
        ] != []

    def _log_request(self, url):
        """Log request, store traceback, and update request count, domain."""
        domain = urlparse(url).netloc
        if not self._check_domain(domain):
            return
        if url not in self.logged_requests:
            self.logged_requests[url] = {'count': 0, 'tracebacks': set()}
        self.logged_requests[url]['count'] += 1
        m_init = 'monitor_requests/__init__.py'
        tb_list = [f for f in traceback.format_stack() if m_init not in f]
        self.logged_requests[url]['tracebacks'].add(tuple(tb_list))
        self.analysis['total_requests'] += 1
        self.analysis['domains'].add(domain)

    def _report_analysis(self, output):
        """Output the analysis.

        :param output: Stream. Output destination.
        """
        output.write('___________Analysis__________\n')
        output.write('Total Requests: {}\n'.format(
            self.analysis['total_requests']))
        output.write('Time (Seconds): {}\n'.format(self.analysis['time']))
        output.write('URL Count:      {}\n'.format(
            len(self.logged_requests.keys())))
        output.write('Domain Count:   {}\n'.format(
            len(self.analysis['domains'])))
        output.write('Domains:        {}\n'.format(
            ', '.join(sorted(list(self.analysis['domains'])))))

    def report(
        self, tracebacks=True, inspect_limit=10, output=sys.stdout, stop=True
    ):
        """Print out the requests, general analysis, and optionally unique tracebacks.

        :param tracebacks: Boolean. Display unique tracebacks for each request.
        :param inspect_limit: Integer. How deep the stack trace should be.
        :param output: Stream. Output destination.
        :param stop: Undo the hotpatching (True by default).
        """
        if output != sys.stdout:
            self._report_analysis(output)
        output.write('__________URLS__________\n')
        for url in sorted(self.logged_requests.keys()):
            output.write('__________URL________\n')
            output.write('URL:      {}\n'.format(url))
            output.write('Requests: {}\n'.format(
                self.logged_requests[url]['count']))
            if tracebacks:
                output.write('______Tracebacks_____\n')
                for tb in self.logged_requests[url]['tracebacks']:
                    output.write('{}\n'.format(
                        ''.join(tb[-inspect_limit:]).strip()))
                    output.write('\n')
        if output == sys.stdout:
            self._report_analysis(output)
        if stop:
            self.stop()

    def stop(self):
        """Undo the hotpatching."""
        import requests
        requests.request = self.stock_requests_method
        for method in self.METHODS:
            setattr(requests, method, getattr(self, 'stock_{}'.format(method)))
