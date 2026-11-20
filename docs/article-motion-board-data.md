# What 11 snapshots of Motion's leaderboard actually show

Motion Draft Room has been collecting Motion's public creator leaderboard every
four hours since 15 November. This is what the data says — measured, with the
method and the holes stated, because most of the interesting findings are
about the *shape* of the board rather than who sits on top of it.

**11 windows · 79 creators · 15 Nov 20:00Z → 20 Nov 04:00Z · data as of 20 Nov 04:00Z**

---

## 1. The board moves far more than the top ten suggests

Only four creators did not move a single place across all 11 windows: IShowSpeed
(#1, frozen the entire time), Chris Dixon, Shayne Coplan and Brian Chesky
(the three at the bottom, #77–79). Everyone else moved at least once.

Per-window churn — how many of the 79 cards changed rank between consecutive
snapshots:

- 58% changed in the most recent window (46 of 79)
- 87% changed on 18 Nov 04:00Z, the biggest reshuffle on record
- 18% on 16 Nov 08:00Z, the quietest

"The board moved" is the normal state, not the exception. A single snapshot is a
photograph of a river.

## 2. Net movement over five days

Biggest climbers (first snapshot → 20 Nov):

- **Kai Trump** — #73 → #35 (+38)
- **Jynxzi** — #76 → #48 (+28)
- **Jim Cramer** — #34 → #14 (+20)
- **Paul Graham** — #62 → #45 (+17)
- **Grimes** — #19 → #8 (+11)

Biggest fallers:

- **Mert Mumtaz** — #47 → #61 (−14)
- **Lex Fridman** — #7 → #20 (−13)
- **Threadguy** — #29 → #42 (−13)
- **Tarek Mansour** — #50 → #62 (−12)
- **Sir Doge of the Coin** — #40 → #50 (−10)

Two entries deserve a caveat that the ranking table alone would hide. Kai Trump
went #73 → #36 *inside* the 40-hour collection gap, and then sat at #36 for six
straight windows before nudging to #35. Jynxzi did the same thing one place lower.
The net numbers are real; the path through them is unknown, and a two-point move
over the following four days is not momentum — it is a plateau at a new level.
Kai Trump's current momentum score is **−13.9**: up 38 places over 72 hours,
decelerating, with volatility 10.6. That is the profile of a jump that already
happened, not one in progress.

## 3. Stars track rank, and the price is not linear

Star estimate is derived from percentile position on the board — this is our
modelling on the game's 1–8 scale, not Motion's published per-card rating. What
that mapping produces:

- #1–10 → 5–8 stars (avg 6.4)
- #11–20 → 4–5 stars (avg 4.6)
- #21–45 → 2–4 stars (avg 3.2)
- #46–60 → 2 stars (avg 2.0)
- #61–79 → 1–2 stars (avg 1.2)

A ranking move is roughly twice as expensive in stars near the top as near the
bottom. Grimes climbing 11 places costs a 6-star card; Balaji climbing 10 places
costs a 2-star card. Under a 32-star cap with five lineup slots — 6.4 stars
average allowed — that asymmetry is the whole game: you cannot buy the top ten
and fill a roster.

## 4. The cheap tail is where the moves are

Ranked by momentum per star spent (value), latest window:

- **Balaji** — #46, 2★, value 13.6, #56 → #46 over five days
- **Vlad Tenev** — #68, 1★, value 11.2, #65 → #68
- **Aaron Levie** — #70, 1★, value 9.6, #68 → #70
- **Murray Hill Guy** — #40, 3★, value 9.2, #38 → #40
- **Nikita Bier** — #52, 2★, value 9.1, #49 → #52

Two of those five are moving the wrong way over the full five days (Vlad Tenev,
Aaron Levie) while scoring positive momentum *right now*. That divergence is the
honest reason to distrust a single window: momentum is a short-horizon number.

Of the 13 creators that moved 10+ places net, the star cost was 1, 2, 2, 2, 2, 2,
2, 3, 3, 4, 4, 5, 6 — average 2.92 stars, slightly *below* the board average of
3.08. Rank movement is not bought at the top.

## 5. Momentum across the whole board is negative, barely

Sum of momentum across all 79 creators: **−60.3**. Mean: **−0.76**.
39 creators positive, 36 negative, 4 exactly zero.

In the latest window: 42 of 79 did not move at all, 18 moved down, 7 moved up by
2 or more. Tag split: COILED 24, SLEEPER 22, STEADY 15, FADE 8, SURGING 6, QUIET 4.
Six cards surging against twenty-four gone flat.

The board is mostly standing still with a slightly heavier decay pile. A lineup
built on last window's risers is buying at the moment the momentum score has
already spent itself — the six SURGING cards are the only ones climbing *and*
carrying momentum (Shams Charania, Murray Hill Guy, Balaji, Jason, Chamath
Palihapitiya, Nikita Bier). Jim Cramer is the counter-example: +11 places in the
last window, momentum 1.1, value 0.2, tagged FADE because the latest window
turned down. Tags are exclusive and priority-ordered (SURGING → FADE → COILED →
SLEEPER → STEADY → QUIET), so a card can be on neither pile while being visible
in the ranking table.

Best five by momentum sum at or under the 32-star cap (this is arithmetic on the
momentum column, not a claim about the game's Lineup Score): Shams Charania 28.2
(5★), Murray Hill Guy 27.6 (3★), Balaji 27.2 (2★), Jason 26.1 (3★), Chamath
Palihapitiya 18.4 (3★) — total 127.5 momentum on 16 of 32 stars. The app's own
"balanced" lineup spends 9 stars for 93.7. The best five cards are cheap; the
expensive cards are not the ones moving.

## 6. The data has holes, and they are dated

Eleven windows exist. A clean four-hour collector over the same span would have
about 26. The gaps:

- 8h between 15 Nov 20:00Z and 16 Nov 04:00Z
- **40h between 16 Nov 12:00Z and 18 Nov 04:00Z**
- 12h between 18 Nov 04:00Z and 18 Nov 16:00Z
- 8h, 12h, 8h across the last three steps

Motion's board only serves the active slot, so a missed window is unrecoverable —
it cannot be backfilled. Those 40 hours are why 24h and 72h deltas are computed
from the newest published as-of time backwards over the windows we actually hold,
rather than pretending to a uniform grid. Eleven of the thirty single-window jumps
of 6+ places in §2 landed in that one gap, which is a fair estimate of how much
motion the missing 29 windows would have shown.

## 7. What the app claims, and what it refuses to claim

The Lineup Score formula is published: sum of Creator Motion Score × card Score
Boost, and so are the tier multipliers — Common 1×, Rare 1.5×, Epic 2×,
Legendary 2.5×. What the docs do not publish is the per-tournament boost limit,
how boosts combine across a mixed lineup, or Motion Score itself. So rarity is
recorded on the receipt and never graded on. Star costs here are estimated from
rank; they are not the real card values. A projected score is labelled projected
in the same line where it appears, and it is rank-relative to the best-available
lineup on this board, not the game's Lineup Score.

That distinction matters for reading every number above: the rank data is
Motion's, the star estimates and momentum scores are this draft room's modelling,
and the two are never mixed in one column.

---

*Method: `collector/snapshot.py` captures the full 79-creator board per window;
`engine/score.py` derives momentum as `d4h×6 + acceleration×4 + d24h×1.5 −
volatility×1`, clamped to ±100. Live: [motion-draft-room.vercel.app](https://motion-draft-room.vercel.app)*
