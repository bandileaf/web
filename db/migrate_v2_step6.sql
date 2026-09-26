-- Word Atlas v2, step 6: remove the obsolete columns. Run in Supabase Dashboard > SQL Editor
-- ONLY after the site works with words.parts (index.html and admin.html no longer read either column).
--
--   words.morpheme_ids  replaced by words.parts (typed 'm12' / 'w7' references)
--   words.kind          not needed: a root is a word with parts = '{}' that other words use

alter table words drop column if exists morpheme_ids;
alter table words drop column if exists kind;
