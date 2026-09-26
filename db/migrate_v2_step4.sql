-- Word Atlas v2, step 4: part-of-speech meanings of roots, one column per part of speech.
-- Run in Supabase Dashboard > SQL Editor.
--
--   morphemes.noun / verb / adj / adv  text  the meaning of the root as that part of speech (null = not that POS)
--   e.g. service: noun = '서비스', verb = '제공하다'   ->  shown as "n. 서비스, v. 제공하다"
--   Roots only; prefixes/suffixes and unclassified roots keep all four null.
--   Which words/roots are verbs: GET /morphemes?verb=not.is.null

alter table morphemes add column if not exists noun text;
alter table morphemes add column if not exists verb text;
alter table morphemes add column if not exists adj  text;
alter table morphemes add column if not exists adv  text;

-- drafts from earlier iterations are superseded
alter table morphemes drop constraint if exists morphemes_senses_check;
alter table morphemes drop constraint if exists morphemes_pos_check;
alter table morphemes drop column if exists senses;
alter table morphemes drop column if exists pos;
