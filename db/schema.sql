-- Word Atlas schema (final form). Run in Supabase Dashboard > SQL Editor.
-- Safe to re-run: objects are created if missing. Data is not part of this file (it lives in the DB and is
-- maintained through Claude with the add-word skill).
--
-- morphemes = prefixes and suffixes only.  words = every word AND every root: a root is a word that cannot be
-- split (parts = '{}') and is used by other words.

create table if not exists morphemes (
  id       bigint generated always as identity primary key,
  type     text not null check (type in ('prefix', 'suffix')),
  text     text not null,                     -- representative spelling, no hyphen (ad, ion)
  meaning_ko text not null,
  variants text[] not null default '{}',      -- spelling variants of text: ad -> {ac,af,ap,ar,as,at}
  unique (type, text)
);

create table if not exists words (
  id     bigint generated always as identity primary key,
  word   text not null unique,
  -- meaning per part of speech (null = not that POS; several senses in one column separated by ' / ')
  noun   text,
  verb   text,
  adj    text,
  adv    text,
  prep   text,
  conj   text,
  -- ordered components, each tagged with its table: 'm12' = morphemes.id 12 (prefix/suffix), 'w7' = words.id 7
  -- (a root or another word). '{}' = the word cannot be split, i.e. it is a root.
  --   compassion = {m<con>,w<passion>}    benefit = {}
  parts  text[] not null default '{}',
  forms  text[] not null default '{}',        -- actual spelling of each part, same order as parts ({com,passion})
  etym_checked_at timestamptz,                -- when the etymology was verified (null = not yet)
  importance smallint check (importance between 1 and 5)  -- daily-use rank, 1=most common .. 5=rarest; Oxford 5000
                                                            -- CEFR first, else the BNC/COCA 25k band; null = in
                                                            -- neither list, e.g. a bound root (see add-word skill)
);

create index if not exists words_parts_gin on words using gin (parts);   -- which words use w7: parts=cs.{w7}

-- Public read-only access for the browser (anon key). Writes only via the service role (secret key).
alter table morphemes enable row level security;
alter table words     enable row level security;

drop policy if exists "public read" on morphemes;
drop policy if exists "public read" on words;
create policy "public read" on morphemes for select to anon, authenticated using (true);
create policy "public read" on words     for select to anon, authenticated using (true);

-- Bring a database created with the earlier schema up to this form (no-ops on a fresh one).
alter table morphemes drop constraint if exists morphemes_type_check;
alter table morphemes add  constraint morphemes_type_check check (type in ('prefix', 'suffix'));
alter table words add column if not exists importance smallint check (importance between 1 and 5);
