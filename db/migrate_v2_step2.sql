-- Word Atlas v2, step 2: track which words have been checked against Wiktionary.
-- Run in Supabase Dashboard > SQL Editor.
--
--   words.etym_checked_at  timestamptz  when the word's etymology was verified (null = not checked yet)

alter table words drop column if exists etym_checked;
alter table words add column if not exists etym_checked_at timestamptz;
