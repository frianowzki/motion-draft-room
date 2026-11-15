#!/usr/bin/env python3
"""Turn accumulated snapshots into per-creator signals + a weekly forecast.

Reads data/snapshots/*.json (at least 1, ideally 3+ for acceleration) and writes
data/signals.json.

Signal definitions (all derived from PUBLIC data only — positions and rank deltas,
which Motion publishes every 4 hours; nothing here is insider information):

  d4h          current delta, as published by Motion (rank change vs 4h baseline)
  d24h         position change over ~24h of our own snapshots
  d72h         position change over ~72h of our own snapshots
  acceleration d4h now minus the mean d4h of the previous snapshots
  volatility   stdev of d4h across our snapshots
  heat         how active the creator's rank has been (movement volume)
  momentum     blended forward score, -100..100
  tags         SLEEPER | COILED | FADE | SURGING | QUIET

Predicted star cost: expensive creators sit high and have been calm; cheap ones sit
low. This mirrors the game's star-cap logic (stars follow trailing 14-day heat), so
it is an ESTIMATE, not the real card price. The UI must say so.
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAP_DIR = ROOT / "data" / "snapshots"
OUT = ROOT / "data" / "signals.json"

STAR_CAP = 15
LINEUP_SIZE = 5


def load_snapshots() -> list[dict]:
    snaps = []
    for p in sorted(SNAP_DIR.glob("*.json")):
        try:
            snaps.append(json.loads(p.read_text()))
        except Exception:
            continue
    return snaps


def index_positions(snaps: list[dict]) -> dict[str, list[int]]:
    """creator name -> list of positions, oldest first."""
    series: dict[str, list[int]] = {}
    for s in snaps:
        for r in s.get("rows", []):
            series.setdefault(r["name"], []).append(r["position"])
    return series


def index_deltas(snaps: list[dict]) -> dict[str, list[int]]:
    series: dict[str, list[int]] = {}
    for s in snaps:
        for r in s.get("rows", []):
            series.setdefault(r["name"], []).append(r["delta"])
    return series


def est_stars(position: int, total: int) -> int:
    """Estimate star cost from rank. Top of board costs the most stars."""
    if total <= 1:
        return 3
    pct = (position - 1) / (total - 1)  # 0 = rank 1, 1 = last
    if pct <= 0.06:
        return 5
    if pct <= 0.15:
        return 4
    if pct <= 0.40:
        return 3
    if pct <= 0.70:
        return 2
    return 1


def build() -> dict:
    snaps = load_snapshots()
    if not snaps:
        raise SystemExit("no snapshots found — run collector/snapshot.py first")

    latest = snaps[-1]
    rows = latest.get("rows", [])
    total = len(rows) or 1

    positions = index_positions(snaps)
    deltas = index_deltas(snaps)

    out_rows = []
    for r in rows:
        name = r["name"]
        phist = positions.get(name, [r["position"]])
        dhist = deltas.get(name, [r["delta"]])

        d4h = r["delta"]
        d24h = phist[0] - phist[-1] if len(phist) >= 2 else None
        d72h = d24h  # same window until we have >24h of history
        prev = dhist[:-1]
        acceleration = round(d4h - (sum(prev) / len(prev)), 2) if prev else None
        volatility = round(statistics.pstdev(dhist), 2) if len(dhist) > 1 else 0.0

        # momentum: reward current move + acceleration, punish recent decay
        score = d4h * 6.0
        if acceleration is not None:
            score += acceleration * 4.0
        if d24h is not None:
            score += d24h * 1.5
        score -= volatility * 1.0
        momentum = max(-100.0, min(100.0, round(score, 1)))

        stars = est_stars(r["position"], total)

        tags = []
        if momentum >= 12:
            tags.append("SURGING")
        if d4h >= 2 and volatility < 2.5:
            tags.append("COILED")
        if d4h < 0 and r["position"] <= int(total * 0.4):
            tags.append("FADE")
        if stars <= 2 and momentum > 0:
            tags.append("SLEEPER")
        if d4h == 0 and volatility == 0:
            tags.append("QUIET")
        if not tags:
            tags.append("STEADY")

        # value: momentum per star spent
        value = round(momentum / stars, 1) if stars else 0.0

        out_rows.append(
            {
                "name": name,
                "id": r.get("id"),
                "handle": r.get("handle"),
                "position": r["position"],
                "delta4h": d4h,
                "delta24h": d24h,
                "delta72h": d72h,
                "acceleration": acceleration,
                "volatility": volatility,
                "momentum": momentum,
                "estStars": stars,
                "value": value,
                "tags": tags,
                "isNew": r.get("isNew", False),
            }
        )

    out_rows.sort(key=lambda x: -x["momentum"])

    # Suggested lineups: best value under the star cap.
    def greedy(pool: list[dict]) -> dict:
        picked, spent = [], 0
        for c in pool:
            if spent + c["estStars"] <= STAR_CAP and len(picked) < LINEUP_SIZE:
                picked.append(c)
                spent += c["estStars"]
        return {
            "picks": [{"name": c["name"], "estStars": c["estStars"], "momentum": c["momentum"], "tags": c["tags"]} for c in picked],
            "starsUsed": spent,
            "projectedMomentum": round(sum(c["momentum"] for c in picked), 1),
        }

    lineups = {
        "balanced": greedy(out_rows),
        "sleeperHeavy": greedy([c for c in out_rows if c["estStars"] <= 3]),
        "contrarian": greedy(sorted([c for c in out_rows if "FADE" not in c["tags"]], key=lambda x: x["value"], reverse=True)),
    }

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "snapshotCount": len(snaps),
        "firstSnapshot": snaps[0].get("collectedAt"),
        "latestSnapshot": latest.get("collectedAt"),
        "dataAsOf": latest.get("asOf"),
        "source": latest.get("source"),
        "starsCap": STAR_CAP,
        "lineupSize": LINEUP_SIZE,
        "creators": out_rows,
        "lineups": lineups,
        "disclaimer": (
            "Scores are derived from Motion's public leaderboard (positions + 4-hour rank deltas). "
            "Star costs are estimated from rank, not the real card values. Nothing here is insider information."
        ),
    }


def main() -> int:
    data = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1) + "\n")
    top = data["creators"][:5]
    print(f"snapshots: {data['snapshotCount']} | creators: {len(data['creators'])}")
    print("top momentum:")
    for c in top:
        print(f"  {c['name']:<20} #{c['position']:<3} mom={c['momentum']:>6} ★{c['estStars']} {','.join(c['tags'])}")
    for name, lu in data["lineups"].items():
        print(f"lineup {name}: {lu['starsUsed']}/{STAR_CAP}★ proj={lu['projectedMomentum']}")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
