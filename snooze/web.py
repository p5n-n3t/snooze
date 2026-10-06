"""Localhost web view with authenticated control requests."""
import hmac
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


def authorized(headers, host, token):
    return headers.get('Origin') == 'http://' + host and hmac.compare_digest(headers.get('X-Snooze-Token', ''), token)


def safe_link(value):
    parsed = urlparse(value)
    return value if parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password else None


def serve(store, project, monitor, token, port=8765):
    static = Path(__file__).parent / 'static'
    check_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, payload, status=200):
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.headers.get('Host') not in (f'localhost:{port}', f'127.0.0.1:{port}'):
                return self.send({'error': 'Invalid host'}, 403)
            path = urlparse(self.path).path
            if path == '/api/state':
                return self.send(store.snapshot(project))
            if path == '/api/incidents':
                return self.send(store.snapshot(project)['incidents'])
            filename = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css'}.get(path)
            if not filename:
                return self.send({'error': 'Not found'}, 404)
            content = (static / filename).read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', {'index.html': 'text/html', 'app.js': 'text/javascript', 'style.css': 'text/css'}[filename])
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(content)

        def do_POST(self):
            host = self.headers.get('Host', '')
            if host not in (f'localhost:{port}', f'127.0.0.1:{port}') or not authorized(self.headers, host, token):
                return self.send({'error': 'Origin and control token required'}, 403)
            try:
                length = int(self.headers.get('Content-Length', 0))
                if not 0 < length <= 8192:
                    raise ValueError('Invalid body size')
                body = json.loads(self.rfile.read(length))
                if self.path == '/api/settings':
                    store.set_settings(project, body)
                elif self.path == '/api/check':
                    if not check_lock.acquire(blocking=False):
                        return self.send({'error': 'Check already running'}, 409)
                    def run():
                        try:
                            monitor.check(project)
                        finally:
                            check_lock.release()
                    threading.Thread(target=run, daemon=True).start()
                elif self.path == '/api/ack':
                    store.ack(project, body['job'], body['kind'])
                else:
                    return self.send({'error': 'Not found'}, 404)
                self.send({'ok': True})
            except (ValueError, KeyError, TypeError):
                self.send({'error': 'Invalid request'}, 400)

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.serve_forever()
