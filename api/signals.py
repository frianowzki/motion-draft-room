"""Serve a fresher signals.json than the copy bundled at build time.

The UI is deployed from `main`; the data is rewritten every 4 hours on the `data`
branch. Reading the raw file from GitHub at request time means a new snapshot shows
up without waiting for a redeploy. Public repo, public raw file — no secrets here.

Vercel Python functions need the module-level `handler` (BaseHTTPRequestHandler
subclass), so this follows that convention rather than the dict-returning one.
"""

import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler

REPO = os.environ.get("DATA_REPO", "frianowzki/motion-draft-room")
RAW = f"https://raw.githubusercontent.com/{REPO}/data/data/signals.json"
UA = "motion-draft-room/0.1"


def fetch() -> bytes:
    req = urllib.request.Request(RAW, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read()


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            body = fetch()
            json.loads(body)  # fail fast if upstream is not valid JSON
            code = 200
        except Exception as exc:
            body = json.dumps({"error": "upstream unavailable", "detail": str(exc)}).encode()
            code = 503

        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "public, max-age=60, s-maxage=300")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
