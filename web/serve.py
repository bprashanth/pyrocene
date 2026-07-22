#!/usr/bin/env python3
"""Local dev server that sets the same COOP/COEP headers Netlify will.

Plain `python3 -m http.server` will not work: without cross-origin isolation the
browser refuses to hand out SharedArrayBuffer and the game cannot read stdin.

    python3 web/serve.py          # http://localhost:8010
"""
import argparse
import functools
import http.server
import os


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        if "200" not in (args[1] if len(args) > 1 else ""):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8010)
    args = ap.parse_args()
    root = os.path.dirname(os.path.abspath(__file__))
    handler = functools.partial(Handler, directory=root)
    print(f"pyrocene on http://localhost:{args.port}  (serving {root})")
    http.server.ThreadingHTTPServer(("", args.port), handler).serve_forever()
