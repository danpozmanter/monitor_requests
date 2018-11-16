"""Basic server for Monitor Requests.

Run with:
monitor_requests_server
Optional arguments:
-p 9001
--port=9001
"""
import argparse
import json
import tornado.ioloop
import tornado.web
import sqlite3
from tornado import gen
from tornado.escape import json_decode


def init_db():
    """Initialize the temp db."""
    conn = sqlite3.connect(':memory:')
    conn.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')
    c = conn.cursor()
    c.execute('CREATE TABLE logged_requests (url text, duration real)')
    c.execute('CREATE TABLE methods (url text, method text)')
    c.execute('CREATE TABLE tracebacks (url text, traceback text)')
    c.execute(
        'CREATE TABLE responses (url text, status_code integer, content text)'
    )
    c.execute('CREATE TABLE domains (domain text)')
    conn.commit()
    c.close()
    return conn


class MonitorEncoder(json.JSONEncoder):
    """Basic encoder - override set but possibly more."""

    def default(self, o):
        """Override."""
        if isinstance(o, set):
            return list(o)
        return json.JSONEncoder.default(self, o)


class MainHandler(tornado.web.RequestHandler):
    """Handler."""

    def initialize(self, conn):
        """Initialize handler with connection."""
        self.conn = conn

    @gen.coroutine
    def delete(self):
        """Reset stored data."""
        c = self.conn.cursor()
        c.execute('DELETE FROM logged_requests')
        c.execute('DELETE FROM methods')
        c.execute('DELETE FROM tracebacks')
        c.execute('DELETE FROM responses')
        c.execute('DELETE FROM domains')
        self.conn.commit()
        c.close()

    @gen.coroutine
    def get(self):
        """Retrieve stored data."""
        logged_requests = {}
        analysis = {
            'total_requests': 0,
            'domains': set(),
            'duration': 0
        }
        c = self.conn.cursor()
        c.execute('SELECT * from logged_requests')
        for row in c.fetchall():
            url, duration = row
            if url not in logged_requests:
                logged_requests[url] = {
                    'count': 0,
                    'methods': set(),
                    'tracebacks': set(),
                    'responses': set()
                }
            logged_requests[url]['count'] += 1
            analysis['total_requests'] += 1
            analysis['duration'] += duration
        c.execute('SELECT * from domains')
        for row in c.fetchall():
            analysis['domains'].add(row[0])
        c.execute('SELECT * from methods')
        for row in c.fetchall():
            url, method = row
            logged_requests[url]['methods'].add(method)
        for row in c.fetchall():
            url, traceback = row
            logged_requests[url]['tracebacks'].add(
                tuple(json.loads(traceback))
            )
        c.execute('SELECT * from responses')
        for row in c.fetchall():
            url, status_code, content = row
            logged_requests[url]['responses'].add((status_code, content))
        c.close()
        self.write(json.dumps({
            'logged_requests': logged_requests,
            'analysis': analysis
        }, cls=MonitorEncoder))

    @gen.coroutine
    def post(self):
        """Add a new logged request."""
        request_data = json_decode(self.request.body)
        url = request_data.get('url')
        c = self.conn.cursor()
        c.execute(
            'INSERT INTO logged_requests (url, duration) VALUES (?,?)',
            (url, request_data.get('duration'))
        )
        c.execute(
            'INSERT INTO methods (url, method) VALUES (?,?)',
            (url, request_data.get('method'))
        )
        c.execute(
            'INSERT INTO tracebacks (url, traceback) VALUES (?,?)',
            (url, json.dumps(request_data.get('traceback_list')))
        )
        c.execute(
            'INSERT INTO responses (url, status_code, content) VALUES (?,?,?)',
            (
                url,
                request_data.get('response_content'),
                request_data.get('response_status_code')
            )
        )
        c.execute(
            'INSERT INTO domains (domain) VALUES (?)',
            (request_data.get('domain'),)
        )
        self.conn.commit()
        c.close()


def make_app():
    """Tornado make app."""
    return tornado.web.Application([
        (r'/', MainHandler, {'conn': init_db()})
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
