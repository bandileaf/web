-- Word Atlas v2, step 6: remove the obsolete columns. Run in Supabase Dashboard > SQL Editor
-- ONLY after the site works with words.parts and the part-of-speech columns
-- (index.html and admin.html no longer read any of these columns). Dropping is not reversible.
--
--   words.morpheme_ids  replaced by words.parts (typed 'm12' / 'w7' references)
--   words.kind          not needed: a root is a word with parts = '{}' that other words use
--   words.meaning_ko    replaced by noun / verb / adj / adv / prep / conj (morphemes keep their own meaning_ko)

alter table words drop column if exists morpheme_ids;
alter table words drop column if exists kind;
alter table words drop column if exists meaning_ko;
