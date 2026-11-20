# THREAD — Motion leaderboard, 11 windows of data (20 Nov 2026)

Line limits: 280 chars. Numbered 1/12 … 12/12. Link lives in the last tweet only.
Tone: dry, data-first, no hype. Every number is from `/api/signals` (dataAsOf 20 Nov 04:00Z) and `/api/history` (11 windows, 15 Nov 20:00Z → 20 Nov 04:00Z).

---

**1/12**
5 days, 11 snapshots, 79 creators. we captured Motion's creator leaderboard every 4 hours from 15–20 Nov and compared every window to the last.

what the board actually does is not what the top 10 suggests. thread:

---

**2/12**
surprise #1: almost nothing is frozen.

only 4 of 79 creators held the exact same place across all 11 windows — IShowSpeed (#1, never budged) plus the three at the bottom (#77–79).

everyone else moved. churn per window ran 18%–87% of the board.

---

**3/12**
churn by window (share of 79 cards that changed rank):
16 nov 08z — 18%
16 nov 12z — 29%
19 nov 12z — 41%
19 nov 20z — 47%
20 nov 04z — 58%
18 nov 04z — 87% ← the big one

a single snapshot is a photo of a river, not the river.

---

**4/12**
the 40-hour hole in the middle (16 nov 12z → 18 nov 04z) did most of the visible damage.

11 of the 30 jumps of 6+ places in a single window happened inside that one gap. kai trump #73→#36, jynxzi #76→#50, garry tan #37→#24. all unseen.

---

**5/12**
be careful reading the 5-day climbers list:

kai trump +38, jynxzi +28, jim cramer +20, paul graham +17, grimes +11.

kai trump now: momentum −13.9, decelerating, volatility 10.6. she jumped once, then sat at #36 for six straight windows. plateau, not climb.

---

**6/12**
what a rank costs in stars (est. from percentile — our modelling, not motion's ratings):

#1–10 → 5–8★ (avg 6.4)
#11–20 → 4–5★ (4.6)
#21–45 → 2–4★ (3.2)
#46–60 → 2★ (2.0)
#61–79 → 1–2★ (1.2)

the price of a place roughly doubles at the top.

---

**7/12**
the 13 creators who moved 10+ places net cost 1,2,2,2,2,2,2,3,3,4,4,5,6 stars.

that's 2.92 average — below the board's own 3.08.

grimes climbing 11 places costs a 6★ card. balaji climbing 10 costs 2★. movement is not bought at the top.

---

**8/12**
whole-board momentum is negative, barely: sum −60.3, mean −0.76. 39 positive, 36 negative, 4 exactly zero.

latest window: 42 of 79 didn't move at all.

six cards SURGING, twenty-four COILED. the crowd is asleep with a long decay tail.

---

**9/12**
here's where a "best lineup" tool quietly lies:

optimise 5 slots under 32★ purely on current momentum → shams charania 28.2, murray hill guy 27.6, balaji 27.2, jason 26.1, chamath 18.4. 16 stars spent.

optimise on 5-day net climb instead → zero overlap. not one name repeats.

---

**10/12**
that's the real finding: momentum and persistence are different questions with disjoint answers.

- momentum = 4h move + acceleration + 24h, minus volatility
- persistence = where the rank actually ended up

shams leads momentum at 28.2 while trading −5 over 24h.

---

**11/12**
arithmetic that ends most "buy the top" arguments:

the top 5 by rank costs 36 stars. the cap is 32. you cannot field #1–5.

and their combined momentum is −0.2.

39 of the 79 cards carry positive momentum (+345.9 total). the top is a wall of zeros, the moves are underneath it.

---

**12/12**
what we won't claim:

momentum = d4h×6 + accel×4 + d24h×1.5 − volatility, ±100.
star costs estimated from rank, not motion's real values.
boosts are published (1/1.5/2/2.5). the boost cap and motion score aren't — rarity logged, never graded.

live: motion-draft-room.vercel.app
