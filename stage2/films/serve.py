"""Serve the film gallery: the page from this repo, the films from wherever.

    python3 -m stage2.films.serve                 # :8022
    python3 -m stage2.films.serve --port 9000 --assets /some/other/drive

The masters are hundreds of megabytes and live outside the repo. The page that
indexes them is source and belongs with the code, so it is kept here and served
from here. Anything the page asks for that is not the page itself is read from
the asset root, which can sit on any disk.
"""
from __future__ import annotations
import argparse
import os
import sys
import re
from urllib.parse import unquote
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.environ.get("PYROCENE_FILMS", "/mnt/seagate/videos/pyrocene")


class Handler(SimpleHTTPRequestHandler):
    """Two roots. The page comes from the repo, everything else from the drive."""

    def translate_path(self, path: str) -> str:
        rel = unquote(path.split("?", 1)[0].split("#", 1)[0]).lstrip("/")
        if rel in ("", "index.html"):
            return os.path.join(HERE, "index.html")
        # Resolve inside the asset root and refuse anything that climbs out.
        full = os.path.realpath(os.path.join(self.server.assets, rel))
        root = os.path.realpath(self.server.assets)
        if full != root and not full.startswith(root + os.sep):
            return os.path.join(HERE, "index.html")
        return full

    def list_directory(self, path):
        self.send_error(404, "No gallery at this path")
        return None

    def send_head(self):
        self.range_remaining = None
        header = self.headers.get('Range')
        if not header or self.headers.get('If-Range'):
            return super().send_head()
        path = self.translate_path(self.path)
        if not os.path.isfile(path): return super().send_head()
        size = os.path.getsize(path)
        match = re.fullmatch(r'bytes=(\d*)-(\d*)', header.strip())
        try:
            if not match or not any(match.groups()): raise ValueError()
            a,b=match.groups()
            start=int(a) if a else max(0,size-int(b))
            end=min(size-1,int(b)) if a and b else size-1
            if start<0 or start>end or start>=size: raise ValueError()
        except ValueError:
            self.send_response(416);self.send_header('Content-Range',f'bytes */{size}')
            self.send_header('Content-Length','0');self.end_headers();return None
        f=open(path,'rb');f.seek(start)
        self.range_remaining=end-start+1
        self.send_response(206)
        self.send_header('Content-Type',self.guess_type(path))
        self.send_header('Accept-Ranges','bytes')
        self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length',str(self.range_remaining));self.end_headers()
        return f

    def copyfile(self, source, outputfile):
        try:
            if self.range_remaining is None: return super().copyfile(source,outputfile)
            while self.range_remaining:
                data=source.read(min(self.range_remaining,128*1024))
                if not data: break
                outputfile.write(data);self.range_remaining-=len(data)
        except (BrokenPipeError,ConnectionResetError): pass

    def log_message(self, fmt, *args):     # quiet; the launcher owns the console
        pass


def main():
    ap = argparse.ArgumentParser(description="the Pyrocene film gallery")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PYROCENE_FILMS_PORT", "8022")))
    ap.add_argument("--assets", default=ASSETS, help="where the films live")
    args = ap.parse_args()

    if not os.path.isdir(args.assets):
        print(f"films: no asset directory at {args.assets}")
        print("films: set PYROCENE_FILMS or pass --assets. The page will still")
        print("       load but every film on it will be missing.")

    try:
        srv = ThreadingHTTPServer((args.host, args.port), Handler)
    except OSError as e:
        print(f"films: cannot start on {args.host}:{args.port}: {e.strerror or e}")
        sys.exit(1)
    srv.assets = args.assets
    srv.daemon_threads = True
    print(f"films  page {HERE}/index.html   assets {args.assets}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
