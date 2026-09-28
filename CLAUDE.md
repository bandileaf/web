# CLAUDE.md

## 목적

- 미국 영어를 쉽게 외우기 위한, 고등학교 수준의 사전이다. 대상 단어 범위, 우선순위(`words.importance`), 새 기능(예: 주제별 묶음)은 전부 이 목적 기준으로 판단한다.
- 어원(접두사·어근·접미사) 분해가 1차 암기 보조 수단이고, 주제별 묶음(관계도 등) 같은 의미 기반 그룹도 같은 목적의 2차 수단이다. 어원 분해가 안 되는 고유/합성 단어(date, couple 등)도 고등학교 수준에서 중요하면 등록 대상이다.

- This is a static HTML web service deployed with GitHub Pages.
- Changes are verified on the deployed site, so after editing files, commit and **push immediately**. (Overrides the global rule.)
- Still review the push for secrets and personal data first. The repo is public.

## Database (Supabase)

- Word data lives in Supabase (`morphemes` = prefixes and suffixes only, `words` = every word and root; the whole structure is defined in `db/schema.sql`, the single source of truth). The user adds and edits data **through Claude**.
- The site only reads with the publishable key in `index.html` (RLS allows SELECT only). Writes need the secret key.
- Read the secret key from the local env var `SUPABASE_SECRET_KEY` (or the gitignored `db/.env.local`). Never write it into any tracked file, commit, or chat output.
- Insert via the Supabase REST API (`/rest/v1/<table>`), preferably with the scripts in `.claude/skills/add-word/scripts/`. A word's components are `words.parts` (text[]: `m12` = a prefix/suffix in `morphemes`, `w7` = a root or word in `words`); `parts = []` means the word cannot be split, i.e. it is a root. `words.forms` holds the actual spelling of each part. Spelling variants (ad/ac/af/ap...) live in `morphemes.variants`; the representative is `morphemes.text`. A word's meaning per part of speech is in `words.noun/verb/adj/adv/prep/conj` (text, null = not that POS; several senses separated by ` / `), shown as `n. 서비스, v. 제공하다`; words have no other meaning column. Verification progress is `words.etym_checked_at`. DDL (ALTER/DROP) cannot go through REST: update `db/schema.sql` (keep it re-runnable) and give it to the user to run in the Supabase SQL Editor.
- To add or check a word, use the `add-word` skill (`.claude/skills/add-word`): verify etymology with Wiktionary and Etymonline first, confirm with the user, then insert.
- After inserting, re-read the tables to verify (`verify_all.py`). `db/schema.sql` holds structure only, no data; change it only when the structure changes.
