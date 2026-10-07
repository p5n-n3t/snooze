"""Localhost web view with authenticated control requests."""
import hmac
import json
import mimetypes
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie, CookieError
from pathlib import Path
from urllib.parse import unquote, urlparse

from snooze.views import dashboard_state, task_detail


def authorized(headers, host, token):
    supplied = headers.get('X-Snooze-Token', '')
    if not supplied:
        try:
            cookies = SimpleCookie(headers.get('Cookie', ''))
            supplied = cookies['snooze_control'].value if 'snooze_control' in cookies else ''
        except CookieError:
            return False
    return headers.get('Origin') == 'http://' + host and hmac.compare_digest(supplied, token)


def authorized_read(headers, host, token):
    supplied = headers.get('X-Snooze-Token', '')
    if supplied:
        return headers.get('Origin') == 'http://' + host and hmac.compare_digest(supplied, token)
    try:
        cookies = SimpleCookie(headers.get('Cookie', ''))
        supplied = cookies['snooze_control'].value if 'snooze_control' in cookies else ''
    except CookieError:
        return False
    if not supplied or not hmac.compare_digest(supplied, token):
        return False
    origin = headers.get('Origin')
    if origin is not None:
        return origin == 'http://' + host
    if headers.get('Sec-Fetch-Site') == 'same-origin':
        return True
    referer = headers.get('Referer', '')
    parsed_referer = urlparse(referer)
    return parsed_referer.scheme == 'http' and parsed_referer.netloc == host


def safe_link(value):
    parsed = urlparse(value)
    return value if parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password else None


def _make_server(store, project, monitor, token, port=8765, project_config=None, static_root=None):
    static = Path(static_root) if static_root is not None else Path(__file__).parent / 'static'
    static = static.resolve()
    config = project_config if isinstance(project_config, dict) else {}
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
            host = self.headers.get('Host', '')
            valid_hosts = {f'localhost:{port}', f'127.0.0.1:{port}'}
            if port == 0:
                bound_port = self.server.server_address[1]
                valid_hosts = {f'localhost:{bound_port}', f'127.0.0.1:{bound_port}'}
            if host not in valid_hosts:
                return self.send({'error': 'Invalid host'}, 403)
            path = urlparse(self.path).path
            if path == '/api/health':
                return self.send({'name': 'snooze', 'api_version': 2, 'project': project})
            if path == '/api/v2/state':
                if not authorized_read(self.headers, host, token):
                    return self.send({'error': 'Origin and control token required'}, 403)
                return self.send(dashboard_state(store, project, config, time.time()))
            task_match = re.fullmatch(r'/api/v2/tasks/([^/]+)', path)
            if task_match:
                if not authorized_read(self.headers, host, token):
                    return self.send({'error': 'Origin and control token required'}, 403)
                task_id = unquote(task_match.group(1))
                detail = task_detail(store, project, task_id)
                return self.send(detail if detail is not None else {'error': 'Not found'}, 200 if detail is not None else 404)
            if path == '/api/state':
                if not authorized_read(self.headers, host, token):
                    return self.send({'error': 'Origin and control token required'}, 403)
                return self.send(store.snapshot(project))
            if path == '/api/incidents':
                if not authorized_read(self.headers, host, token):
                    return self.send({'error': 'Origin and control token required'}, 403)
                return self.send(store.snapshot(project)['incidents'])
            relative = 'index.html' if path == '/' else unquote(path).lstrip('/')
            if not relative or '\\' in relative or '\x00' in relative:
                return self.send({'error': 'Not found'}, 404)
            target = (static / relative).resolve()
            try:
                target.relative_to(static)
                if not target.is_file():
                    raise ValueError('not a file')
                content = target.read_bytes()
            except (OSError, RuntimeError, ValueError):
                return self.send({'error': 'Not found'}, 404)
            self.send_response(200)
            content_type = mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'")
            if path == '/':
                self.send_header('Set-Cookie', f'snooze_control={token}; HttpOnly; SameSite=Strict; Path=/')
            self.end_headers()
            self.wfile.write(content)

        def do_POST(self):
            host = self.headers.get('Host', '')
            bound_port = self.server.server_address[1]
            if host not in (f'localhost:{bound_port}', f'127.0.0.1:{bound_port}') or not authorized(self.headers, host, token):
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

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def serve(store, project, monitor, token, port=8765, project_config=None):
    server = _make_server(store, project, monitor, token, port, project_config)
    server.serve_forever()
