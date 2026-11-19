-- Working lineup storage for Motion Draft Room.
-- Run this once in the Supabase dashboard: SQL Editor -> New query -> Run.
-- Safe to run twice; every statement is idempotent.
--
-- Why a table and not localStorage: a draft saved only in the browser lives on
-- exactly that browser. Five picks made on a laptop read 0/5 on a phone. The
-- lineup is the one thing on this site a visitor builds over time, so it follows
-- the X account instead of the device.

create table if not exists public.drafts (
  -- X's numeric id, not the handle: handles get renamed, ids do not.
  xid         text        primary key,
  handle      text        not null default '',
  -- the whole lineup as one value. It is read and written whole, five entries at
  -- a time, and nothing queries inside it, so a jsonb column is the honest shape.
  picks       jsonb       not null default '[]'::jsonb,
  updated_at  timestamptz not null default now(),

  constraint drafts_picks_len check (jsonb_array_length(picks) between 0 and 5)
);

-- Row level security on with no policies: the anon key reads and writes nothing.
-- The endpoint reaches this table with the service role, which bypasses RLS and
-- never leaves the Vercel environment. A draft is someone's unfinished work; it
-- is not public the way a filed receipt is.
alter table public.drafts enable row level security;
