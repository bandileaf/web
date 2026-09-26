-- Word Atlas v2, step 1 of 3: ADD columns only. Nothing is removed, the site keeps working.
-- Run in Supabase Dashboard > SQL Editor.
--
--   words.morpheme_ids  bigint[]  ordered morpheme ids, shown as 3-15-24 (replaces word_morphemes)
--   words.forms         text[]    the actual spelling of each part, e.g. {ac,cept} for accept
--   morphemes.variants  text[]    spelling variants of the representative `text`, e.g. ad -> {ac,af,ap,...}

alter table words     add column if not exists morpheme_ids bigint[] not null default '{}';
alter table words     add column if not exists forms        text[]   not null default '{}';
alter table morphemes add column if not exists variants     text[]   not null default '{}';

-- "which words use morpheme X" -> GET /words?morpheme_ids=cs.{15}
create index if not exists words_morpheme_ids_gin on words using gin (morpheme_ids);
