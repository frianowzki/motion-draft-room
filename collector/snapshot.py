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

# Source of truth: Motion's own leaderboard JSON (checked 2026-11-15, no auth).
# It carries asOf/capturedAt/baselineCapturedAt + all 79 rows, same shape as the
# aggregator, but straight from the game — so we do not depend on a third party.
# Note: rows have no `handle`, only `id`/`name`/`position`/`delta`/`isNew`.
PRIMARY_URL = "https://leaderboard.motion.game/api/leaderboard"
# Secondary: MotionRadar aggregator, which additionally exposes `handle` + stats.
SECONDARY_URL = "https://motionradar.vercel.app/api/leaderboard"
# Last resort: the HTML page (data is JS-rendered, so this rarely yields rows).
OFFICIAL_URL = "https://leaderboard.motion.game/"


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
                "handle": r.get("handle"),  # official API omits this
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


def fetch_secondary() -> dict:
    """MotionRadar aggregator -> normalized snapshot (adds handle + stats)."""
    payload = json.loads(http_get(SECONDARY_URL))
    data = payload.get("data") or {}
    rows_raw = data.get("rows") or []
    if not rows_raw:
        raise RuntimeError("aggregator returned zero rows")

    by_name = {r.get("name"): r for r in rows_raw}
    try:
        official = {r["name"]: r for r in fetch_primary()["rows"]}
    except Exception:
        official = {}

    rows = []
    for name, r in by_name.items():
        off = official.get(name, {})
        rows.append(
            {
                "id": r.get("id") or off.get("id"),
                "name": name,
                "handle": r.get("handle"),
                "position": int(off.get("position") or r.get("position") or 0),
                "delta": int(off.get("delta") if off else (r.get("delta") or 0)),
                "isNew": bool(r.get("isNew")),
            }
        )
    rows.sort(key=lambda x: x["position"])

    return {
        "source": "motionradar",
        "asOf": data.get("asOf"),
        "sourceCapturedAt": data.get("capturedAt"),
        "baselineCapturedAt": data.get("baselineCapturedAt"),
        "stats": payload.get("stats") or {},
        "rows": rows,
    }



def parse_leaderboard_html(html: str) -> list[dict]:
    """Fallback parser for the official leaderboard page.

    The page renders rank, name and rank-change in static markup, so a regex pass
    is enough. Deliberately conservative: if we cannot find at least 20 creators
    we treat the scrape as failed rather than write a half-empty snapshot.
    """
    import re

    rows: list[dict] = []
    # Each row: rank number, optional pfp image (id embedded), name, rank change.
    pattern = re.compile(
        r"(?P<pos>\d{1,3})\s*(?:_?!\[Image \d+\]\([^)]*?/pfp/(?P<id>[0-9a-f-]{36})\.jpg\)_?\s*)?"
        r"(?P<name>[A-Za-z0-9][^<\n*]{1,40}?)\s*\*\*(?P<delta>-?\d+)\*\*"
    )
    for m in pattern.finditer(html):
        name = m.group("name").strip().rstrip("_").strip()
        if not name or name.lower().startswith(("rank change", "image")):
            continue
        rows.append(
            {
                "id": m.group("id"),
                "name": name,
                "handle": None,
                "position": int(m.group("pos")),
                "delta": int(m.group("delta")),
                "isNew": False,
            }
        )

    seen: set[int] = set()
    unique = []
    for r in rows:
        if r["position"] in seen:
            continue
        seen.add(r["position"])
        unique.append(r)
    unique.sort(key=lambda x: x["position"])

    if len(unique) < 20:
        raise RuntimeError(f"official scrape yielded only {len(unique)} rows; refusing to save")
    return unique


def fetch_fallback() -> dict:
    html = http_get(OFFICIAL_URL)
    rows = parse_leaderboard_html(html)
    return {
        "source": "official-scrape",
        "asOf": None,
        "sourceCapturedAt": None,
        "baselineCapturedAt": None,
        "stats": {},
        "rows": rows,
    }


def collect() -> dict:
    errors = []
    for name, fn in (("motion-official", fetch_primary), ("motionradar", fetch_secondary), ("html", fetch_fallback)):
        try:
            snap = fn()
            if errors:
                snap["fallbackReason"] = "; ".join(errors)
            return snap
        except Exception as exc:  # try the next source
            errors.append(f"{name}: {exc}")
    raise RuntimeError("all sources failed -> " + " | ".join(errors))


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
