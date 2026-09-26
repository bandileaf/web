-- Word Atlas v2, step 5: prepositions and conjunctions get their own part-of-speech columns.
-- Run in Supabase Dashboard > SQL Editor (only adds columns).
--
--   words.prep  text  meaning as a preposition   (despite, via, amid ...)   shown as "prep. ..."
--   words.conj  text  meaning as a conjunction   (whereas, although ...)    shown as "conj. ..."

alter table words add column if not exists prep text;
alter table words add column if not exists conj text;
