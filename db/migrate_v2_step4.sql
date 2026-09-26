-- Word Atlas v2, step 4: part-of-speech meanings on WORDS, and a link from a root to its word.
-- Run in Supabase Dashboard > SQL Editor.
--
--   words.noun / verb / adj / adv  text  the word's meaning as that part of speech (null = not that POS)
--       e.g. service: noun = '서비스', verb = '제공하다'   ->  shown as "n. 서비스, v. 제공하다"
--       words.meaning_ko stays as the short summary meaning.
--   morphemes.word_id  bigint  the word with the same spelling when a root is itself a word (happy, use, break);
--       null for bound roots (dict, mit) and for prefixes/suffixes. Rich meaning comes from that word.
--
-- The POS drafts that were added to morphemes are removed (their values are re-created on words).

alter table words add column if not exists noun text;
alter table words add column if not exists verb text;
alter table words add column if not exists adj  text;
alter table words add column if not exists adv  text;

alter table morphemes add column if not exists word_id bigint references words (id) on delete set null;
create index if not exists morphemes_word_id_idx on morphemes (word_id);

alter table morphemes drop column if exists noun;
alter table morphemes drop column if exists verb;
alter table morphemes drop column if exists adj;
alter table morphemes drop column if exists adv;
alter table morphemes drop constraint if exists morphemes_senses_check;
alter table morphemes drop constraint if exists morphemes_pos_check;
alter table morphemes drop column if exists senses;
alter table morphemes drop column if exists pos;
