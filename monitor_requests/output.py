"""Separate output handling."""
import sys


class OutputHandler(object):
    """Handle output."""

    def __init__(
        self,
        output=sys.stdout,
        urls=False,
        tracebacks=False,
        responses=False,
        debug=False,
        inspect_limit=None,
        logged_requests={},
        analysis={}
    ):
        """Initialize.

        :param server_port: Int. local port.
        """
        self.output = output
        self.urls = urls
        self.tracebacks = tracebacks
        self.responses = responses
        self.debug = debug
        self.inspect_limit = inspect_limit
        self.logged_requests = logged_requests
        self.analysis = analysis

    def _output_analysis(self):
        """Output the analysis.

        :param output: Stream. Output destination.
        """
        tb = 0
        for url in self.logged_requests:
            tb += len(self.logged_requests[url]['tracebacks'])
        self.output.write('___________Analysis__________\n\n')
        self.output.write('Total Requests:    {}\n'.format(
            self.analysis['total_requests']))
        self.output.write('Unique Tracebacks: {}\n'.format(tb))
        self.output.write('Time (Seconds):    {}\n'.format(
            self.analysis['duration'])
        )
        self.output.write('URL Count:         {}\n'.format(
            len(self.logged_requests.keys())))
        self.output.write('Domain Count:      {}\n'.format(
            len(self.analysis['domains'])))
        self.output.write('Domains:           {}\n'.format(
            ', '.join(sorted(list(self.analysis['domains'])))))

    def _output_responses(self, url):
        self.output.write('_______Responses______\n')
        for rs in self.logged_requests[url]['responses']:
            self.output.write('____Response____\n')
            self.output.write('<StatusCode>{}</StatusCode>\n'.format(rs[0]))
            self.output.write('<Content>{}</Content>\n'.format(rs[1]))

    def _output_tracebacks(self, url):
        self.output.write('______Tracebacks_____\n')
        for tb in self.logged_requests[url]['tracebacks']:
            if self.inspect_limit:
                tb = tb[-self.inspect_limit:]
            self.output.write('____Traceback____\n')
            self.output.write('{}\n'.format(''.join(tb).strip()))

    def _output_urls(self):
        """Output URLS.

        :param tracebacks:
        :param responses:
        :param inspect_limit:
        """
        self.output.write('__________URLS__________\n\n')
        for url in sorted(self.logged_requests.keys()):
            self.output.write('__________URL________\n')
            self.output.write('URL:      {}\n'.format(url))
            self.output.write('Requests: {}\n'.format(
                self.logged_requests[url]['count']))
            if self.tracebacks:
                self._output_tracebacks(url)
            if self.responses:
                self._output_responses(url)
            self.output.write('\n')

    def write(self):
        """Write data to output stream."""
        if self.output != sys.stdout:
            self._output_analysis()
        if self.debug or self.urls or self.tracebacks or self.responses:
            self._output_urls()
        if self.output == sys.stdout:
            self._output_analysis()
