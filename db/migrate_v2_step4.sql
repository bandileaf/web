-- Word Atlas v2, step 4: grammatical classes of roots.
-- Run in Supabase Dashboard > SQL Editor.
--
--   morphemes.pos  text[]  any of noun | verb | adj | adv, e.g. grant -> {verb,noun}
--                          (roots only; empty for prefixes/suffixes and roots not classified yet)

alter table morphemes add column if not exists pos text[] not null default '{}';
alter table morphemes drop constraint if exists morphemes_pos_check;
alter table morphemes add constraint morphemes_pos_check
  check (pos <@ array['noun', 'verb', 'adj', 'adv']);
