"""Serve the snapshot history as one small, ordered array.

The Timeline on /app needs every recorded window, not just the newest board that
/api/signals serves. The snapshots live in data/snapshots/*.json on the `data`
branch, one file per collection run, and each one is ~13KB of full board rows.
Shipping all of them whole would be hundreds of kilobytes for something the page
only reads as "who moved between window i-1 and i", so this endpoint does the
reduction on the server and returns only what the Timeline draws:

    {"windows": [{"slot": "...", "asOf": "...", "rows": [{"name", "position"}]}]}

Two honest limits, because they decide what the page is allowed to claim:
- Only windows that actually exist are returned. The page must not extrapolate a
  window that was never collected, so a gap in collection shows as a gap.
- Runs inside the same leaderboard window (same `asOf`) are collapsed to one, the
  last one written, because two identical rows would read as history that does
  not exist.

The repository is private, so this reads through the contents API with the same
fine-grained read token the other endpoints use. Without it the answer is 503
with a plain reason rather than an empty array pretending there is no history.
"""

import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler

REPO = os.environ.get("DATA_REPO", "frianowzki/motion-draft-room")
BRANCH = os.environ.get("DATA_BRANCH", "data")
SNAP_DIR = "data/snapshots"
API = "https://api.github.com/repos/{repo}/contents/{path}?ref={branch}"
UA = "motion-draft-room/0.1"

# a year of 4-hour windows is 2190 files; well past anything this book will hold,
# but a bound keeps a runaway directory from turning into a slow response
MAX_FILES = 400


def _get(url: str, token: str, accept: str = "application/vnd.github+json") -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {token}",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def fetch_windows() -> list:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("no GITHUB_TOKEN configured for the private data branch")

    listing = json.loads(_get(API.format(repo=REPO, path=SNAP_DIR, branch=BRANCH), token))
    names = sorted(
        e["name"] for e in listing
        if e.get("type") == "file" and e["name"].endswith(".json")
    )[-MAX_FILES:]

    by_asof = {}
    for name in names:
        raw = _get(
            API.format(repo=REPO, path=f"{SNAP_DIR}/{name}", branch=BRANCH),
            token,
            accept="application/vnd.github.raw",
        )
        try:
            snap = json.loads(raw)
        except Exception:
            continue  # a half-written file must not poison the whole history
        rows = snap.get("rows") or []
        if not rows:
            continue
        key = snap.get("asOf") or snap.get("collectedAt") or name
        by_asof[key] = {
            "slot": snap.get("asOf") or snap.get("collectedAt"),
            "asOf": snap.get("asOf"),
            "collectedAt": snap.get("collectedAt"),
            "source": snap.get("source"),
            # the Timeline only needs identity and rank; handles and metrics are
            # already on the board and would double the payload for nothing
            "rows": [
                {"name": r.get("name"), "position": int(r.get("position") or 0)}
                for r in rows if r.get("name")
            ],
        }

    return [by_asof[k] for k in sorted(by_asof)]


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            windows = fetch_windows()
            body = json.dumps({"windows": windows, "count": len(windows)}).encode()
            code = 200
        except Exception as exc:
            body = json.dumps({"error": "history unavailable", "detail": str(exc)}).encode()
            code = 503

        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        # history changes at most once per 4-hour window
        self.send_header("Cache-Control", "public, max-age=300, s-maxage=600")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
