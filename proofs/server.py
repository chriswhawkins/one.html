#!/usr/bin/env python3
"""Optional dependency-free signaling and streamed-HTML server for the proof lab.

Run from any directory. Serves this repository only. Sessions expire after 15
minutes and hold SDP in memory, not surface content. No public ICE/TURN service
is supplied. For phones use --bind plus a certificate trusted by the devices.
"""
import argparse
import base64
import hashlib
import struct
import functools
import hmac
import json
from pathlib import Path
import secrets
import ssl
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
SESSIONS = {}
LOCK = threading.Lock()
TTL = 15 * 60
MAX_BODY = 120_000


def valid_sdp(value, kind):
    return (isinstance(value, dict) and value.get('type') == kind
            and isinstance(value.get('sdp'), str)
            and 0 < len(value['sdp']) < 100_000)


class Handler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, format, *args):
        # SDP credentials and capability tokens must not enter access logs.
        if '/api/' not in self.path:
            super().log_message(format, *args)

    def json_response(self, status, body):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        parsed = urlsplit(self.path)
        if not parsed.path.startswith('/proofs/api/'):
            return self.json_response(404, {'error': 'Unknown endpoint.'})
        origin = self.headers.get('Origin')
        scheme = 'https' if isinstance(self.connection, ssl.SSLSocket) else 'http'
        expected = scheme + '://' + self.headers.get('Host', '')
        if origin and origin != expected:
            return self.json_response(403, {'error': 'Same-origin requests only.'})
        if self.headers.get('Sec-Fetch-Site') == 'cross-site':
            return self.json_response(403, {'error': 'Same-origin requests only.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= MAX_BODY:
                return self.json_response(413, {'error': 'Invalid request size.'})
            if self.headers.get_content_type() != 'application/json':
                return self.json_response(415, {'error': 'JSON required.'})
            self.connection.settimeout(10)
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError()
        except (ValueError, OSError):
            return self.json_response(400, {'error': 'Invalid JSON request.'})
        with LOCK:
            self.expire()
            if parsed.path == '/proofs/api/session':
                if not valid_sdp(body.get('offer'), 'offer'):
                    return self.json_response(400, {'error': 'Valid offer required.'})
                if len(SESSIONS) >= 100:
                    return self.json_response(503, {'error': 'Session limit reached; try later.'})
                session_id, host, guest = (secrets.token_urlsafe(18) for _ in range(3))
                SESSIONS[session_id] = {'hostToken': host, 'guestToken': guest,
                                        'offer': body['offer'], 'answer': None,
                                        'expires': time.monotonic() + TTL}
                return self.json_response(201, {'id': session_id, 'hostToken': host,
                                                'guestToken': guest, 'expiresIn': TTL})
            session_id = parsed.path.removeprefix('/proofs/api/session/')
            session = SESSIONS.get(session_id)
            if not session or not self.token_matches(body.get('token'), session['guestToken']):
                return self.json_response(404, {'error': 'Session unavailable or expired.'})
            if session['answer'] is not None:
                return self.json_response(409, {'error': 'This invite has already been used. Create another session.'})
            if not valid_sdp(body.get('answer'), 'answer'):
                return self.json_response(400, {'error': 'Valid answer required.'})
            session['answer'] = body['answer']
            return self.json_response(200, {'ok': True})

    @staticmethod
    def token_matches(actual, expected):
        return (isinstance(actual, str) and actual.isascii() and len(actual) == len(expected)
                and hmac.compare_digest(actual, expected))

    @staticmethod
    def expire():
        for key in list(SESSIONS):
            if SESSIONS[key]['expires'] <= time.monotonic():
                del SESSIONS[key]

    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path == '/proofs/echo':
            return self.websocket_echo()
        if parsed.path == '/proofs/api/health':
            return self.json_response(200, {'service': 'one-proof', 'version': 1})
        if parsed.path.startswith('/proofs/api/session/'):
            token = parse_qs(parsed.query).get('token', [''])[0]
            with LOCK:
                self.expire()
                session = SESSIONS.get(parsed.path.removeprefix('/proofs/api/session/'))
                if session:
                    if self.token_matches(token, session['hostToken']):
                        return self.json_response(200, {'answer': session['answer']})
                    if self.token_matches(token, session['guestToken']):
                        if session['answer'] is not None:
                            return self.json_response(409, {'error': 'Invite already used. Ask the host for a new session.'})
                        return self.json_response(200, {'offer': session['offer']})
            return self.json_response(404, {'error': 'Session unavailable or expired.'})
        if parsed.path.startswith('/proofs/api/'):
            return self.json_response(404, {'error': 'Unknown endpoint.'})
        if parsed.path == '/proofs/stream':
            return self.stream()
        relative = Path(unquote(parsed.path).lstrip('/'))
        path = (ROOT / relative).resolve()
        if (any(part.startswith('.') for part in relative.parts)
                or not path.is_relative_to(ROOT)
                or (path.is_file() and path.suffix.lower() not in
                    {'.html', '.js', '.css', '.md', '.json', '.jpg', '.png', '.webp', '.svg', '.wasm', '.py'})):
            return self.send_error(404)
        if path.is_dir() and not (path / 'index.html').is_file():
            return self.send_error(404)
        return super().do_GET()

    def do_HEAD(self):
        # Only needed for tooling; do not expose a second, unfiltered file path.
        return self.send_error(405, 'Use GET')

    def websocket_echo(self):
        # A deliberately bounded RFC 6455 echo endpoint, not a general broker.
        scheme = 'https' if isinstance(self.connection, ssl.SSLSocket) else 'http'
        if self.headers.get('Origin') != scheme + '://' + self.headers.get('Host', ''):
            return self.json_response(403, {'error': 'Same-origin WebSocket only.'})
        key = self.headers.get('Sec-WebSocket-Key', '')
        try:
            valid_key = len(base64.b64decode(key, validate=True)) == 16
        except ValueError:
            valid_key = False
        if (self.headers.get('Upgrade', '').lower() != 'websocket'
                or self.headers.get('Sec-WebSocket-Version') != '13' or not valid_key):
            return self.json_response(400, {'error': 'WebSocket upgrade required.'})
        accept = base64.b64encode(hashlib.sha1((key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode()
        self.send_response(101)
        self.send_header('Upgrade', 'websocket')
        self.send_header('Connection', 'Upgrade')
        self.send_header('Sec-WebSocket-Accept', accept)
        self.end_headers()
        self.close_connection = True
        self.connection.settimeout(15)

        def read_exact(count):
            data = self.rfile.read(count)
            if len(data) != count:
                raise EOFError()
            return data

        def frame(opcode, data):
            size = len(data)
            header = bytes([128 | opcode, size]) if size < 126 else bytes([128 | opcode, 126]) + struct.pack('!H', size)
            self.wfile.write(header + data)
            self.wfile.flush()

        try:
            for _ in range(10):
                first, second = read_exact(2)
                opcode, length = first & 15, second & 127
                if length == 126:
                    length = struct.unpack('!H', read_exact(2))[0]
                elif length == 127:
                    length = struct.unpack('!Q', read_exact(8))[0]
                if (not first & 128 or first & 112 or not second & 128
                        or length > 16000 or opcode not in (1, 2, 8, 9, 10)
                        or (opcode >= 8 and length > 125)):
                    frame(8, struct.pack('!H', 1002))
                    return
                mask = read_exact(4)
                data = bytes(byte ^ mask[index % 4] for index, byte in enumerate(read_exact(length)))
                if opcode == 8:
                    frame(8, data)
                    return
                if opcode == 9:
                    frame(10, data)
                elif opcode in (1, 2):
                    if opcode == 1:
                        data.decode('utf-8')
                    frame(opcode, data)
        except (OSError, EOFError, UnicodeDecodeError):
            pass

    def stream(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Connection', 'close')
        self.close_connection = True
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'")
        self.end_headers()
        parts = [
            '<!doctype html><meta charset="utf-8"><style>body{font:16px system-ui;'
            'padding:16px;color:#182322;background:#fff}textarea{width:90%;font:inherit}'
            'section{padding:10px;border:1px solid #aaa;margin:10px 0}</style><body>'
            '<label>Draft stays here<textarea id="draft" rows="2" placeholder="Type while sections arrive"></textarea></label>'
            '<section id="first"><?start name="first">First section pending…<?end></section>'
            '<section id="second"><?start name="second">Second section pending…<?end></section>'
            '<p id="stream-proof"><?start name="done">Waiting for native patches…<?end></p>',
            '<template for="second">Second section arrived first.</template>',
            '<template for="first">First section arrived later.</template>',
            '<template for="done">Completed</template></body>',
        ]
        try:
            for index, part in enumerate(parts):
                if index:
                    time.sleep(1.5)
                self.wfile.write(part.encode())
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8001)
    parser.add_argument('--bind', default='127.0.0.1')
    parser.add_argument('--cert')
    parser.add_argument('--key')
    args = parser.parse_args()
    if bool(args.cert) != bool(args.key):
        parser.error('--cert and --key must be supplied together')
    server = ThreadingHTTPServer((args.bind, args.port), functools.partial(Handler, directory=str(ROOT)))
    if args.cert:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(args.cert, args.key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
    print(f"Open {'https' if args.cert else 'http'}://{args.bind}:{args.port}/proofs/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == '__main__':
    main()
