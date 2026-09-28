"""Single-origin event gateway. Cloudflare Access remains the outer login gate.

Only explicit upstreams and the Stage 3 build are served. No directory listings,
open proxy, HTML-wide URL substitutions or buffering of SSE/large media.
"""
from __future__ import annotations
import argparse
import base64
import hmac
import http.client
import json
import mimetypes
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
HOP = {'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
       'te', 'trailer', 'transfer-encoding', 'upgrade'}


class Gateway(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, *, room=8020, forest=8024, films=8022,
                 cinematic=8021, gm_credentials=None, web_root=None):
        self.ports = dict(room=room, forest=forest, films=films, cinematic=cinematic)
        self.gm_credentials = gm_credentials
        self.web_root = Path(web_root or ROOT/'web').resolve()
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, fmt, *args):
        # Query strings can contain private team capabilities.
        print(f'{self.command} {urlsplit(self.path).path} {args[1] if len(args)>1 else ""}', flush=True)

    def reply(self, status, body=b'', **headers):
        self.send_response(status)
        for k,v in headers.items(): self.send_header(k.replace('_','-'),str(v))
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Connection', 'close')
        self.end_headers()
        self.close_connection = True
        if self.command != 'HEAD': self.wfile.write(body)

    def authorised(self, path, query):
        private = (path == '/gm' or path.startswith('/gm/') or
                   path.startswith('/api/gm/') or
                   path in {'/api/state','/api/steps','/api/logs','/api/log'} or path.startswith('/api/log/') or
                   (path == '/events' and parse_qs(query).get('ch', ['projector']) != ['phone']
                    and parse_qs(query).get('ch', ['projector']) != ['projector']))
        if not private: return True
        expected = self.server.gm_credentials
        if not expected:
            self.reply(503, b'GM access has not been configured.'); return False
        try:
            scheme, value = self.headers.get('Authorization','').split(' ',1)
            supplied = base64.b64decode(value,validate=True).decode() if scheme.lower()=='basic' else ''
        except (ValueError,UnicodeError): supplied = ''
        if hmac.compare_digest(supplied.encode(), expected.encode()): return True
        self.reply(401, b'Organiser login required.', WWW_Authenticate='Basic realm="Pyrocene organiser", charset="UTF-8"')
        return False

    def do_GET(self): self.dispatch()
    def do_HEAD(self): self.dispatch()
    def do_POST(self): self.dispatch()

    def dispatch(self):
        u = urlsplit(self.path)
        path = unquote(u.path)
        if (u.scheme or u.netloc or not path.startswith('/') or '\\' in path or
            '%' in path or any(p in {'.','..'} for p in path.split('/')) or
            any(ord(c)<32 for c in path) or '//' in path):
            return self.reply(400, b'Invalid path.')
        if path == '/healthz':
            return self.reply(200, b'{"service":"pyrocene-gateway"}', Content_Type='application/json')
        if path in {'/stage4','/stage3','/films','/cinematic'}:
            return self.reply(308, Location=path+'/' + ('?'+u.query if u.query else ''))
        if path == '/stage4/':
            return self.reply(302, Location='/stage4/expedition.html'+('?' +u.query if u.query else ''))
        if path.startswith('/stage3/'):
            if self.command not in {'GET','HEAD'}: return self.reply(405)
            return self.stage3(path[len('/stage3/'):])
        prefix = ''
        if path == '/lore' or path.startswith('/lore/'):
            service, upstream = 'forest', path
        elif path.startswith('/stage4/'):
            service, prefix = 'forest', '/stage4'
            upstream = path[len(prefix):]
        elif path.startswith('/films/'):
            service, prefix = 'films', '/films'
            upstream = path[len(prefix):]
        elif path.startswith('/cinematic/'):
            service, prefix = 'cinematic', '/cinematic'
            upstream = path[len(prefix):]
        else:
            if not self.authorised(path,u.query): return
            service, upstream = 'room', path
            # HTML source aliases would otherwise bypass the GM page challenge.
            if path == '/static/gm.html' and not self.authorised('/gm',''): return
        if self.headers.get('Transfer-Encoding'):
            return self.reply(400,b'Use Content-Length.')
        origin = self.headers.get('Origin')
        host = self.headers.get('Host','')
        if self.command=='POST' and origin:
            if origin not in {f'http://{host}', f'https://{host}'}:
                return self.reply(403,b'Use this game page to send actions.')
        try: size = int(self.headers.get('Content-Length','0'))
        except ValueError: return self.reply(400)
        if not 0 <= size <= 2*1024*1024: return self.reply(413)
        self.connection.settimeout(35)
        try: body = self.rfile.read(size) if size else None
        except OSError: return self.reply(408)
        if body is not None and len(body)!=size: return self.reply(400)
        target = quote(upstream,safe='/-._~') + ('?'+u.query if u.query else '')
        conn = http.client.HTTPConnection('127.0.0.1', self.server.ports[service], timeout=40)
        sent = False
        try:
            excluded = HOP | {'host','authorization','accept-encoding','content-length'}
            excluded |= {x.strip().lower() for x in self.headers.get('Connection','').split(',')}
            headers = {k:v for k,v in self.headers.items() if k.lower() not in excluded}
            headers['Host'] = self.headers.get('Host','localhost')
            headers['Accept-Encoding'] = 'identity'
            # TLS ends at Cloudflare. After validating the browser's origin,
            # express it in the HTTP transport used by our local backends.
            # Stage 4 still performs its own same-origin check; untrusted
            # forwarded headers never decide which origins are accepted.
            if self.command == 'POST' and origin:
                headers['Origin'] = f'http://{host}'
            conn.request(self.command, target, body=body, headers=headers)
            response = conn.getresponse()
            modified = None
            is_html = response.getheader('Content-Type','').startswith('text/html')
            if self.command != 'HEAD' and is_html and (path=='/start' or service=='forest'):
                modified = response.read()
                if path=='/start': modified=modified.replace(b'<head>',b'<head><meta name="pyrocene-gateway" content="1">',1)
                if prefix: modified=modified.replace(b'<base href="/">',f'<base href="{prefix}/">'.encode())
            self.send_response(response.status)
            excluded = HOP | {'server','date'}
            excluded |= {x.strip().lower() for x in response.getheader('Connection','').split(',')}
            for k,v in response.getheaders():
                if k.lower() in excluded or (modified is not None and k.lower()=='content-length'): continue
                if k.lower()=='location' and prefix and v.startswith('/') and not v.startswith('//'): v=prefix+v
                self.send_header(k,v)
            if modified is not None: self.send_header('Content-Length',str(len(modified)))
            self.send_header('Connection','close')
            self.send_header('X-Content-Type-Options','nosniff')
            self.end_headers(); sent=True; self.close_connection=True
            if self.command=='HEAD': return
            if modified is not None: self.wfile.write(modified); return
            # read1 returns available SSE bytes immediately. read(n) can wait
            # for a full buffer and make an otherwise live room appear frozen.
            while chunk := response.read1(128*1024):
                self.wfile.write(chunk); self.wfile.flush()
        except (OSError,http.client.HTTPException):
            if not sent: self.reply(502,b'This game service is starting or unavailable. Please retry.')
        finally: conn.close()

    def stage3(self, relative):
        name = relative or 'index.html'
        if name not in {'index.html','app.css','main.js','worker.js','boot.py'} and not name.startswith('py/'):
            return self.reply(404)
        target=(self.server.web_root/name).resolve()
        if not target.is_relative_to(self.server.web_root) or not target.is_file(): return self.reply(404)
        data=target.read_bytes()
        self.reply(200,data,Content_Type=mimetypes.guess_type(name)[0] or 'application/octet-stream',
                   Cross_Origin_Opener_Policy='same-origin',Cross_Origin_Embedder_Policy='require-corp')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--host',default='127.0.0.1');ap.add_argument('--port',type=int,default=8030)
    ap.add_argument('--gm-file',type=Path,required=True)
    args=ap.parse_args()
    credentials=args.gm_file.read_text().strip()
    if ':' not in credentials or len(credentials.split(':',1)[1])<16: ap.error('GM credentials require user:password (password at least 16 characters).')
    server=Gateway((args.host,args.port),gm_credentials=credentials)
    print(f'Pyrocene gateway on {args.host}:{args.port}',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()


if __name__=='__main__': main()
