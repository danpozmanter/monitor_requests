"""Monitor Requests."""
import datetime
import re
import sys
import traceback
from requests.utils import urlparse

__version__ = '0.3.1'


class Monitor(object):
    """Monitor class to handle patching."""

    METHODS = ('delete', 'get', 'head', 'options', 'patch', 'post', 'put')

    def __init__(self, domains=[]):
        """Initialize Monitor, hot patch requests.

        :param domains:: List of regex patterns to match against.
        """
        self.domain_patterns = [
            re.compile(domain_pattern) for domain_pattern in domains
        ]
        self.analysis = {'total_requests': 0, 'domains': set(), 'time': 0}
        self.logged_requests = {}
        # Mocking
        import requests
        self.stock_requests_method = requests.request
        requests.request = self._generate_mocked_request()
        for method in self.METHODS:
            stock_method_name = 'stock_{}'.format(method)
            setattr(self, stock_method_name, getattr(requests, method))
            setattr(requests, method, self._generate_mocked_request_method(
                stock_method_name))

    def _generate_mocked_request(self):
        """Generate mock functions for http request.

        :return: Mocked request.
        """
        def mock_request(method, url, **kwargs):
            start = datetime.datetime.now()
            response = self.stock_requests_method(method, url, **kwargs)
            duration = (datetime.datetime.now() - start).total_seconds()
            self._log_request(url, response, duration)
            return response
        return mock_request

    def _generate_mocked_request_method(self, stock_method_name):
        """Generate mock functions for http methods.

        :param stock_method_name: String.
        :return: Mocked request method
        """
        def mock_request_method(url, **kwargs):
            start = datetime.datetime.now()
            response = getattr(self, stock_method_name)(url, **kwargs)
            duration = (datetime.datetime.now() - start).total_seconds()
            self._log_request(url, response, duration)
            return response
        return mock_request_method

    def _check_domain(self, domain):
        if not self.domain_patterns:
            return True
        matched = False
        for pattern in self.domain_patterns:
            if pattern.search(domain):
                matched = True
        return matched

    def _log_request(self, url, response, duration):
        """Log request, store traceback/response data and update counts."""
        domain = urlparse(url).netloc
        if not self._check_domain(domain):
            return
        if url not in self.logged_requests:
            self.logged_requests[url] = {
                'count': 0,
                'tracebacks': set(),
                'responses': set()
            }
        self.logged_requests[url]['count'] += 1
        m_init = 'monitor_requests/__init__.py'
        tb_list = [f for f in traceback.format_stack() if m_init not in f]
        self.logged_requests[url]['tracebacks'].add(tuple(tb_list))
        self.logged_requests[url]['responses'].add((
            response.status_code,
            response.content,
        ))
        self.analysis['time'] += duration
        self.analysis['total_requests'] += 1
        self.analysis['domains'].add(domain)

    def _output_analysis(self, output):
        """Output the analysis.

        :param output: Stream. Output destination.
        """
        output.write('___________Analysis__________\n\n')
        output.write('Total Requests: {}\n'.format(
            self.analysis['total_requests']))
        output.write('Time (Seconds): {}\n'.format(self.analysis['time']))
        output.write('URL Count:      {}\n'.format(
            len(self.logged_requests.keys())))
        output.write('Domain Count:   {}\n'.format(
            len(self.analysis['domains'])))
        output.write('Domains:        {}\n'.format(
            ', '.join(sorted(list(self.analysis['domains'])))))

    def _output_responses(self, output, url):
        output.write('_______Responses______\n')
        for rs in self.logged_requests[url]['responses']:
            output.write('<StatusCode>{}</StatusCode>\n'.format(rs[0]))
            output.write('<Content>{}</Content>\n'.format(rs[1]))

    def _output_tracebacks(self, output, url, inspect_limit):
        output.write('______Tracebacks_____\n')
        for tb in self.logged_requests[url]['tracebacks']:
            output.write('{}\n'.format(
                ''.join(tb[-inspect_limit:]).strip()))

    def _output_urls(self, output, tracebacks, responses, inspect_limit):
        """Output URLS.

        :param tracebacks:
        :param responses:
        :param inspect_limit:
        """
        output.write('__________URLS__________\n\n')
        for url in sorted(self.logged_requests.keys()):
            output.write('__________URL________\n')
            output.write('URL:      {}\n'.format(url))
            output.write('Requests: {}\n'.format(
                self.logged_requests[url]['count']))
            if tracebacks:
                self._output_tracebacks(output, url, inspect_limit)
            if responses:
                self._output_responses(output, url)
            output.write('\n')

    def report(
        self,
        urls=False,
        tracebacks=False,
        responses=False,
        debug=False,
        inspect_limit=10,
        output=sys.stdout,
        stop=True
    ):
        """Print out the requests, general analysis, and optionally unique tracebacks.

        If debug is True, show urls, tracebacks, and responses.
        If tracebacks or responses are set to True, urls will be output.
        :param urls: Boolean. Display unique urls requested.
        :param tracebacks: Boolean. Display unique tracebacks per url.
        :param responses: Boolean. Display response/request info per url.
        :param debug: Boolean. Convenience to display tracebacks and responses.
        :param inspect_limit: Integer. How deep the stack trace should be.
        :param output: Stream. Output destination.
        :param stop: Undo the hotpatching (True by default).
        """
        tracebacks = tracebacks or debug
        responses = responses or debug
        if output != sys.stdout:
            self._output_analysis(output)
        if debug or urls or tracebacks or responses:
            self._output_urls(output, tracebacks, responses, inspect_limit)
        if output == sys.stdout:
            self._output_analysis(output)
        if stop:
            self.stop()

    def stop(self):
        """Undo the hotpatching."""
        import requests
        requests.request = self.stock_requests_method
        for method in self.METHODS:
            setattr(requests, method, getattr(self, 'stock_{}'.format(method)))
