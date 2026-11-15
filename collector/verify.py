#!/usr/bin/env python3
"""Verify that the collector actually recorded the leaderboard slot it should have.

Runs after the cron snapshot. GitHub Actions schedulers are not exact, so a run
can be delayed or dropped; without this check a red workflow is the only signal
and nobody notices a gap. This prints the last slots it has, the slot it expects
to be recording now, and exits non-zero when a slot inside the retention window
has no snapshot for the official source.

Exit codes:
  0  every expected slot is present
  1  a slot is missing (gap in the record)
  2  the collector is running against a source other than motion-official

Usage:
    python3 collector/verify.py
    python3 collector/verify.py --at 2026-11-16T04:10:00Z   # pretend now
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP_DIR = ROOT / "data" / "snapshots"

SLOT_HOURS = 4
# Leaderboard scores update every 4 hours Mon-Fri (docs.motion.game). We only
# expect slots on weekdays, and only from the moment our first real snapshot
# exists - nothing before that can be backfilled, and we do not invent it.
OFFICIAL = "motion-official"


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_snapshots() -> list[dict]:
    out = []
    for path in sorted(SNAP_DIR.glob("*.json")):
        try:
            snap = json.loads(path.read_text())
        except Exception:
            continue
        if snap.get("asOf"):
            snap["_file"] = path.name
            out.append(snap)
    return out


def slot_of(when: datetime) -> datetime:
    return when.replace(minute=0, second=0, microsecond=0) - timedelta(hours=when.hour % SLOT_HOURS)


def expected_slots(now: datetime, first: datetime) -> list[datetime]:
    """Slots that must exist: weekday, 4-hour aligned, from the first real
    snapshot up to the most recent slot that has already settled."""
    slots = []
    cursor = slot_of(first)
    # A slot's data lands a minute or two after the boundary; give it 20 minutes
    # before treating it as owed.
    limit = now - timedelta(minutes=20)
    while cursor <= limit:
        if cursor.weekday() < 5:  # Mon-Fri
            slots.append(cursor)
        cursor += timedelta(hours=SLOT_HOURS)
    return slots


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--at", help="ISO timestamp to verify against (default: now)")
    args = ap.parse_args()

    now = parse_iso(args.at) if args.at else datetime.now(timezone.utc)
    snaps = load_snapshots()
    if not snaps:
        print("no snapshots at all - the collector has never succeeded")
        return 1

    bad = [s for s in snaps if s.get("source") != OFFICIAL]
    if bad:
        print(f"{len(bad)} snapshot(s) from a source other than {OFFICIAL}:")
        for s in bad:
            print(f"  {s['_file']} source={s.get('source')} asOf={s.get('asOf')}")
        return 2

    official = [s for s in snaps if s.get("source") == OFFICIAL]
    have = {slot_of(parse_iso(s["asOf"])).isoformat() for s in official}
    first = min(parse_iso(s["asOf"]) for s in official)
    want = expected_slots(now, first)

    print(f"snapshots on record : {len(official)}")
    print(f"windows covered     : {len(have)}")
    print(f"first slot          : {first.isoformat()}")
    print(f"verifying at        : {now.isoformat()}")
    print(f"slots expected      : {len(want)}")

    missing = [s for s in want if s.isoformat() not in have]
    if not missing:
        last = max(official, key=lambda s: s["asOf"])
        print(f"\nOK - every weekday slot since {first.isoformat()} is recorded. "
              f"latest asOf {last['asOf']}")
        return 0

    print(f"\nMISSING {len(missing)} slot(s):")
    for slot in missing:
        print(f"  {slot.isoformat()}  (leaderboard window, no snapshot)")
    print("\nThe cron did not record a window it should have. Check the Actions tab:")
    print("  https://github.com/frianowzki/motion-draft-room/actions/workflows/collect.yml")
    return 1


if __name__ == "__main__":
    sys.exit(main())
