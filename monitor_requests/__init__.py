"""Monitor Requests."""
import datetime
import re
import sys
import traceback
from requests.utils import urlparse
from .data import DataHandler
from .output import OutputHandler

__version__ = '1.2.2'


class Monitor(object):
    """Monitor class to handle patching."""

    METHODS = ('delete', 'get', 'head', 'options', 'patch', 'post', 'put')
    # Libraries which mock requests by patching it:
    MOCKING_LIBRARIES = ('requests_mock',)
    # responses and unittest.mock don't seem to show up.

    def __init__(self, domains=[], server_port=None, mock=True):
        """Initialize Monitor, hot patch requests.

        :param domains: List. Regex patterns to match against.
        :param server_port: Int. Server mode: witn monitor_requests_server
        running on the specified port.
        :param mock: Boolean. Mock requests. Default True, set to False
        when running in server mode from the test suite/session level.
        """
        self.domain_patterns = [
            re.compile(domain_pattern) for domain_pattern in domains
        ]
        self.data = DataHandler(server_port=server_port)
        # Mocking
        self.mock = mock
        if mock:
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

    def _check_mocked(self, tb_list):
        traceback = str(tb_list)
        for library in self.MOCKING_LIBRARIES:
            if '/{}/'.format(library) in traceback:
                return True
        return False

    def _log_request(self, url, response, duration):
        """Log request, store traceback/response data and update counts."""
        domain = urlparse(url).netloc
        if not self._check_domain(domain):
            return
        m_init = 'monitor_requests/__init__.py'
        tb_list = [f for f in traceback.format_stack() if m_init not in f]
        if self._check_mocked(tb_list):
            return
        self.data.log(url, domain, response, tb_list, duration)

    def refresh(self):
        """Refresh data from store (server or instance)."""
        self.logged_requests, self.analysis = self.data.retrieve()

    def report(
        self,
        urls=False,
        tracebacks=False,
        responses=False,
        debug=False,
        inspect_limit=10,
        output=sys.stdout,
        tear_down=True
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
        :param tear_down: Undo the hotpatching (True by default), delete data.
        """
        tracebacks = tracebacks or debug
        responses = responses or debug
        self.refresh()
        output_handler = OutputHandler(
            output, urls, tracebacks, responses, debug, inspect_limit,
            self.logged_requests, self.analysis
        )
        output_handler.write()
        if tear_down:
            self.stop(delete=True)

    def stop(self, delete=False):
        """Undo the hotpatching.

        :param delete: Boolean. Delete data (only with server mode).
        """
        if delete:
            self.data.delete()
        if not self.mock:
            return
        import requests
        requests.request = self.stock_requests_method
        for method in self.METHODS:
            setattr(requests, method, getattr(self, 'stock_{}'.format(method)))
