"""Monitor Requests."""
import datetime
import re
import sys
import traceback
import mock
from requests.utils import urlparse
from .data import DataHandler
from .output import OutputHandler

__version__ = '2.1.0'


class Monitor(object):
    """Monitor class to handle patching."""

    # Libraries which mock requests by patching it:
    # unittest.mock / mock and responses will not show up in tracebacks.
    MOCKING_LIBRARIES = ('requests_mock',)

    def __init__(self, domains=[], server_port=None, mocking=True):
        """Initialize Monitor, hot patch requests.

        :param domains: List. Regex patterns to match against.
        :param server_port: Int. Server mode: witn monitor_requests_server
        running on the specified port.
        :param mocking: Boolean. Mock requests. Default True, set to False
        when running in server mode from the test suite/session level.
        """
        self.domain_patterns = [
            re.compile(domain_pattern) for domain_pattern in domains
        ]
        self.data = DataHandler(server_port=server_port)
        # Mocking
        self.mocking = mocking
        if mocking:
            from requests.adapters import HTTPAdapter
            self.stock_send = HTTPAdapter.send
            self.send_patcher = mock.patch.object(
                HTTPAdapter,
                'send',
                side_effect=self._generate_mocked_send(),
                autospec=True
            )
            self.send_patcher.start()

    def _generate_mocked_send(self):
        """Generate mock function for http request.

        :return: Mocked send method for HTTPAdapter.
        """
        def mock_send(instance, request, *args, **kwargs):
            start = datetime.datetime.now()
            response = self.stock_send(instance, request, *args, **kwargs)
            duration = (datetime.datetime.now() - start).total_seconds()
            self._log_request(request.url, request.method, response, duration)
            return response
        return mock_send

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

    def _log_request(self, url, method, response, duration):
        """Log request, store traceback/response data and update counts."""
        domain = urlparse(url).netloc
        if not self._check_domain(domain):
            return
        m_init = 'monitor_requests/__init__.py'
        tb_list = [f for f in traceback.format_stack() if m_init not in f]
        if self._check_mocked(tb_list):
            return
        self.data.log(url, domain, method, response, tb_list, duration)

    def refresh(self):
        """Refresh data from store (server or instance)."""
        self.logged_requests, self.analysis = self.data.retrieve()

    def report(
        self,
        urls=False,
        tracebacks=False,
        responses=False,
        debug=False,
        inspect_limit=None,
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
        if not self.mocking:
            return
        self.send_patcher.stop()
