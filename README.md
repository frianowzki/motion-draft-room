# Motion Draft Room

**Mogathon submission** — a forecast arena and auto-settled receipt book for
[Motion](https://motion.game)'s creator leaderboard.

Motion already gives you a leaderboard: who is where, right now. It does not give
you a memory, a forecast, or a scoreboard for your own calls. That is the gap this
fills.

---

## What it does

1. **Remembers.** Motion publishes a 4-hour rank delta and forgets it. A scheduled
   collector snapshots all 79 creators every 4 hours, so 24h/72h movement,
   acceleration and volatility become measurable.
2. **Forecasts.** Each creator gets a `momentum` score with an explicit formula
   (no black box), a star estimate, and a tag: `SURGING` / `COILED` / `SLEEPER` /
   `FADE` / `QUIET` / `STEADY`.
3. **Challenges you to commit.** You draft a lineup under a 15-star cap. Each pick
   requires a one-line thesis **and** a pre-mortem ("what would make this wrong").
   No one-click lineups — a lineup without reasoning is rejected.
4. **Settles itself.** When the next slot lands, every locked lineup is scored
   against actual rank movement. That produces a public hit rate per player. Claims
   get graded; vibes do not.

## Where the numbers come from

Primary source: `https://leaderboard.motion.game/api/leaderboard` — Motion's own
JSON, unauthenticated, 79 rows with `position`, `delta`, `isNew`, plus `asOf` /
`capturedAt` / `baselineCapturedAt`.

That is the **only** source. There is deliberately no third-party fallback: a
snapshot taken from anywhere else is not the same measurement, so a failed fetch fails
loudly (workflow goes red) instead of silently recording a different dataset.

**Honest limits — these are stated in the UI too, not buried:**

- Motion's creator **Score** is not public. Only rank position and 4-hour rank
  delta are. Every number here is derived from those two fields.
- Stars in the real game come from 14-day relative performance on a **1–8** scale and
  only gate eligibility via a per-tournament cap; ours are estimated from rank.
- The **32-star cap** is the cap used in Motion's own docs example. Real caps are set
  per tournament, and tournaments also limit the **rarity/boost mix**, which this
  project does not model yet.
- History starts at zero. On day one `delta24h` is `null`; acceleration needs at
  least three snapshots (~12 hours).
- The official API is undocumented and could change. `collector/snapshot.py`
  degrades to the aggregator, then to HTML, and refuses to write a half-empty
  snapshot.

## Layout

```
collector/snapshot.py   fetch + normalize + append one snapshot
engine/score.py         snapshots -> data/signals.json (momentum, tags, lineups)
data/snapshots/*.json   append-only history, one file per 4-hour slot
data/latest.json        most recent snapshot
data/signals.json       derived signals consumed by the UI
.github/workflows/      cron: every 4 hours, on branch `data`
```

## Why the collector runs on GitHub Actions

The authoring machine is suspended every 30 minutes. Anything holding state or
running on a timer cannot live there, so the schedule runs on GitHub Actions
(`cron: 7 */4 * * *`) and commits to the `data` branch. The app reads that branch;
no server of ours has to stay awake.

Run it by hand:

```bash
python3 collector/snapshot.py --dry-run   # fetch and print, write nothing
python3 collector/snapshot.py             # take a real snapshot
python3 engine/score.py                   # rebuild signals
```

No dependencies beyond the standard library.

## What the official docs say (read 2026-11-15)

Source: <https://docs.motion.game>. Summarised in `data/game-rules.json`.

| Rule | Value |
| --- | --- |
| Tournament | Mon 09:00 ET → Fri, finalised 17:30 ET |
| Lineup lock | Mon 07:00 ET (submissions open from Saturday) |
| Score updates | every 4 hours, Mon–Fri — the same rhythm as our collector |
| Lineup | exactly 5 different creators |
| Star cap | per tournament (docs example: 32); stars are **1–8** |
| Score boost | set by card rarity: Common / Rare / Epic / Legendary |
| Lineup Score | Σ (Creator Motion Score × card Score Boost) |
| Motion Score | X + Instagram + TikTok + YouTube engagement, normalised vs the creator pool — **not public** |
| Stars | trailing 14-day relative performance; **add no points**, only gate eligibility |
| Card extras | T20 (all-time top-20 finishes), RANK, SRC (platforms active, of 4) |
| Card acquisition | Starter Pack (7 random cards) or Marketplace (buy/bid/sell) |
| Trade-in | 12 cards burned → 1 new Starter Pack |

Two corrections this forced on the product: the draft cap moved from 15 to **32**
(a 5-card lineup of 1–8 star creators cannot fit under 15), and the star estimate now
uses the real **1–8** scale instead of a 1–5 invention.

### Rarity and Score Boost — modelled as an assumption, on purpose

The formula is public; the numbers in it are not. The docs state
`Lineup Score = Σ (Motion Score × Score Boost)`, that boost comes from card rarity and
that Legendary > Epic > Rare > Common — but the actual multipliers, the tournament's
boost limit and how boosts combine are printed only in the in-game Pack Shop. Motion
Score is not public either.

So `engine/rarity.py` does not pretend to reproduce a Lineup Score. It exposes the
boost table as a single named constant (`DEFAULT_BOOST`, clearly marked assumed),
projects a lineup from a rank-based stand-in for Motion Score, and returns the
assumptions alongside every number. Every rarity a player picks is recorded on the
receipt but **never graded on**, because grading on our own invented multipliers would
turn an assumption into a fake score. The UI shows `projected 3.42 · boosts ×5.60` and
says in the same line that this is not the game's Lineup Score.

When Motion publishes the real multipliers, change `DEFAULT_BOOST` in one place and the
engine, the API and the UI all follow.

## Status

Collector, scoring engine, Draft Room UI, public receipt book and rarity modelling are
live and verified against real data (79 creators, 6 slots/day). Deployed at
<https://motion-draft-room.vercel.app>.

What is verified end-to-end:

- Collection runs on GitHub Actions (`7 */4 * * *`, Mon–Fri slots), one snapshot per
  `(asOf, source)`, followed by `collector/verify.py`, which fails the run when a slot
  is missing even if the commit step had nothing to do.
- `GET /api/receipts` returns the whole public book and its summary; `POST` accepts a
  receipt from a claimable X handle (400 on a malformed handle), grades it server-side
  from the snapshot (the client never sends a score), and refuses a second receipt from
  the same handle in the same slot (409).
- Rarity is recorded per pick but never graded on; the only published boost numbers are
  the assumptions in `engine/rarity.py`.
- A receipt locked in the newest window shows as "waiting for a window" and is kept out
  of the hit-rate denominator, because there is no later snapshot to grade it against.

Still open:

- `delta24h` / `delta72h` are `null` until at least three distinct 4-hour windows exist.
  Early history came from manual runs, so some of it sits inside a single slot.
- The cron has produced no scheduled snapshot on its own yet; the first unattended run
  is the proof this needs.
- No marketplace or card-value integration: star costs remain a rank-based estimate.
