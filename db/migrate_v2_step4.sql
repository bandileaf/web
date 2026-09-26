-- Word Atlas v2, step 4: grammatical class of roots.
-- Run in Supabase Dashboard > SQL Editor.
--
--   morphemes.pos  text  noun | verb | adj | adv  (roots only; null for prefixes/suffixes and not yet classified)

alter table morphemes add column if not exists pos text
  check (pos in ('noun', 'verb', 'adj', 'adv'));
