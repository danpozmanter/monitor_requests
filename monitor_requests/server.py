"""Server."""
import argparse
import json
import tornado.ioloop
import tornado.web
from tornado import gen
from tornado.escape import json_decode


class MonitorEncoder(json.JSONEncoder):
    """Basic encoder - override set but possibly more."""

    def default(self, o):
        """Override."""
        if isinstance(o, set):
            return list(o)
        return json.JSONEncoder.default(self, o)


class MainHandler(tornado.web.RequestHandler):
    """Handler."""

    def __init__(self, *args, **kwargs):
        """Override."""
        self.delete()
        return super(MainHandler, self).__init__(*args, **kwargs)

    @gen.coroutine
    def delete(self):
        """Reset stored data."""
        self.logged_requests = {}
        self.analysis = {'total_requests': 0, 'domains': set(), 'time': 0}

    @gen.coroutine
    def get(self):
        """Retrieve stored data."""
        self.write(json.dumps({
            'logged_requests': self.logged_requests,
            'analysis': self.analysis
        }, cls=MonitorEncoder))

    @gen.coroutine
    def post(self):
        """Add a new logged request."""
        request_data = json_decode(self.request.body)
        url = request_data.get('url')
        response_content = request_data.get('response_content')
        response_status_code = request_data.get('response_status_code')
        domain = request_data.get('domain')
        tb_list = request_data.get('traceback_list')
        if url not in self.logged_requests:
            self.logged_requests[url] = {
                'count': 0,
                'tracebacks': set(),
                'responses': set()
            }
        self.logged_requests[url]['count'] += 1
        self.logged_requests[url]['tracebacks'].add(tuple(tb_list))
        self.logged_requests[url]['responses'].add((
            response_status_code,
            response_content,
        ))
        self.analysis['time'] += request_data.get('duration')
        self.analysis['total_requests'] += 1
        self.analysis['domains'].add(domain)


def make_app():
    """Tornado make app."""
    return tornado.web.Application([
        (r'/', MainHandler),
    ])


def run_server():
    """Run server with command line arguments."""
    parser = argparse.ArgumentParser(description='Set port.')
    parser.add_argument('-p', '--port', help='Port', required=False)
    args = vars(parser.parse_args())
    app = make_app()
    port = args.get('port') or 9001
    app.listen(port)
    print('Listening on {}'.format(port))
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    run_server()
