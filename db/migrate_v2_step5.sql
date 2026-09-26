-- Word Atlas v2, step 5: roots keep their meaning only in noun/verb/adj/adv.
-- Run in Supabase Dashboard > SQL Editor.
--
-- morphemes.meaning_ko stays for prefixes and suffixes (they have no part-of-speech columns),
-- but roots no longer need it, so it must be allowed to be null.

alter table morphemes alter column meaning_ko drop not null;
