"""Public receipt book at /api/receipts.

GET   -> every line-up receipt, plus the settled/win rate computed from them.
         Nothing is filtered by who is asking: a hit rate nobody else can see
         proves nothing.

POST  -> file a receipt. Body is JSON:
           {"slotAtLock": "...", "picks": [{name, positionAtLock, estStars}]}
         The player is the X account that signed in through /api/xauth, read from the
         signed session cookie. A handle in the body is ignored: attributing a call
         to someone who did not make it is the one thing this book cannot allow.
         The server recomputes the score from the snapshot that exists now, so a
         client cannot submit a score of its own. One receipt per player per
         slot: re-posting the same player+slot is rejected instead of stacking.

Receipts live in Postgres (see receipt_store.py). It used to be one JSON file on a
git branch, which meant every filing was a read-modify-write of the whole book: two
visitors filing at the same moment lost one of the two writes, and uniqueness was a
loop here rather than a rule the database could enforce. Now a filing is an INSERT
and `unique (receipts.xid, receipts.slot_at_lock)` decides who was first.

Writes need SUPABASE_URL + SUPABASE_KEY. Without them the endpoint fails loudly
rather than reporting a receipt it did not save. The snapshot the grading reads is
still the collector's artefact on the data branch, so GITHUB_TOKEN is still needed.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

# Both api/ and api/xauth/ hold a copy of this module: a Vercel function's own
# directory is on sys.path (api/ here, api/xauth/ for the OAuth steps), and the
# repository root is not reliably importable from a nested function.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import receipt_store as store
import xauth_lib as xl

REPO = "frianowzki/motion-draft-room"
BRANCH = "data"
SNAPSHOT_PATH = "data/signals.json"
SNAPSHOT_URL = f"https://api.github.com/repos/{REPO}/contents/{SNAPSHOT_PATH}?ref={BRANCH}"
MAX_BODY = 8_000

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


def _settle_one(receipt, snap):
    """Grade a receipt in place-ish, and report whether it changed.

    Pending receipts are graded on read; already-graded ones are not touched, so a
    GET is a write only when it actually moved a receipt forward. That distinction
    matters now that writing is an HTTP call to Postgres rather than a local edit.
    """
    if not (snap.get("rows") or snap.get("creators")):
        return receipt, False
    graded = _settle(receipt, snap)
    if not graded:
        return receipt, False
    return graded, graded.get("score") != receipt.get("score") or \
        graded.get("status") != receipt.get("status")


def _summary(receipts):
    settled = [r for r in receipts if r.get("status") == "settled"]
    hits = [r for r in settled if (r.get("score") or 0) > 0]
    return {
        "count": len(receipts),
        "settled": len(settled),
        "pending": len(receipts) - len(settled),
        "hits": len(hits),
        # hitRate is over GRADED receipts only, which is what `settled` means here:
        # a receipt is never graded against its own lock window, so a pending one is
        # not a miss and must not dilute anyone's rate.
        "hitRate": (len(hits) / len(settled)) if settled else None,
        "netRank": sum(r.get("score") or 0 for r in settled),
    }


def _snapshots():
    """The snapshot lives on a private branch, so this read needs the same token the
    write path uses — the anonymous raw host answers 404 now."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    headers = {"User-Agent": "motion-draft-room/0.1",
               "Accept": "application/vnd.github.raw",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(SNAPSHOT_URL, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def _settle(receipt, snap):
    """Grade against a snapshot from a LATER window than the lock, never the lock's own.

    A lineup locked in the 12:00 window and graded against the 12:00 window scores
    exactly 0 for everyone: the movement it is supposed to measure has not happened
    yet. Only a snapshot with a strictly greater `dataAsOf` is a fair grade, so a
    receipt whose lock slot is still the newest window stays pending. The score is
    also never taken from the client - it is recomputed here from the rows below.

    A receipt graded by this function stays graded: the score is the movement from
    lock to the first later snapshot, not whatever the board says today. Receipts
    without `gradedAsOf` were written by the old grader, which read the wrong key
    and graded against the lock's own window - those are regraded once.
    """
    if receipt.get("status") == "settled" and receipt.get("gradedAsOf"):
        return receipt
    snap_as_of = snap.get("dataAsOf")
    if snap_as_of and receipt.get("slotAtLock") and snap_as_of <= receipt["slotAtLock"]:
        return None  # no later window on record yet - still pending, not a zero
    # Snapshots (collector/snapshot.py) write `rows`; `creators` is the signals
    # shape. Reading the wrong key here silently graded every pick as "not found",
    # so keep the fallback but prefer the real one.
    rows_in = snap.get("rows") or snap.get("creators") or []
    by_name = {c["name"]: c for c in rows_in if c.get("name")}
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
    receipt["settledAt"] = snap_as_of
    receipt["gradedAsOf"] = snap_as_of
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
            receipts = store.read(store.PAGE)
        except Exception as e:
            _json(self, 502, {"error": f"could not read the book: {e}"})
            return
        try:
            snap = _snapshots()
        except Exception:
            snap = {"dataAsOf": None}

        # regrade anything still pending against this snapshot; receipts that a later
        # window has already graded keep the score they earned then
        changed = []
        for r in receipts:
            graded, moved = _settle_one(r, snap)
            if moved:
                changed.append(graded)
        try:
            store.regrade(changed)
        except Exception:
            # A failed regrade must not cost the reader their page: the grades are
            # still correct for this response and will be written on the next one.
            pass

        receipts.sort(key=lambda r: (r.get("lockedAt") or ""), reverse=True)
        _json(self, 200, {
            "source": "supabase:receipts",
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

        user = xl.session_of(self.headers)
        if not user:
            _json(self, 401, {"error": "connect X first - a receipt carries the handle of the "
                                       "account that filed it, so the book can be checked"})
            return
        player = str(user.get("handle") or "")
        if not HANDLE_RE.match(player):
            _json(self, 401, {"error": "the session does not carry a usable X handle - reconnect X"})
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
            # The rarity a player claimed. Recorded, not scored: receipts grade rank
            # movement against a snapshot, and the Motion Score a boost multiplies
            # is not public - so scoring on it would be scoring on our stand-in.
            rarity = str(p.get("rarity") or "Common").strip().capitalize()
            if rarity not in ("Common", "Rare", "Epic", "Legendary"):
                rarity = "Common"
            clean.append({"name": name, "positionAtLock": pos, "estStars": stars,
                          "rarity": rarity, "thesis": thesis, "premortem": premortem})

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
            "xid": str(user.get("id") or ""),
            "name": str(user.get("name") or "")[:40],
            "avatar": str(user.get("avatar") or ""),
            "slotAtLock": slot,
            "picks": clean,
            "status": "pending",
            "lockedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        receipt = _settle(receipt, snap) or receipt

        # Uniqueness is the database's now: `unique (xid, slot_at_lock)` on the table.
        # This endpoint used to scan the whole book in Python, which raced - two
        # filings at the same instant both passed the scan and one overwrote the other.
        try:
            saved = store.insert(receipt)
        except store.Duplicate:
            _json(self, 409, {"error": f"@{receipt['player']} already filed a lineup for that slot"})
            return
        except Exception as e:
            _json(self, 502, {"error": f"could not save the receipt: {e}"})
            return

        # Catch the rest of the book up on a write as well as on a read, so a page
        # that is never reloaded does not leave graded receipts ungraded in storage.
        try:
            changed = []
            for r in store.read(store.PAGE):
                graded, moved = _settle_one(r, snap)
                if moved:
                    changed.append(graded)
            store.regrade(changed)
        except Exception:
            pass

        try:
            receipts = store.read(store.PAGE)
        except Exception:
            receipts = [saved]
        _json(self, 201, {"ok": True, "receipt": saved, "summary": _summary(receipts)})
