"""Prove the Supabase receipt store against a real Postgres.

There is no PostgREST here, so this does two things:

1. SQL level — the schema's guarantees, run through psql against a live Postgres 17:
   the unique constraint, the check constraints, jsonb round-trip, RLS on.
2. HTTP level — receipt_store speaks PostgREST, so a small fake PostgREST translates
   its three calls into real SQL. That exercises the code the deployment will run
   (URL building, headers, payload shape, 409 -> Duplicate, row<->JSON mapping),
   just against localhost instead of Supabase.

Run: python3 -m tests.receipt_store_check
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api"))

DATA = "/data/home/.hermes/cache/scratch/pgtest"
PSQL = ["/usr/lib/postgresql/17/bin/psql", "-h", DATA, "-p", "55432", "-U", "postgres", "-d", "draftroom"]
COLS = ("xid,slot_at_lock,player,name,avatar,picks,status,score,locked_at,settled_at,graded_as_of")


def psql(sql, want_fail=False):
    p = subprocess.run(PSQL + ["-v", "ON_ERROR_STOP=1", "-At", "-c", sql],
                       capture_output=True, text=True)
    if want_fail:
        assert p.returncode != 0, f"expected this to be rejected: {sql}"
        return p.stderr
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def sql_row(row):
    """A receipt_store row dict -> a VALUES tuple, with jsonb cast."""
    pick = json.dumps(row["picks"]).replace("'", "''")
    def q(v):
        if v is None:
            return "null"
        return "'" + str(v).replace("'", "''") + "'"
    locked = q(row.get("locked_at")) if row.get("locked_at") else "now()"
    return ("(" + ", ".join([q(row["xid"]), q(row["slot_at_lock"]), q(row["player"]),
                             q(row.get("name") or ""), q(row.get("avatar") or ""),
                             "'" + pick + "'::jsonb", q(row.get("status") or "pending"),
                             "null" if row.get("score") is None else str(int(row["score"])),
                             locked, q(row.get("settled_at")), q(row.get("graded_as_of"))]) + ")")


class FakePostgREST(BaseHTTPRequestHandler):
    """Just enough PostgREST for receipt_store: GET a table, POST an array."""

    def log_message(self, format, *args):  # noqa: A002 - base class name
        pass

    def _rows_out(self):
        raw = psql(f"select json_agg(t) from (select {COLS} from public.receipts "
                   f"order by locked_at desc) t")
        return json.loads(raw) if raw else []

    def do_GET(self):
        if self.path.startswith("/rest/v1/receipts"):
            body = json.dumps(self._rows_out()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        rows = json.loads(self.rfile.read(n))
        prefer = self.headers.get("Prefer") or ""
        merge = "resolution=merge-duplicates" in prefer
        err = None
        for row in rows:
            vals = sql_row(row)
            if merge:
                sql = (
                    f"insert into public.receipts ({COLS}) values {vals} "
                    f"on conflict (xid, slot_at_lock) do update set "
                    f"status=excluded.status, score=excluded.score, picks=excluded.picks, "
                    f"settled_at=excluded.settled_at, graded_as_of=excluded.graded_as_of"
                )
            else:
                sql = f"insert into public.receipts ({COLS}) values {vals}"
            p = subprocess.run(PSQL + ["-v", "ON_ERROR_STOP=1", "-At", "-c", sql],
                               capture_output=True, text=True)
            if p.returncode != 0:
                err = p.stderr
                break
        if err:
            body = json.dumps({"code": "23505" if "unique constraint" in err else "23514",
                               "message": err.strip()}).encode()
            self.send_response(409)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        out = b"[]" if "return=minimal" in prefer else json.dumps(self._rows_out()).encode()
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)


def main():
    psql("truncate public.receipts")
    srv = HTTPServer(("127.0.0.1", 0), FakePostgREST)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    os.environ["SUPABASE_URL"] = f"http://127.0.0.1:{srv.server_port}"
    os.environ["SUPABASE_KEY"] = "service-role-placeholder"
    import receipt_store as store

    receipt = {
        "player": "frian", "xid": "111", "name": "Frian", "avatar": "https://x/a.jpg",
        "slotAtLock": "2026-11-18T04:00:00Z",
        "picks": [{"name": "Ludwig", "positionAtLock": 12, "estStars": 4,
                   "rarity": "Rare", "thesis": "climbing", "premortem": "burns out"}],
        "status": "pending",
        "lockedAt": "2026-11-18T05:00:00Z",
    }

    # 1. insert then read back: the JSON envelope survives the round trip
    saved = store.insert(receipt)
    assert saved["player"] == "frian" and saved["status"] == "pending", saved
    back = store.read()
    assert len(back) == 1, back
    assert back[0]["slotAtLock"] == "2026-11-18T04:00:00Z", back[0]
    assert back[0]["picks"][0]["premortem"] == "burns out", back[0]["picks"]
    assert back[0]["picks"][0]["positionAtLock"] == 12, "camelCase keys must survive"
    assert "score" not in back[0], "an ungraded receipt must not carry a score key"
    print("ok  insert + read: envelope, camelCase picks, no null score")

    # 2. the database, not the endpoint, refuses a second lineup for the same slot
    try:
        store.insert(dict(receipt, picks=[{"name": "Zoe", "positionAtLock": 3, "estStars": 3}]))
    except store.Duplicate:
        print("ok  a second lineup for the same slot is refused by the unique constraint")
    else:
        raise AssertionError("duplicate was accepted")

    # 3. a different slot is a different lineup
    store.insert(dict(receipt, slotAtLock="2026-11-18T08:00:00Z",
                      picks=[{"name": "Zoe", "positionAtLock": 3, "estStars": 3}]))
    assert len(store.read()) == 2
    print("ok  the same player may file again for a later window")

    # 4. regrade writes the grade back and read() sees it
    graded = dict(back[0], status="settled", score=7, settledAt="2026-11-18T08:00:00Z",
                  gradedAsOf="2026-11-18T08:00:00Z")
    assert store.regrade([graded]) == 1
    rows = {r["slotAtLock"]: r for r in store.read()}
    assert rows["2026-11-18T04:00:00Z"]["score"] == 7, rows
    assert rows["2026-11-18T04:00:00Z"]["status"] == "settled"
    print("ok  regrade: same key, new score, nothing duplicated")

    # 5. empty regrade costs no write
    assert store.regrade([]) == 0
    print("ok  an empty regrade is a no-op")

    # 6. the check constraints bite even if the endpoint is bypassed
    psql(f"insert into public.receipts ({COLS}) values {sql_row({
        'xid': '333', 'slot_at_lock': 's', 'player': 'x', 'picks': [],
        'status': 'pending'})}", want_fail=True)
    psql("insert into public.receipts (xid,slot_at_lock,player,status) "
         "values ('444','s','x','graded')", want_fail=True)
    print("ok  empty picks and an unknown status are rejected by the table")

    # 7. RLS is on: the public anon key cannot touch the table at all
    rls = psql("select relrowsecurity from pg_class where relname='receipts'")
    assert rls == "t", rls
    print("ok  row level security is enabled (no policies: service role only)")

    # 8. ordering is newest-locked-first
    order = [r["slotAtLock"] for r in store.read()]
    assert order == sorted(order, reverse=True), order
    print("ok  the book reads newest-first")

    srv.shutdown()
    print("\nall store checks passed")


if __name__ == "__main__":
    main()
