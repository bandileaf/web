-- Word Atlas v2, step 2: track which words have been checked against Wiktionary.
-- Run in Supabase Dashboard > SQL Editor.
--
--   words.etym_checked  boolean  true once the word's etymology was verified (split or confirmed unsplittable)

alter table words add column if not exists etym_checked boolean not null default false;
