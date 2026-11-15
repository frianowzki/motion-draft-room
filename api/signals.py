"""Serve the data branch's signals.json to the static UI.

Why a function instead of a static file: the UI is deployed from `main`, the data
lives on the `data` branch (committed every 4 hours). This reads the raw file from
GitHub's CDN and re-serves it, so a deploy of the front-end never has to be repeated
just to pick up new snapshots.

No secrets: the repo is public, this is a read of a public RAW file.
"""

import json
import os
import urllib.request

RAW = "https://raw.githubusercontent.com/{repo}/data/data/{path}"
REPO = os.environ.get("DATA_REPO", "frianowzki/motion-draft-room")
UA = "motion-draft-room/0.1"


def _fetch(path: str) -> bytes:
    req = urllib.request.Request(RAW.format(repo=REPO, path=path), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def handler(request):
    """Vercel Python runtime entrypoint."""
    try:
        body = _fetch("signals.json")
        status = 200
        payload = body
    except Exception as exc:
        status = 503
        payload = json.dumps({"error": "upstream unavailable", "detail": str(exc)}).encode()

    return {
        "statusCode": status,
        "headers": {
            "content-type": "application/json; charset=utf-8",
            "cache-control": "public, max-age=60, s-maxage=300",
            "access-control-allow-origin": "*",
        },
        "body": payload.decode("utf-8", "replace"),
    }
