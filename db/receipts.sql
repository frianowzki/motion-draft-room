-- Receipt book for Motion Draft Room.
-- Run this once in the Supabase dashboard: SQL Editor -> New query -> Run.
-- It is safe to run twice; every statement is idempotent.

create table if not exists public.receipts (
  -- identity. `xid` is X's numeric user id: handles get renamed, ids do not, so
  -- uniqueness keys on the id and the handle is only what the book displays.
  xid            text        not null,
  slot_at_lock   text        not null,
  player         text        not null,
  name           text        not null default '',
  avatar         text        not null default '',
  picks          jsonb       not null default '[]'::jsonb,
  -- 'pending' until a snapshot from a strictly later window grades it, then
  -- 'settled'. Never a boolean: the book shows the three states separately.
  status         text        not null default 'pending'
                             check (status in ('pending', 'settled')),
  score          integer,
  locked_at      timestamptz not null default now(),
  settled_at     timestamptz,
  graded_as_of   text,
  created_at     timestamptz not null default now(),

  -- One lineup per person per snapshot window, enforced by the database rather
  -- than by a scan in the endpoint. Two people filing in the same instant used
  -- to race and lose one of the two; this makes the second answer a 409.
  constraint receipts_one_per_player_per_slot unique (xid, slot_at_lock),

  -- The page can only render these; anything longer is a client that lied.
  constraint receipts_player_len check (char_length(player) between 1 and 15),
  constraint receipts_slot_len   check (char_length(slot_at_lock) between 1 and 40),
  constraint receipts_picks_len  check (jsonb_array_length(picks) between 1 and 5)
);

-- The book is read newest-first and settled-in-order; one index serves both.
create index if not exists receipts_locked_at_idx on public.receipts (locked_at desc);
create index if not exists receipts_status_idx    on public.receipts (status);

-- Row level security is on with no policies: the anon key can read nothing and
-- write nothing. The API reaches the table with the service role, which bypasses
-- RLS, and that key only ever exists in the Vercel environment. Leaving RLS off
-- would let anyone holding the public anon key (it ships in every Supabase client)
-- write receipts, and a receipt is meant to be evidence.
alter table public.receipts enable row level security;
