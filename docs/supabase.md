# Receipt book on Supabase

The public receipt book used to be one file, `data/receipts.json`, on the `data`
branch. Every filing was a read-modify-write of the whole file through the GitHub
contents API, which cost three things:

- **lost writes.** Two visitors filing in the same second both read the file, both
  wrote, and one of the two receipts disappeared. Nothing in the code could fix that:
  git has no compare-and-swap.
- **a read per visitor scaled badly.** Answering `GET /api/receipts` meant fetching
  and base64-decoding every receipt ever filed.
- **the rule lived in the wrong place.** "One lineup per person per window" was a
  loop in `api/receipts.py`. A race walks straight past a loop.

Postgres fixes all three: a filing is an `INSERT`, a read is a `SELECT`, and the
uniqueness rule is a constraint the database enforces whether or not the endpoint is
correct.

## What the user does (once)

1. **Create the project.** [supabase.com](https://supabase.com) → New project.
   Nothing here needs the region to be special; pick the one closest to the users.
2. **Create the table.** Dashboard → **SQL Editor** → New query → paste the whole of
   [`db/receipts.sql`](../db/receipts.sql) → **Run**. It is idempotent, so running it
   twice changes nothing.
3. **Copy two values** from Project Settings → **API**:
   - **Project URL** → `https://<ref>.supabase.co`
   - **service_role key** (under "Project API keys"). This is the secret one, not
     `anon`. The anon key cannot write: row level security is on with no policies.
4. **Put them in Vercel**, not in chat and not in the repo:
   Project `motion-draft-room` → Settings → Environment Variables → Production:

   | Name           | Value                    |
   | -------------- | ------------------------ |
   | `SUPABASE_URL` | the project URL          |
   | `SUPABASE_KEY` | the service_role key     |

   Mark both **sensitive**. `SUPABASE_KEY` is also accepted under the name
   `SUPABASE_SERVICE_KEY` if the dashboard has that already.
5. **Redeploy.** Env vars only reach a function on a new deployment.

## What happens with no credentials

`/api/receipts` answers **502** with `SUPABASE_URL / SUPABASE_KEY are not set on this
deployment`. It deliberately does not fall back to the git file and does not report a
receipt it did not save — a receipt is evidence, so a silent success would be worse
than a visible failure. `GET` fails the same way, which the page already renders as
"the public book is unreachable".

## The table

`public.receipts`, one row per filing. Columns are the JSON envelope the endpoint has
always returned, snake_cased; `picks` is `jsonb` and keeps the per-pick shape
(`name`, `positionAtLock`, `estStars`, `rarity`, `thesis`, `premortem`) verbatim, so
`api/receipt_store.py` maps row ↔ JSON and `/api/receipts` answers exactly the shape
the dashboard already renders.

The guarantees, all enforced by the table rather than by the endpoint:

- `unique (xid, slot_at_lock)` — one lineup per person per window. Keyed on X's
  numeric id, not the handle: handles get renamed, and before this a renamed account
  could file twice.
- `picks` holds 1–5 entries; `player` is 1–15 chars; `slot_at_lock` is 1–40.
- `status` is `pending` or `settled`, never a boolean — the page shows the two states
  differently.
- **RLS enabled, no policies.** Only the service role (server-side, in Vercel) can
  read or write. The anon key ships in every Supabase client, so it must be able to
  do nothing.

## Grading

Grading did not move. A receipt is still scored against the collector's snapshot on
the `data` branch, still only against a window *strictly later* than the lock, and
still recomputed server-side from the snapshot rows — a client cannot submit a score.
What changed is only where the grade is written back: `GET` and `POST` both regrade
pending receipts and write them with an upsert on the same key, so `regrade([])` costs
nothing and a page view is a write only when a receipt actually moved.

## Tests

Both run against a throwaway local Postgres 17, not against Supabase, and need no
credentials:

```
python3 -m tests.receipt_store_check     # schema + store, via a fake PostgREST over real SQL
python3 -m tests.receipts_endpoint_check # POST/GET through the real handler, signed X session
```

They cover the round trip (camelCase picks survive), the unique constraint refusing a
second lineup, a regrade not duplicating a row, the check constraints rejecting
bypassing input, RLS being on, newest-first ordering, a filing without a session
(401), a duplicate filing (409), and a slot in the future of the snapshot (400).
