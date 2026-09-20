-- Word Atlas schema + seed. Run in Supabase Dashboard > SQL Editor.
-- Safe to re-run: tables are created if missing and seed rows are skipped on conflict.

create table if not exists morphemes (
  id         bigint generated always as identity primary key,
  type       text not null check (type in ('prefix','root','suffix')),
  text       text not null,
  meaning_ko text not null,
  unique (type, text)
);

create table if not exists words (
  id         bigint generated always as identity primary key,
  word       text not null unique,
  meaning_ko text not null
);

create table if not exists word_morphemes (
  word_id     bigint not null references words(id) on delete cascade,
  morpheme_id bigint not null references morphemes(id) on delete cascade,
  position    smallint not null,
  primary key (word_id, morpheme_id)
);

-- Public read-only access for the browser (anon key). Writes only via the dashboard / service role.
alter table morphemes      enable row level security;
alter table words          enable row level security;
alter table word_morphemes enable row level security;

drop policy if exists "public read" on morphemes;
drop policy if exists "public read" on words;
drop policy if exists "public read" on word_morphemes;
create policy "public read" on morphemes      for select to anon, authenticated using (true);
create policy "public read" on words          for select to anon, authenticated using (true);
create policy "public read" on word_morphemes for select to anon, authenticated using (true);

-- Seed: morphemes
insert into morphemes (type, text, meaning_ko) values
  ('prefix', 'un', '부정'),
  ('prefix', 're', '다시'),
  ('prefix', 'pre', '이전'),
  ('prefix', 'im', '안으로'),
  ('prefix', 'ex', '밖으로'),
  ('prefix', 'trans', '가로질러'),
  ('prefix', 'dis', '반대'),
  ('prefix', 'inter', '사이'),
  ('prefix', 'con', '함께'),
  ('prefix', 'de', '아래로 · 반대'),
  ('root', 'happy', '행복한'),
  ('root', 'break', '깨다'),
  ('root', 'use', '사용하다'),
  ('root', 'view', '보다'),
  ('root', 'dict', '말하다'),
  ('root', 'port', '나르다'),
  ('root', 'agree', '동의하다'),
  ('root', 'act', '행하다'),
  ('root', 'form', '모양'),
  ('root', 'struct', '짓다'),
  ('suffix', 'able', '~할 수 있는'),
  ('suffix', 'ful', '~로 가득한'),
  ('suffix', 'less', '~이 없는'),
  ('suffix', 'ion', '행위 · 명사'),
  ('suffix', 'ment', '결과 · 명사'),
  ('suffix', 'ive', '~하는 성향'),
  ('suffix', 'or', '~하는 사람')
on conflict (type, text) do nothing;

-- Seed: words
insert into words (word, meaning_ko) values
  ('unhappy', '불행한'),
  ('unbreakable', '깨지지 않는'),
  ('reusable', '재사용할 수 있는'),
  ('review', '복습하다, 검토'),
  ('preview', '미리 보기'),
  ('predict', '예측하다'),
  ('prediction', '예측'),
  ('import', '수입하다'),
  ('export', '수출하다'),
  ('transport', '수송하다'),
  ('portable', '휴대할 수 있는'),
  ('disagreement', '의견 차이'),
  ('useful', '유용한'),
  ('useless', '쓸모없는'),
  ('action', '행동'),
  ('active', '활동적인'),
  ('actor', '배우'),
  ('interact', '상호작용하다'),
  ('transform', '변형시키다'),
  ('construction', '건설'),
  ('destruction', '파괴')
on conflict (word) do nothing;

-- Seed: word <-> morpheme links
insert into word_morphemes (word_id, morpheme_id, position)
select w.id, m.id, x.pos
from (values
  ('unhappy', 'prefix', 'un', 1),
  ('unhappy', 'root', 'happy', 2),
  ('unbreakable', 'prefix', 'un', 1),
  ('unbreakable', 'root', 'break', 2),
  ('unbreakable', 'suffix', 'able', 3),
  ('reusable', 'prefix', 're', 1),
  ('reusable', 'root', 'use', 2),
  ('reusable', 'suffix', 'able', 3),
  ('review', 'prefix', 're', 1),
  ('review', 'root', 'view', 2),
  ('preview', 'prefix', 'pre', 1),
  ('preview', 'root', 'view', 2),
  ('predict', 'prefix', 'pre', 1),
  ('predict', 'root', 'dict', 2),
  ('prediction', 'prefix', 'pre', 1),
  ('prediction', 'root', 'dict', 2),
  ('prediction', 'suffix', 'ion', 3),
  ('import', 'prefix', 'im', 1),
  ('import', 'root', 'port', 2),
  ('export', 'prefix', 'ex', 1),
  ('export', 'root', 'port', 2),
  ('transport', 'prefix', 'trans', 1),
  ('transport', 'root', 'port', 2),
  ('portable', 'root', 'port', 1),
  ('portable', 'suffix', 'able', 2),
  ('disagreement', 'prefix', 'dis', 1),
  ('disagreement', 'root', 'agree', 2),
  ('disagreement', 'suffix', 'ment', 3),
  ('useful', 'root', 'use', 1),
  ('useful', 'suffix', 'ful', 2),
  ('useless', 'root', 'use', 1),
  ('useless', 'suffix', 'less', 2),
  ('action', 'root', 'act', 1),
  ('action', 'suffix', 'ion', 2),
  ('active', 'root', 'act', 1),
  ('active', 'suffix', 'ive', 2),
  ('actor', 'root', 'act', 1),
  ('actor', 'suffix', 'or', 2),
  ('interact', 'prefix', 'inter', 1),
  ('interact', 'root', 'act', 2),
  ('transform', 'prefix', 'trans', 1),
  ('transform', 'root', 'form', 2),
  ('construction', 'prefix', 'con', 1),
  ('construction', 'root', 'struct', 2),
  ('construction', 'suffix', 'ion', 3),
  ('destruction', 'prefix', 'de', 1),
  ('destruction', 'root', 'struct', 2),
  ('destruction', 'suffix', 'ion', 3)
) as x(word, type, text, pos)
join words w on w.word = x.word
join morphemes m on m.type = x.type and m.text = x.text
on conflict do nothing;
