#!/usr/bin/env python3
# File: capture_proxy.py
# Purpose: Capture ONE real Claude Code request verbatim, for replay.
# Project: sparkbench | Date: 2026-08-29
#
# Overview: Sits between `claude` and llama-server, forwards byte-for-byte, and
# dumps each request body to disk. Every synthetic probe this session has been
# easier than the real harness and therefore wrong: a toy tool passes on models
# that fail Claude Code's actual schemas. The only faithful cheap instrument is
# the real request, replayed - so capture it once instead of inventing it.
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request, pathlib, sys, json

UPSTREAM = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8559"
OUTDIR = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/capture")
OUTDIR.mkdir(parents=True, exist_ok=True)
N = [0]

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("content-length", 0)))
        N[0] += 1
        # Keep the FIRST request of each path: that is the one carrying the
        # full tool array before any tool_result turns inflate it.
        f = OUTDIR / f"req-{N[0]:03d}-{self.path.strip('/').replace('/','_')}.json"
        try: f.write_bytes(body)
        except Exception: pass
        req = urllib.request.Request(UPSTREAM + self.path, data=body,
              headers={k: v for k, v in self.headers.items()
                       if k.lower() not in ("host", "content-length")})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                data = r.read(); code = r.status
                ctype = r.headers.get("content-type", "application/json")
        except urllib.error.HTTPError as e:
            data = e.read(); code = e.code; ctype = "application/json"
        except Exception as e:
            data = json.dumps({"error": {"message": str(e)}}).encode()
            code = 502; ctype = "application/json"
        self.send_response(code)
        self.send_header("content-type", ctype)
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

print(f"proxy -> {UPSTREAM}, dumping to {OUTDIR}", flush=True)
HTTPServer(("127.0.0.1", 8560), H).serve_forever()
