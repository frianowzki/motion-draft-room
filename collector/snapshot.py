#!/usr/bin/env python3
"""Snapshot the Motion creator leaderboard into data/snapshots/.

Why: MotionRadar's API only describes the LAST 4 hours (delta vs a 4h baseline).
Anything longer — acceleration, 24h/72h trend, volatility — has to be accumulated
on our side. Every run appends one snapshot; nothing is ever rewritten.

Usage:
    python3 collector/snapshot.py            # fetch, write, print summary
    python3 collector/snapshot.py --dry-run  # fetch, print, write nothing
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAP_DIR = ROOT / "data" / "snapshots"

# Source of truth: Motion's own leaderboard JSON (unauthenticated, checked 2026-11-15).
# Fields: asOf, capturedAt, baselineCapturedAt, history ("enabled"), rows[] of
# {id, name, position, delta, isNew}. No `handle`, no creator Score — by design we
# use nothing but this endpoint, so every number is traceable to Motion itself.
PRIMARY_URL = "https://leaderboard.motion.game/api/leaderboard"


UA = "motion-draft-room/0.1 (+collector; contact via repo)"
TIMEOUT = 30
RETRIES = 3


def http_get(url: str) -> str:
    last: Exception | None = None
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json,text/html"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.read().decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:  # pragma: no cover - network
            last = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"GET {url} failed after {RETRIES} attempts: {last}")


def fetch_primary() -> dict:
    """Official Motion leaderboard JSON -> normalized snapshot."""
    payload = json.loads(http_get(PRIMARY_URL))
    rows_raw = payload.get("rows") or []
    if not rows_raw:
        raise RuntimeError("official API returned zero rows")

    rows = []
    for r in rows_raw:
        rows.append(
            {
                "id": r.get("id"),
                "name": r.get("name"),
                "handle": None,  # official API publishes no X handle
                "position": int(r.get("position") or 0),
                "delta": int(r.get("delta") or 0),
                "isNew": bool(r.get("isNew")),
            }
        )
    rows.sort(key=lambda x: x["position"])

    return {
        "source": "motion-official",
        "asOf": payload.get("asOf"),
        "sourceCapturedAt": payload.get("capturedAt"),
        "baselineCapturedAt": payload.get("baselineCapturedAt"),
        "stats": payload.get("stats") or {},
        "rows": rows,
    }


def collect() -> dict:
    """Fetch from Motion's official endpoint only.

    Deliberately no third-party fallback: a snapshot from anywhere else would not be
    the same measurement, so a failed fetch must fail loudly and the workflow goes
    red instead of quietly recording a different source.
    """
    return fetch_primary()


def summarize(snap: dict) -> str:
    rows = snap["rows"]
    gainers = sorted([r for r in rows if r["delta"] > 0], key=lambda r: -r["delta"])[:5]
    losers = sorted([r for r in rows if r["delta"] < 0], key=lambda r: r["delta"])[:3]
    lines = [
        f"source     : {snap['source']}" + (f" (fallback: {snap.get('fallbackReason')})" if snap.get("fallbackReason") else ""),
        f"asOf       : {snap.get('asOf')}",
        f"creators   : {len(rows)}",
        f"gainers    : {len([r for r in rows if r['delta'] > 0])} | losers: {len([r for r in rows if r['delta'] < 0])}",
        "top gainers: " + ", ".join(f"{r['name']} Δ{r['delta']:+}" for r in gainers),
        "top drops  : " + ", ".join(f"{r['name']} Δ{r['delta']:+}" for r in losers),
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    snap = collect()
    now = datetime.now(timezone.utc)
    snap["collectedAt"] = now.isoformat().replace("+00:00", "Z")
    # Slot key: the 4-hour bucket the snapshot belongs to (00,04,08,12,16,20 UTC).
    snap["slot"] = now.strftime("%Y-%m-%dT%H")

    print(summarize(snap))

    if args.dry_run:
        print("\n[dry-run] nothing written")
        return 0

    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    out = SNAP_DIR / f"{stamp}.json"
    out.write_text(json.dumps(snap, indent=1) + "\n")
    print(f"\nwrote {out.relative_to(ROOT)}")

    latest = ROOT / "data" / "latest.json"
    latest.write_text(json.dumps(snap, indent=1) + "\n")
    print(f"wrote {latest.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
