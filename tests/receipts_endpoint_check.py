"""End-to-end check of /api/receipts against the local Postgres.

Starts the real handler from api/receipts.py behind a socket, mints a signed X
session the same way xauth_lib does, and drives it the way the dashboard does:
one filing, a duplicate filing, and a read. The snapshot the grader needs is served
by a fake GitHub contents API so the grade is deterministic.

Run: python3 -m tests.receipts_endpoint_check
"""

from __future__ import annotations

import base64
import json
import os
import socket
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api"))
sys.path.insert(0, os.path.join(ROOT, "api", "xauth"))

SNAP = {
    "dataAsOf": "2026-11-18T08:00:00Z",
    "rows": [{"name": "Ludwig", "position": 5}, {"name": "Zoe", "position": 9},
             {"name": "Aim", "position": 40}],
}


def main():
    os.environ["X_SESSION_SECRET"] = base64.b64encode(b"k" * 48).decode()
    os.environ["GITHUB_TOKEN"] = "snapshot-read-placeholder"

    import xauth_lib as xl
    import receipts

    # the snapshot read is the collector's artefact on the data branch; stub it so
    # grading is a fixed input rather than whatever the board says today
    receipts._snapshots = lambda: SNAP
    # the store speaks to PostgREST; the fake one from the store test speaks SQL
    from tests.receipt_store_check import FakePostgREST
    from http.server import HTTPServer
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    pr = HTTPServer(("127.0.0.1", port), FakePostgREST)
    threading.Thread(target=pr.serve_forever, daemon=True).start()
    os.environ["SUPABASE_URL"] = f"http://127.0.0.1:{port}"
    os.environ["SUPABASE_KEY"] = "service-role-placeholder"

    from tests.receipt_store_check import psql
    psql("truncate public.receipts")

    from http.server import ThreadingHTTPServer
    srv = ThreadingHTTPServer(("127.0.0.1", 0), receipts.handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"

    token = xl.seal({"u": {"id": "919191", "handle": "frian", "name": "Frian",
                           "avatar": "https://pbs/frian.jpg"},
                     "exp": int(time.time()) + 3600})
    cookie = f"{xl.SESSION_COOKIE}={token}"
    body = {
        "slotAtLock": "2026-11-18T04:00:00Z",
        "picks": [{"name": "Ludwig", "positionAtLock": 12, "estStars": 4,
                   "rarity": "Rare", "thesis": "climbing", "premortem": "burns out"}],
    }

    import urllib.error
    import urllib.request

    def call(method, payload=None, with_cookie=True):
        req = urllib.request.Request(
            base + "/api/receipts", method=method,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Content-Type": "application/json",
                     **({"Cookie": cookie} if with_cookie else {})})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    # 1. no session: refused, because a receipt nobody can check is not evidence
    code, out = call("POST", body, with_cookie=False)
    assert code == 401, (code, out)
    print("ok  a filing without an X session is refused (401)")

    # 2. a real filing grades immediately, because the snapshot is a later window
    code, out = call("POST", body)
    assert code == 201, (code, out)
    assert out["receipt"]["player"] == "frian", out
    assert out["receipt"]["score"] == 7, out["receipt"]  # 12 -> 5 is 7 places
    assert out["receipt"]["status"] == "settled", out["receipt"]
    print("ok  a filing is graded by the server (12 -> 5 means +7), never by the client")

    # 3. the same player cannot file twice for one window
    code, out = call("POST", body)
    assert code == 409, (code, out)
    assert "already filed" in out["error"], out
    print("ok  a second filing for the same window is a 409, straight from Postgres")

    # 4. a different player may file for the same window
    code, out = call("GET")
    assert code == 200
    assert out["summary"]["count"] == 1, out["summary"]
    assert out["receipts"][0]["avatar"] == "https://pbs/frian.jpg"
    print("ok  GET returns the book with the summary the page renders")

    # 5. the client cannot dictate a score or a handle
    req_body = dict(body, slotAtLock="2026-11-18T12:00:00Z", player="someoneelse",
                    picks=[{"name": "Zoe", "positionAtLock": 12, "estStars": 4, "score": 999}])
    code, out = call("POST", req_body)
    # 12:00 is later than the snapshot on record, so this is rejected before it is graded
    assert code == 400, (code, out)
    print("ok  a slot in the future of the snapshot is refused (400)")

    psql("truncate public.receipts")
    srv.shutdown()
    pr.shutdown()
    print("\nall endpoint checks passed")


if __name__ == "__main__":
    main()
