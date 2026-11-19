# Mogathon submission

Everything you need to post this. Rules are from the official Mogathon 1-Pager
(fluent-labs.notion.site/mogathon) and the @motiongame_ announcement.

## What the rules actually ask for

- Create something around Motion.
- Post the creation on X.
- Tag **@callmogbot** in the post so it can be found.
- Deadline: submit before **19 November 2026**. Seats awarded before 20 November.
- A post tagged at the bot is the whole submission. No form, no repo requirement.
- Quality over quantity. One strong entry beats five rushed ones.
- Multiple entries are allowed, but seats do not stack.
- Something built before Mogathon is fine, as long as you post it and tag the bot.
- AI involvement is fine, but one click of generation is not the point. Your own judgment has to show.

## The post (ready to copy)

Text below is 1,271 characters, inside X's 280 on one tweet only if you attach
nothing. Use it as a tweet, or paste it into a thread if you want the screenshots
inline.

```
Five creators. Five reasons. One grade.

I built Motion Draft Room for #Mogathon @callmogbot

Motion's leaderboard shows where everyone stands right now, then the next slot
lands and it's gone. Rank deltas come in 4h slices and nothing accumulates.

So I made a draft room that remembers.

- A collector snapshots all 79 creators every 4h, so 24h/72h moves,
  acceleration and volatility are measured, not guessed
- Every pick needs a one-line thesis and a pre-mortem. You can't one-click
  a lineup here
- When the next window lands, your locked lineup gets graded against what
  actually moved, and the receipt goes into a public book with your hit rate
- Momentum tags on every creator: SURGING, COILED, SLEEPER, FADE, QUIET
- Built to the real rulebook: 5 cards, 32-star cap, 1-8 star scale, lock Mon
  07:00 ET, finalised Fri 5:00 PM ET

Where I had to guess, the app says so. Motion doesn't publish Score Boost
multipliers, so rarity is recorded on the receipt and never graded on. A
projected score is labelled as projected, in the same line where it appears.

Live: https://motion-draft-room.vercel.app
Code: https://github.com/frianowzki/motion-draft-room
```

## Posting steps

1. Log into X as yourself. This has to come from your account, not anyone else's.
2. Open https://motion-draft-room.vercel.app in a fresh tab and grab one screenshot
   for the attachment. The market tab in light mode reads best.
3. Paste the text above. Attach the screenshot.
4. Confirm **@callmogbot** is in the text and the link previews are not truncated.
5. Post. Then check the post renders and the links open on mobile.
6. Optional: reply to your own post with the demo walkthrough, or quote the
   @motiongame_ announcement.

## Alt post, shorter (264 chars)

```
Motion's leaderboard forgets the last slot. So I built a draft room that
doesn't: 4h snapshots of all 79 creators, 5 picks under a 32-star cap, every
pick needs a thesis, and each locked lineup gets graded when the next window
lands. #Mogathon @callmogbot

https://motion-draft-room.vercel.app
```

## If asked

- **What is it, one line?** A draft room for Motion that keeps a receipt on your calls.
- **Why should a seat go here?** It is the only entry that grades the player and not just the creators. The reasoning is written down before the window opens, so a lucky pick and a good call look different afterwards.
- **What is not finished?** Grading needs settled receipts, so the player leaderboard is empty until enough windows have locked. The app says that instead of padding the table.
- **Anything simulated?** No. Snapshot data is Motion's own leaderboard JSON, taken on a four-hour cron. Score Boost multipliers are modelled and labelled as modelled everywhere they show.

## Pre-flight

- [ ] README pushed to the `data` branch with the screenshots in `img/`
- [ ] https://motion-draft-room.vercel.app loads cold, no console errors
- [ ] Draft flow works end to end in a private window
- [ ] Screenshot attached, not just linked
- [ ] @callmogbot tagged, #Mogathon present
- [ ] Posted before 19 November 2026
