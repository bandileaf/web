-- Word Atlas v2, step 4: roots move from morphemes to words; words get part-of-speech meanings
-- and typed part references. Run in Supabase Dashboard > SQL Editor. Only ADDs columns on words
-- (the old words.morpheme_ids keeps working until the site is switched over).
--
--   words.parts   text[]  ordered components of the word, each tagged with its table:
--                         'm12' = morphemes.id 12 (prefix/suffix), 'w7' = words.id 7 (a word or root, itself
--                         decomposed by ITS parts). An atomic word/root has parts = '{}'.
--                         e.g. unhappiness = {m3,w15,m24}; happy = {w90,m31} (hap + y); benefit = {}
--   words.forms   text[]  (already exists) actual spelling of each part, same order as parts
--   words.kind    text    'word' (a real word) | 'root' (bound Latin/Greek root such as dict, mit)
--   words.noun / verb / adj / adv  text  the meaning as that part of speech (null = not that POS),
--                         e.g. service: noun '서비스', verb '제공하다'  ->  "n. 서비스, v. 제공하다"
--                         words.meaning_ko stays as the short summary meaning.
--
-- After the roots have been moved (later steps), morphemes holds only prefixes and suffixes.

alter table words add column if not exists parts text[] not null default '{}';
alter table words add column if not exists kind  text   not null default 'word';
alter table words drop constraint if exists words_kind_check;
alter table words add constraint words_kind_check check (kind in ('word', 'root'));
alter table words add column if not exists noun text;
alter table words add column if not exists verb text;
alter table words add column if not exists adj  text;
alter table words add column if not exists adv  text;
create index if not exists words_parts_gin on words using gin (parts);

-- drafts from earlier iterations on morphemes are superseded
alter table morphemes drop column if exists word_id;
alter table morphemes drop column if exists noun;
alter table morphemes drop column if exists verb;
alter table morphemes drop column if exists adj;
alter table morphemes drop column if exists adv;
alter table morphemes drop constraint if exists morphemes_senses_check;
alter table morphemes drop constraint if exists morphemes_pos_check;
alter table morphemes drop column if exists senses;
alter table morphemes drop column if exists pos;
