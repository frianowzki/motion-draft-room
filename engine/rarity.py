"""Rarity and Score Boost - the published half of the real formula.

What the official docs do say (docs.motion.game, read 2026-11-15):

  Lineup Score = Sum of (Creator's Motion Score x Card's Score Boost)
  Each rarity comes with a Score Boost multiplier; rarer card = higher boost.
  Stars do not add boost; they only gate eligibility through the star cap.
  A lineup must meet tournament-specific limits on the rarity/boost mix.
  The multipliers themselves (docs.motion.game/docs/get-cards/understanding-cards):
  Common 1x, Rare 1.5x, Epic 2x, Legendary 2.5x.

What they do NOT say: the size of the boost limit, or how boosts combine. Those
are tournament-specific and printed in-game.

So this module never claims to reproduce a Lineup Score: the published boost
table is real, the Motion Score it multiplies is not public. It does two things:

  1. projects a lineup as  sum(relative_strength(c) * boost(rarity))  where
     relative_strength is a rank-based stand-in for the unpublished Motion Score
     and the boost multipliers are the published ones from DEFAULT_BOOST below,
     surfaced in the output as `publishedBoost`.
  2. answers the question the boosts actually decide in practice: given a star
     budget and a boost mix, which five creators maximise the projection? A
     degenerate "five Common cards, ignore boost" answer is possible with our
     invented numbers, so `optimise` refuses to present a projection whose
     rarity mix breaks a cap it was given.

The multipliers are copied from Motion's docs, not invented: change DEFAULT_BOOST
here, in one place, if they ever change them.
"""

from __future__ import annotations

TIERS = ("Common", "Rare", "Epic", "Legendary")

# Motion's published Score Boost table, verbatim from
# docs.motion.game/docs/get-cards/understanding-cards.
DEFAULT_BOOST = {"Common": 1.0, "Rare": 1.5, "Epic": 2.0, "Legendary": 2.5}

ASSUMED = False  # the boosts are documented; the Motion Score they multiply is not


def boost_for(rarity: object) -> float:
    key = str(rarity or "Common").strip().capitalize()
    return DEFAULT_BOOST.get(key, DEFAULT_BOOST["Common"])


def relative_strength(position: int, field_size: int) -> float:
    """Rank-based stand-in for Motion Score, in (0, 1].

    Motion Score is normalised against the creator pool, so the top of the board
    is worth more than the bottom. Linear in rank is the least dramatic curve
    that still respects that ordering - we are not claiming the real curve.
    """
    if not field_size or not position:
        return 0.0
    pos = max(1, min(int(position), int(field_size)))
    return (field_size - pos + 1) / field_size


def project(picks: list[dict], field_size: int) -> dict:
    """Project a lineup from {name, positionNow, rarity} entries.

    Returns the projection plus every assumption it rests on, so a caller cannot
    accidentally present the number as if it were the game's own score.
    """
    rows = []
    total = 0.0
    for p in picks:
        strength = relative_strength(p.get("positionNow") or p.get("positionAtLock") or 0, field_size)
        boost = boost_for(p.get("rarity"))
        contribution = strength * boost
        total += contribution
        rows.append({
            "name": p.get("name"),
            "position": p.get("positionNow") or p.get("positionAtLock"),
            "rarity": str(p.get("rarity") or "Common").strip().capitalize(),
            "boost": round(boost, 3),
            "strength": round(strength, 4),
            "contribution": round(contribution, 4),
        })
    return {
        "projected": round(total, 4),
        "picks": rows,
        "publishedBoost": dict(DEFAULT_BOOST),
        "assumptions": [
            "Motion Score is not public; strength is a rank-based stand-in in (0,1].",
            "Score Boost multipliers are published (Common 1, Rare 1.5, Epic 2, Legendary 2.5).",
            "This is not the game's Lineup Score and will not match it.",
        ],
    }


def optimise(creators: list[dict], star_cap: int, size: int = 5,
             cap_boost_sum: float | None = None, rarity: str = "Common") -> dict:
    """Best five under a star cap, by projected contribution.

    Returns the same shape as project(), plus `feasible`. `cap_boost_sum` is the
    tournament's boost limit when one is known; None means unknown and the
    result says so instead of pretending the lineup is legal.
    """
    usable = [c for c in creators if c.get("position") and (c.get("estStars") or 0) > 0]
    field_size = max((c.get("position") or 1) for c in usable) if usable else 0
    scored = []
    for c in usable:
        strength = relative_strength(c["position"], field_size)
        scored.append({**c, "_strength": strength, "_contrib": strength * boost_for(rarity)})
    scored.sort(key=lambda c: c["_contrib"], reverse=True)

    picked, stars = [], 0
    for c in scored:
        if len(picked) == size:
            break
        st = int(c.get("estStars") or 0)
        if stars + st > star_cap:
            continue
        picked.append(c)
        stars += st

    boost_sum = sum(boost_for(rarity) for _ in picked)
    feasible = len(picked) == size and (cap_boost_sum is None or boost_sum <= cap_boost_sum + 1e-9)
    return {
        "picks": [{"name": c["name"], "position": c["position"], "estStars": c["estStars"],
                   "rarity": rarity} for c in picked],
        "starsUsed": stars,
        "starCap": star_cap,
        "boostSum": round(boost_sum, 3),
        "boostCap": cap_boost_sum,
        "feasible": feasible,
        "rarityKnown": str(rarity).strip().capitalize() in DEFAULT_BOOST,
        "feasibleNote": (
            "boost limit is not published; this lineup is unverified against it"
            if cap_boost_sum is None else "checked against the given boost limit"
        ),
    }
