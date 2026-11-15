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

Secondary (fallback, and the only source of X handles):
`https://motionradar.vercel.app/api/leaderboard`.

**Honest limits — these are stated in the UI too, not buried:**

- Motion's creator **Score** is not public. Only rank position and 4-hour rank
  delta are. Every number here is derived from those two fields.
- Star costs are **estimated from rank**, not the real card values in the game.
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

## Status

Collector and scoring engine are live and verified against real data
(79 creators, 6 slots/day). The Draft Room UI and the receipt settlement layer are
next.
