"""Serve a fresher signals.json than the copy bundled at build time.

The UI is deployed from `main`; the data is rewritten every 4 hours on the `data`
branch. Reading the file from GitHub at request time means a new snapshot shows up
without waiting for a redeploy.

The repository is private, so the anonymous raw host answers 404. The read goes
through the contents API with a fine-grained token that has read-only access to
this one repo (GITHUB_TOKEN / GH_TOKEN in the Vercel env). Without the token the
endpoint answers 503 with a plain reason instead of pretending the board is empty.

Vercel Python functions need the module-level `handler` (BaseHTTPRequestHandler
subclass), so this follows that convention rather than the dict-returning one.
"""

import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler

REPO = os.environ.get("DATA_REPO", "frianowzki/motion-draft-room")
PATH = "data/signals.json"
BRANCH = os.environ.get("DATA_BRANCH", "data")
RAW = f"https://api.github.com/repos/{REPO}/contents/{PATH}?ref={BRANCH}"
UA = "motion-draft-room/0.1"


def fetch() -> bytes:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("no GITHUB_TOKEN configured for the private data branch")
    req = urllib.request.Request(RAW, headers={
        "User-Agent": UA,
        "Accept": "application/vnd.github.raw",
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {token}",
    })
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
