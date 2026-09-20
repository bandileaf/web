# CLAUDE.md

- This is a static HTML web service deployed with GitHub Pages.
- Changes are verified on the deployed site, so after editing files, commit and **push immediately**. (Overrides the global rule.)
- Still review the push for secrets and personal data first. The repo is public.

## Database (Supabase)

- Word data lives in Supabase (`morphemes`, `words`, `word_morphemes`; schema in `db/schema.sql`). The user adds and edits data **through Claude**.
- The site only reads with the publishable key in `index.html` (RLS allows SELECT only). Writes need the secret key.
- Read the secret key from the local env var `SUPABASE_SECRET_KEY` (or the gitignored `db/.env.local`). Never write it into any tracked file, commit, or chat output.
- Insert via the Supabase REST API (`/rest/v1/<table>`). Add rows to `words` and `morphemes` (if new), then link them in `word_morphemes` with `position` 1..3 (prefix, root, suffix).
- After inserting, re-read the tables to verify, and keep `db/schema.sql` seed data unchanged (it is only the initial seed).
