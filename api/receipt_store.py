"""Receipt storage, on Supabase Postgres.

Why this exists: the book used to live in data/receipts.json on a git branch, so a
receipt was a read-modify-write of one file through the GitHub contents API. Two
people filing at the same moment meant one of them lost the write, the whole book
had to be fetched and base64-decoded to answer a single GET, and there was nowhere
to put a uniqueness rule except a loop in Python. Postgres answers all three: an
INSERT is a write, a SELECT is a read, and `unique (xid, slot_at_lock)` is a
constraint the database enforces whether or not this file is correct.

Deliberately not an ORM and not a Supabase client library: a Vercel Python function
gets one directory and requirements.txt, and these are three SQL statements. The
PostgREST HTTP API is what supabase-js talks to, so this speaks the same protocol
with urllib and lends no extra dependency weight.

Row shape is kept identical to the old JSON entries, so /api/receipts answers the
same shape it always did and the dashboard needs no knowledge of the move.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

TABLE = "receipts"
# The GET endpoint returns the newest slice of the book; reading all of it to show
# 60 was only ever free because it was one file.
PAGE = 400


def _env(name):
    return (os.environ.get(name) or "").strip()


def url():
    return _env("SUPABASE_URL").rstrip("/")


def key():
    # Service role: this endpoint writes on behalf of a signed-in player, and row
    # level security has no notion of X sessions. The key never leaves the server.
    return _env("SUPABASE_KEY") or _env("SUPABASE_SERVICE_KEY")


def configured():
    return bool(url() and key())


class StorageError(RuntimeError):
    """A failed round trip to Postgres, with the status X/PostgREST gave."""

    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


class Duplicate(Exception):
    """This player already filed for this slot. Postgres said so, not us."""


def _call(path, method="GET", payload=None, prefer=None, params=None):
    if not configured():
        raise StorageError("SUPABASE_URL / SUPABASE_KEY are not set on this deployment")
    query = ("?" + urllib.parse.urlencode(params)) if params else ""
    headers = {
        "apikey": key(),
        "Authorization": f"Bearer {key()}",
        "Accept": "application/json",
        "User-Agent": "motion-draft-room",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if prefer:
        headers["Prefer"] = prefer
    req = urllib.request.Request(
        f"{url()}/rest/v1/{path}{query}",
        method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        body = e.read()[:400].decode(errors="replace")
        # 409 is PostgREST's unique-violation answer once `Prefer: return=representation`
        # is asked for; Postgres codes 23505 travel in the body when it is raised by a
        # constraint on a normal insert.
        if e.code == 409 or "23505" in body:
            raise Duplicate(body)
        raise StorageError(f"supabase {e.code}: {body}", e.code) from None
    except Exception as e:  # noqa: BLE001 - surface it as storage, never as a crash
        raise StorageError(f"supabase unreachable: {e}") from None
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _row_in(r):
    """JSON receipt -> row. Keeps the whole envelope so the shape survives a move."""
    return {
        "player": str(r.get("player") or "").lstrip("@")[:15],
        "xid": str(r.get("xid") or ""),
        "name": str(r.get("name") or "")[:40],
        "avatar": str(r.get("avatar") or "")[:400],
        "slot_at_lock": str(r.get("slotAtLock") or ""),
        "picks": r.get("picks") or [],
        "status": str(r.get("status") or "pending"),
        "score": r.get("score"),
        "locked_at": r.get("lockedAt") or None,
        "settled_at": r.get("settledAt"),
        "graded_as_of": r.get("gradedAsOf"),
    }


def _row_out(row):
    """Row -> the JSON shape /api/receipts has always returned.

    Nulls are dropped rather than emitted: the page renders `score: null` as a
    pending receipt through a `== null` check, and an absent key behaves the same,
    while an explicit null in every field would bloat every response.
    """
    out = {
        "player": row.get("player") or "",
        "xid": row.get("xid") or "",
        "name": row.get("name") or "",
        "avatar": row.get("avatar") or "",
        "slotAtLock": row.get("slot_at_lock") or "",
        "picks": row.get("picks") or [],
        "status": row.get("status") or "pending",
        "lockedAt": row.get("locked_at") or "",
    }
    if row.get("score") is not None:
        out["score"] = int(row["score"])
    if row.get("settled_at"):
        out["settledAt"] = row["settled_at"]
    if row.get("graded_as_of"):
        out["gradedAsOf"] = row["graded_as_of"]
    return out


def read(limit=PAGE):
    """Newest first. A missing table is a broken deployment, not an empty book."""
    rows = _call(
        TABLE,
        params={
            "select": "player,xid,name,avatar,slot_at_lock,picks,status,score,locked_at,settled_at,graded_as_of",
            "order": "locked_at.desc",
            "limit": str(max(1, min(int(limit), PAGE))),
        },
    )
    return [_row_out(r) for r in (rows or [])]


def insert(receipt):
    """One write, and the uniqueness rule is the database's.

    `on_conflict` is not used: a conflict must be a 409 to the player, not a silent
    overwrite of the lineup they filed an hour ago.
    """
    rows = _call(TABLE, method="POST", payload=[_row_in(receipt)],
                 prefer="return=representation")
    if isinstance(rows, list) and rows:
        return _row_out(rows[0])
    return dict(receipt)


def upsert(receipt):
    """Regrading an existing receipt: same key, new score. Nothing is replaced but
    the grading fields, which is all _settle() ever writes back."""
    rows = _call(
        TABLE,
        method="POST",
        payload=[_row_in(receipt)],
        prefer="resolution=merge-duplicates,return=representation",
        params={"on_conflict": "xid,slot_at_lock"},
    )
    if isinstance(rows, list) and rows:
        return _row_out(rows[0])
    return dict(receipt)


def regrade(changes):
    """Write back receipts that a later snapshot has just graded.

    A no-op on an empty list: a read-only page view must not cost a write.
    """
    if not changes:
        return 0
    _call(TABLE, method="POST",
          payload=[_row_in(r) for r in changes],
          prefer="resolution=merge-duplicates,return=minimal",
          params={"on_conflict": "xid,slot_at_lock"})
    return len(changes)
