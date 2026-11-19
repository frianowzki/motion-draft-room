#!/usr/bin/env python3
"""Verify that the collector actually recorded the leaderboard slot it should have.

Runs after the cron snapshot. GitHub Actions schedulers are not exact, so a run
can be delayed or dropped; without this check a red workflow is the only signal
and nobody notices a gap. This prints the last slots it has, the slot it expects
to be recording now, and exits non-zero when a slot inside the retention window
has no snapshot for the official source.

Two things are explicitly NOT gaps, because crying wolf here trains people to ignore
the red build:
  * slots before the first snapshot we ever took - nothing exists to backfill from,
    and inventing a past window is worse than a short history;
  * slots whose window is still open - the cron is 4-hourly, so a run at 18:21 is
    still inside the 16:00 window and has not failed to record it yet.

Exit codes:
  0  every expected slot is present (or the only gaps predate the current record)
  1  the collector has never produced a layout it can verify
  2  the collector is running against a source other than motion-official

A gap in the middle of the record is printed loudly but does NOT fail the job.
Those windows are already gone - the board only ever serves the slot it is on, so
nothing can backfill them - and a job that stays red forever teaches everyone to
ignore the red. Only a broken collector is worth a red build.

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


def expected_slots(now: datetime, first: datetime) -> list[datetime]:
    """Slots that must exist: weekday, 4-hour aligned, from the first real
    snapshot's own slot up to the last slot that has fully closed.

    Only CLOSED windows are ever owed, with one exception: if we are still
    inside the window `now` belongs to and it opened more than 20 minutes ago,
    that window may be owed - the cron fires at :07, so a run at 18:21 is
    inside the 16:00 window and should already have recorded it. A run at
    16:05 is also inside 16:00 but too early to call it missing.

    The deadline for a slot is therefore the end of its own window, which is
    what `slot_of(now)` gives; slots strictly before it are always owed.
    """
    slots = []
    cursor = slot_of(first)
    open_slot = slot_of(now)
    while cursor < open_slot:
        if cursor.weekday() < 5:  # Mon-Fri
            slots.append(cursor)
        cursor += timedelta(hours=SLOT_HOURS)
    # Inside the current window: owed once its data has had 20 minutes to land.
    if open_slot >= slot_of(first) and open_slot.weekday() < 5 and now - open_slot >= GRACE:
        slots.append(open_slot)
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
    print(f"open window         : {slot_of(now).isoformat()} (owed once {GRACE.seconds // 60}m in)")
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

    # A gap this run did not cause is history, not a failure. The board serves only
    # its current slot, so a window that has already closed can never be filled in.
    # Staying red for it hides the one case worth a red build: a run right now that
    # came back empty while its own window was already published.
    this_window = slot_of(now)
    failed_now = this_window in missing and now - this_window >= GRACE
    if not failed_now:
        last = max(official, key=lambda s: s["asOf"])
        print(f"\nOK for this run - {len(missing)} older window(s) are unrecoverable, "
              f"nothing to backfill. latest asOf {last['asOf']}")
        return 0

    print(f"\nThis run did not record {this_window.isoformat()} {GRACE.seconds // 60} "
          f"minutes into the window it belongs to. Check the Actions tab:")
    print("  https://github.com/frianowzki/motion-draft-room/actions/workflows/collect.yml")
    return 1


if __name__ == "__main__":
    sys.exit(main())
