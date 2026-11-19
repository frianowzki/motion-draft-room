"""The working lineup at /api/draft.

A draft was a localStorage key (`mdr_picks`), which meant it lived on exactly one
browser. Pick five on a laptop, open the site on a phone, and the lineup read 0/5:
the picks were never lost, they were simply on the other device. That is not a
draft, it is a bookmark.

GET   -> {"picks": [...]} for the signed-in X account. Empty list when nobody is
         signed in or nothing is saved yet, so a fresh visitor paints 0/5 rather
         than an error.
POST  -> replace the lineup. Body: {"picks": [{name, estStars, thesis, premortem,
         position, momentum, rarity}]}. The player is the session's handle, never
         a handle in the body.
DELETE-> clear it.

The row is keyed by xid and holds the picks as JSON: a lineup is read and written
whole, five entries at a time, and there is nothing to query inside it.

Writes need SUPABASE_URL + SUPABASE_KEY, the same pair /api/receipts uses. Without
them the endpoint says so instead of pretending to save; the client then keeps
working from localStorage, so an unconfigured deployment still functions on one
device.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "xauth"))

import receipt_store as store  # noqa: E402
import xauth_lib as xa  # noqa: E402

TABLE = "drafts"
# set the first time PostgREST answers "no such table"; kept module-level so a warm
# function does not pay for the same failing round trip on every request
TABLE_MISSING = ""
MAX_PICKS = 5
# a pick is five small fields; anything past this is not a lineup
MAX_BODY = 12_000


def _as_list(val):
    """PostgREST hands jsonb back already decoded, but a row written by an older
    build can hold a string or a bare object. Normalise to a list of dicts."""
    for _ in range(2):
        if isinstance(val, str):
            try:
                val = json.loads(val or "[]")
            except Exception:
                return []
    return val if isinstance(val, list) else []


def _picks_of(body):
    """Keep only the fields the board itself produces, bounded, so a POST cannot
    turn this row into arbitrary storage."""
    raw = body.get("picks")
    if not isinstance(raw, list):
        raise ValueError("picks must be a list")
    out = []
    for p in raw[:MAX_PICKS]:
        if not isinstance(p, dict):
            continue
        name = str(p.get("name") or "")[:60]
        if not name:
            continue
        out.append({
            "name": name,
            "estStars": p.get("estStars"),
            "thesis": str(p.get("thesis") or "")[:400],
            "premortem": str(p.get("premortem") or "")[:400],
            "position": p.get("position"),
            "momentum": p.get("momentum"),
            "rarity": str(p.get("rarity") or "Common")[:20],
        })
    return out


class handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, code, payload):
        raw = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _user(self):
        return xa.session_of(self.headers)

    def _xid(self, user):
        """The account key for a lineup.

        Sessions minted before `id` was requested from X carry no numeric id, and
        they stay valid for weeks, so an empty id cannot just be an error: those
        visitors get a handle-keyed row instead. A handle can be renamed, which is
        why the id is preferred whenever it is there.
        """
        xid = str(user.get("xid") or user.get("id") or "").strip()
        if xid:
            return xid
        handle = str(user.get("handle") or "").strip().lower()
        return f"h:{handle}" if handle else ""

    def do_GET(self):
        global TABLE_MISSING
        user = self._user()
        if not user:
            # not an error: the board is public, a draft simply needs a name on it
            return self._json(200, {"picks": [], "signedIn": False})
        xid = self._xid(user)
        if not xid:
            return self._json(200, {"picks": [], "signedIn": True})
        try:
            params = {"xid": f"eq.{xid}", "select": "picks"}
            if TABLE_MISSING:
                # a deployment whose table was never created must say so once, not
                # retry PostgREST for every visitor that lands on the board
                return self._json(503, {"error": TABLE_MISSING, "storage": False})
            rows = store._call(TABLE, params=params) or []
        except store.StorageError as e:
            msg = str(e)
            if "42P01" in msg or "does not exist" in msg.lower():
                TABLE_MISSING = f"table public.{TABLE} is missing - run db/drafts.sql"
                return self._json(503, {"error": TABLE_MISSING, "storage": False})
            return self._json(503, {"error": msg, "storage": False})
        picks = []
        if rows:
            picks = [p for p in _as_list(rows[0].get("picks")) if isinstance(p, dict)]
        return self._json(200, {"picks": picks, "signedIn": True,
                                "handle": user.get("handle")})

    def do_POST(self):
        global TABLE_MISSING
        user = self._user()
        if not user:
            return self._json(401, {"error": "sign in with X to keep a lineup"})
        xid = self._xid(user)
        handle = str(user.get("handle") or "")
        if not xid:
            return self._json(401, {"error": "session has no account id"})
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY:
            return self._json(400, {"error": "body too large"})
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            picks = _picks_of(body)
        except Exception as e:  # noqa: BLE001 - a bad body is the client's problem
            return self._json(400, {"error": f"bad body: {e}"})
        # picks goes out as the array itself. Passing json.dumps(...) here sends a
        # JSON *string*, which Postgres stores as a jsonb scalar and then rejects
        # with 22023 "cannot get array length of a scalar" on the length check.
        row = {"xid": xid, "handle": handle, "picks": picks,
               "updated_at": datetime.now(timezone.utc).isoformat()}
        try:
            store._call(
                TABLE,
                method="POST",
                payload=[row],
                prefer="resolution=merge-duplicates,return=minimal",
                params={"on_conflict": "xid"},
            )
        except store.StorageError as e:
            msg = str(e)
            if "42P01" in msg or "does not exist" in msg.lower():
                msg = f"table public.{TABLE} is missing - run db/drafts.sql"
            return self._json(503, {"error": msg, "storage": False})
        return self._json(200, {"picks": picks, "saved": True})

    def do_DELETE(self):
        user = self._user()
        if not user:
            return self._json(401, {"error": "not signed in"})
        xid = self._xid(user)
        try:
            store._call(TABLE, method="DELETE", params={"xid": f"eq.{xid}"})
        except store.StorageError as e:
            return self._json(503, {"error": str(e), "storage": False})
        return self._json(200, {"picks": [], "saved": True})
