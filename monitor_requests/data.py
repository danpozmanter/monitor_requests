"""Data handling by server or instance."""
import json
import urllib3


class DataHandler(object):
    """Handle data."""

    def __init__(self, server_port=None):
        """Initialize.

        :param server_port: Int. local port.
        """
        self.server_port = server_port
        self.logged_requests = {}
        self.analysis = {
            'total_requests': 0, 'domains': set(), 'duration': 0
        }

    def _delete(self):
        http = urllib3.PoolManager()
        resp = http.request(
            'DELETE',
            'http://localhost:{}/'.format(self.server_port)
        )
        if resp.status != 200:
            raise Exception('Monitor Requests server error: {}.'.format(
                resp.status
            ))

    def _get(self):
        http = urllib3.PoolManager()
        resp = http.request(
            'GET',
            'http://localhost:{}/'.format(self.server_port)
        )
        if resp.status != 200:
            raise Exception('Monitor Requests server error: {}.'.format(
                resp.status
            ))
        return json.loads(resp.data)

    def _post(self, data):
        http = urllib3.PoolManager()
        resp = http.request(
            'POST',
            'http://localhost:{}/'.format(self.server_port),
            headers={'Content-Type': 'application/json'},
            body=json.dumps(data)
        )
        if resp.status != 200:
            raise Exception('Monitor Requests server error: {}.'.format(
                resp.status
            ))

    def delete(self):
        """Delete data from server if applicable."""
        if not self.server_port:
            return
        self._delete()

    def log(self, url, domain, method, response, tb_list, duration):
        """Log request, store traceback/response data and update counts."""
        if self.server_port:
            self._post({
                'url': url,
                'domain': domain,
                'method': method,
                'response_content': str(response.content),
                'response_status_code': response.status_code,
                'duration': duration,
                'traceback_list': tb_list
            })
        else:
            if url not in self.logged_requests:
                self.logged_requests[url] = {
                    'count': 0,
                    'methods': set(),
                    'tracebacks': set(),
                    'responses': set()
                }
            self.logged_requests[url]['count'] += 1
            self.logged_requests[url]['methods'].add(method)
            self.logged_requests[url]['tracebacks'].add(tuple(tb_list))
            self.logged_requests[url]['responses'].add((
                response.status_code,
                response.content,
            ))
            self.analysis['duration'] += duration
            self.analysis['total_requests'] += 1
            self.analysis['domains'].add(domain)

    def retrieve(self):
        """Retrieve data from server or instance."""
        if not self.server_port:
            return self.logged_requests, self.analysis
        data = self._get()
        return data.get('logged_requests'), data.get('analysis')
