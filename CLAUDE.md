# CLAUDE.md

- This is a static HTML web service deployed with GitHub Pages.
- Changes are verified on the deployed site, so after editing files, commit and **push immediately**. (Overrides the global rule.)
- Still review the push for secrets and personal data first. The repo is public.

## Database (Supabase)

- Word data lives in Supabase (`morphemes` = prefixes and suffixes only, `words` = every word and root; initial schema in `db/schema.sql`, v2 changes in `db/migrate_v2_*.sql`; the old `word_morphemes` table is gone). The user adds and edits data **through Claude**.
- The site only reads with the publishable key in `index.html` (RLS allows SELECT only). Writes need the secret key.
- Read the secret key from the local env var `SUPABASE_SECRET_KEY` (or the gitignored `db/.env.local`). Never write it into any tracked file, commit, or chat output.
- Insert via the Supabase REST API (`/rest/v1/<table>`), preferably with the scripts in `.claude/skills/add-word/scripts/`. A word's components are `words.parts` (text[]: `m12` = a prefix/suffix in `morphemes`, `w7` = a root or word in `words`); `parts = []` means the word cannot be split, i.e. it is a root. `words.forms` holds the actual spelling of each part. Spelling variants (ad/ac/af/ap...) live in `morphemes.variants`; the representative is `morphemes.text`. A word's meaning per part of speech is in `words.noun/verb/adj/adv` (text, null = not that POS; several senses separated by ` / `), shown as `n. 서비스, v. 제공하다`. Verification progress is `words.etym_checked_at`. `words.morpheme_ids` and `words.kind` are obsolete. DDL (ALTER/DROP) cannot go through REST; give the SQL to the user to run in the Supabase SQL Editor.
- To add or check a word, use the `add-word` skill (`.claude/skills/add-word`): verify etymology with Wiktionary and Etymonline first, confirm with the user, then insert.
- After inserting, re-read the tables to verify, and keep `db/schema.sql` seed data unchanged (it is only the initial seed).
