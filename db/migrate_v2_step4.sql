-- Word Atlas v2, step 4: grammatical senses of roots (part of speech + its own meaning).
-- Run in Supabase Dashboard > SQL Editor.
--
--   morphemes.senses  jsonb  [{"pos":"noun","ko":"서비스"},{"pos":"verb","ko":"서비스하다"}]
--                            pos is one of noun | verb | adj | adv; first item = main sense.
--                            Roots only; '[]' for prefixes/suffixes and roots not classified yet.
--                            Query: GET /morphemes?senses=cs.[{"pos":"verb"}]

alter table morphemes add column if not exists senses jsonb not null default '[]';
alter table morphemes drop constraint if exists morphemes_senses_check;
alter table morphemes add constraint morphemes_senses_check check (jsonb_typeof(senses) = 'array');

-- the earlier draft column (pos text[]) is superseded by senses
alter table morphemes drop constraint if exists morphemes_pos_check;
alter table morphemes drop column if exists pos;
