#!/usr/bin/env python3
"""Verify that the collector actually recorded the leaderboard slot it should have.

Runs after the cron snapshot. GitHub Actions schedulers are not exact, so a run
can be delayed or dropped; without this check a red workflow is the only signal
and nobody notices a gap. This prints the last slots it has, the slot it expects
to be recording now, and exits non-zero when a slot inside the retention window
has no snapshot for the official source.

The anchor is the NEWEST `asOf` Motion has actually published, not the wall clock.
Motion does not always have a new window out when our cron fires (18:44 still
returned asOf 12:00), and demanding a snapshot for a window the source has not
published is a gap that could never have been filled. Wall clock is only used as
an upper bound: a slot after the newest published window is not owed.

Two more things are explicitly NOT gaps, because crying wolf here trains people to
ignore the red build:
  * slots before the first snapshot we ever took AND before COLLECTING_SINCE -
    nothing exists to backfill from, and inventing a past window is worse;
  * slots whose window is still open on the clock - the cron is 4-hourly, so a run
    at 16:05 is inside the 16:00 window and has not failed to record it yet.

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
# expect slots on weekdays, and only from the moment our own collection actually
# began - nothing before that can be backfilled, and we do not invent it.
OFFICIAL = "motion-official"

# When this collector started running on a schedule, taken from the first run that
# could have fired at all. The workflow only triggers `schedule` from the default
# branch, so the 00:00Z window on 2026-11-16 had no run while `main` was default:
# it is a real hole in the record, but not one any later run could have filled.
# Reading it as a live gap would make every green build impossible, so the owed
# range starts here instead of at the first snapshot we happen to hold.
COLLECTING_SINCE = datetime(2026, 11, 16, 6, 0, tzinfo=timezone.utc)

# Motion publishes a leaderboard window a minute or two after it opens. Before
# this much of a window has passed, "no snapshot for it yet" is normal, not a gap.
GRACE = timedelta(minutes=20)


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


def expected_slots(now: datetime, first: datetime, latest_published: datetime | None = None) -> list[datetime]:
    """Slots that must exist: weekday, 4-hour aligned, from the first window this
    collector could have recorded up to the newest window the source published.

    `first` is the earliest slot we are accountable for; the caller passes the
    max of our first snapshot's slot and COLLECTING_SINCE, so a window that closed
    before the workflow ever ran on a schedule is history, not a standing gap.

    `latest_published` is Motion's own `asOf` from the snapshot just taken. It is
    the hard ceiling: a slot the source has not published cannot be missing, or
    every run before Motion rolls the window reads as a gap.
    """
    slots = []
    start = slot_of(first)
    end = slot_of(latest_published) if latest_published else slot_of(now)
    # Never demand a window the clock has not opened yet, even if a malformed
    # asOf claims a future window.
    end = min(end, slot_of(now))
    cursor = start
    while cursor <= end:
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
    oldest = min(parse_iso(s["asOf"]) for s in official)
    # Accountability starts when we could first have recorded a window, not when a
    # snapshot happened to land: a slot from before the workflow ran on a schedule
    # is not something a later run can repair.
    first = max(oldest, COLLECTING_SINCE)
    # The newest window the source has actually published, from the snapshot just
    # recorded. Without it the ceiling would be the wall clock, which Motion does
    # not follow - it kept serving asOf 12:00 at 18:44.
    latest_published = max(parse_iso(s["asOf"]) for s in official)
    want = expected_slots(now, first, latest_published)

    print(f"snapshots on record : {len(official)}")
    print(f"windows covered     : {len(have)}")
    print(f"oldest snapshot     : {oldest.isoformat()}")
    print(f"accountable since   : {first.isoformat()} (collector start)")
    print(f"newest published    : {latest_published.isoformat()} (the source's own asOf)")
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
