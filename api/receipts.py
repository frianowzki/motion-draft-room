"""Public receipt book at /api/receipts.

GET   -> every line-up receipt on the `data` branch, plus the settled/win rate
         computed from them. Nothing is filtered by who is asking: a hit rate
         nobody else can see proves nothing.

POST  -> file a receipt. Body is JSON:
           {"player": "@handle", "slotAtLock": "...", "picks": [{name, positionAtLock, estStars}]}
         The server recomputes the score from the snapshot that exists now, so a
         client cannot submit a score of its own. One receipt per player per
         slot: re-posting the same player+slot is rejected instead of stacking.

The file is data/receipts.json on the data branch. It is merged, not replaced,
so two visitors filing at once cannot overwrite each other.

The write needs a GitHub token. Without GITHUB_TOKEN the endpoint still reads
(and says so on POST) instead of pretending the receipt was saved.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from base64 import b64decode, b64encode
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

REPO = "frianowzki/motion-draft-room"
BRANCH = "data"
PATH = "data/receipts.json"
SNAPSHOT_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/data/signals.json"
MAX_BODY = 8_000
MAX_RECEIPTS = 500

# A handle that survives a public page: letters, digits, underscore, 1-15 chars,
# optional leading @. Anything else is rejected rather than sanitised, so a
# receipt cannot carry markup into someone else's browser.
HANDLE_RE = re.compile(r"^@?[A-Za-z0-9_]{1,15}$")

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def _json(handler, code, payload):
    body = json.dumps(payload).encode()
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    for k, v in CORS.items():
        handler.send_header(k, v)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _gh(path, method="GET", payload=None):
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("no GITHUB_TOKEN configured - receipts are read-only")
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "motion-draft-room",
            **({"Content-Type": "application/json"} if payload is not None else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read() or b"{}")


def _read_receipts():
    """Return (list, sha). A missing file is an empty book, not an error."""
    try:
        data = _gh(f"/repos/{REPO}/contents/{PATH}?ref={BRANCH}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return [], None
        raise
    raw = b64decode(data["content"]).decode()
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = []
    if isinstance(parsed, dict):
        parsed = parsed.get("receipts", [])
    return (parsed if isinstance(parsed, list) else []), data.get("sha")


def _summary(receipts):
    settled = [r for r in receipts if r.get("status") == "settled"]
    hits = [r for r in settled if (r.get("score") or 0) > 0]
    return {
        "count": len(receipts),
        "settled": len(settled),
        "pending": len(receipts) - len(settled),
        "hits": len(hits),
        "hitRate": (len(hits) / len(settled)) if settled else None,
        "netRank": sum(r.get("score") or 0 for r in settled),
    }


def _snapshots():
    with urllib.request.urlopen(SNAPSHOT_URL, timeout=20) as r:
        return json.loads(r.read())


def _settle(receipt, snap):
    """Grade against the snapshot on record, never against a client-supplied score.

    A receipt already graded stays graded: the score is the movement from lock to
    the first later snapshot, not whatever the board says today.
    """
    if receipt.get("status") == "settled":
        return receipt
    by_name = {c["name"]: c for c in snap.get("creators", [])}
    picks = receipt.get("picks") or []
    total, counted = 0, 0
    rows = []
    for p in picks:
        c = by_name.get(p.get("name"))
        if not c:
            rows.append({**p, "positionNow": None, "move": None})
            continue
        move = int(p["positionAtLock"]) - int(c["position"])
        total += move
        counted += 1
        rows.append({**p, "positionNow": c["position"], "move": move})
    if not counted:
        return None
    receipt = dict(receipt)
    receipt["picks"] = rows
    receipt["score"] = total
    receipt["settledAt"] = snap.get("dataAsOf")
    receipt["status"] = "settled"
    return receipt


class handler(BaseHTTPRequestHandler):  # noqa: N801 - Vercel looks for this name
    def log_message(self, format, *args):  # noqa: A002 - base class name, quiet log
        pass

    def do_OPTIONS(self):
        self.send_response(204)
        for k, v in CORS.items():
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        try:
            receipts, _ = _read_receipts()
        except Exception as e:
            _json(self, 502, {"error": f"could not read the book: {e}"})
            return
        try:
            snap = _snapshots()
        except Exception:
            snap = {"dataAsOf": None, "creators": []}

        # settle anything still pending, using this snapshot
        if snap.get("creators"):
            settled_now = []
            for r in receipts:
                if r.get("status") == "settled":
                    settled_now.append(r)
                else:
                    settled_now.append(_settle(r, snap) or r)
            receipts = settled_now

        receipts.sort(key=lambda r: (r.get("lockedAt") or ""), reverse=True)
        _json(self, 200, {
            "source": f"github:{REPO}@{BRANCH}:{PATH}",
            "asOf": snap.get("dataAsOf"),
            "summary": _summary(receipts),
            "receipts": receipts[:60],
        })

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY:
            _json(self, 413, {"error": "body must be 1-8000 bytes"})
            return
        try:
            body = json.loads(self.rfile.read(length))
        except Exception:
            _json(self, 400, {"error": "body is not JSON"})
            return

        player = str(body.get("player") or "").strip()
        if not HANDLE_RE.match(player):
            _json(self, 400, {"error": "player must be an X handle: letters, digits, underscore, up to 15 chars"})
            return
        picks = body.get("picks")
        if not isinstance(picks, list) or not (1 <= len(picks) <= 5):
            _json(self, 400, {"error": "picks must be a list of 1-5 entries"})
            return

        clean = []
        for p in picks:
            if not isinstance(p, dict):
                _json(self, 400, {"error": "each pick must be an object"})
                return
            name = str(p.get("name") or "").strip()
            try:
                pos = int(str(p.get("positionAtLock")))
                stars = int(str(p.get("estStars")))
            except (TypeError, ValueError):
                _json(self, 400, {"error": "each pick needs integer positionAtLock and estStars"})
                return
            if not name or len(name) > 60 or not (1 <= pos <= 200) or not (1 <= stars <= 8):
                _json(self, 400, {"error": "pick out of range"})
                return
            thesis = str(p.get("thesis") or "")[:120]
            premortem = str(p.get("premortem") or "")[:120]
            clean.append({"name": name, "positionAtLock": pos, "estStars": stars,
                          "thesis": thesis, "premortem": premortem})

        try:
            snap = _snapshots()
        except Exception as e:
            _json(self, 502, {"error": f"cannot read the snapshot to grade this: {e}"})
            return
        slot = body.get("slotAtLock") or snap.get("dataAsOf")
        if not slot:
            _json(self, 502, {"error": "no snapshot on record yet - nothing to grade against"})
            return
        if snap.get("dataAsOf") and slot > snap.get("dataAsOf"):
            _json(self, 400, {"error": "slotAtLock is in the future of the snapshot on record"})
            return

        receipt = {
            "player": player.lstrip("@"),
            "slotAtLock": slot,
            "picks": clean,
            "status": "pending",
            "lockedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        receipt = _settle(receipt, snap) or receipt

        try:
            receipts, sha = _read_receipts()
        except Exception as e:
            _json(self, 502, {"error": f"cannot read the book: {e}"})
            return

        for r in receipts:
            if r.get("player", "").lower() == receipt["player"].lower() and r.get("slotAtLock") == receipt["slotAtLock"]:
                _json(self, 409, {"error": "this handle already filed a lineup for that slot"})
                return

        receipts.insert(0, receipt)
        receipts = receipts[:MAX_RECEIPTS]

        try:
            _gh(
                f"/repos/{REPO}/contents/{PATH}",
                method="PUT",
                payload={
                    "message": f"receipt: {receipt['player']} @ {receipt['slotAtLock']}",
                    "content": b64encode((json.dumps(receipts, indent=1) + "\n").encode()).decode(),
                    "branch": BRANCH,
                    **({"sha": sha} if sha else {}),
                },
            )
        except Exception as e:
            _json(self, 502, {"error": f"could not save the receipt: {e}"})
            return

        _json(self, 201, {"ok": True, "receipt": receipt, "summary": _summary(receipts)})
