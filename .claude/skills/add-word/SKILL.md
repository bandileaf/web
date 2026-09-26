---
name: add-word
description: Maintain the Word Atlas Supabase DB. Verify a word's etymology (prefix / root / suffix) against Wiktionary and Etymonline, then add, fix, or re-check words, merge spelling variants, and verify DB integrity. Use when the user asks to add, register, check, fix, or maintain words (e.g. "predict 추가해줘", "이 단어 어원 확인하고 등록해줘", "남은 단어 검증 이어서 해줘", "DB 점검해줘").
---

# add-word

Check a word's morphology with two sources, get the user's confirmation, then write it to Supabase.
Talk to the user in Korean. Never print the secret key.

## 0. Data model (schema v2)

Two tables. **Everything that is a word or a root lives in `words`; `morphemes` holds only prefixes and suffixes.**

- `words`: `word` (unique), `meaning_ko` (short summary), `noun` / `verb` / `adj` / `adv` (the meaning as that part of speech, null = not that POS; several senses in one column are separated by ` / `; the site shows `n. 서비스, v. 제공하다`), `parts text[]`, `forms text[]`, `etym_checked_at`.
- `words.parts`: the ordered components of the word, each tagged with its table: `m12` = `morphemes.id` 12 (a prefix or suffix), `w7` = `words.id` 7 (a root or another word). **`parts = []` means the word cannot be split, i.e. it is a root.** A root is simply an unsplit word that other words use (`break`, `use`, `dict`, `mit`). A word used as a component is drawn once in the graph.
  - `prediction` = `{m(pre), w(dict), m(ion)}`; `compassion` = `{m(con), w(passion)}`; `benefit` = `{}`.
- `words.forms`: the actual spelling of each part, same order as `parts` (`{com,passion}` for a variant `com` of the representative prefix `con`).
- `morphemes`: `type` prefix|suffix, `text` (representative, no hyphen), `meaning_ko`, `variants text[]` (spelling variants: `ad` -> `{ac,af,ap,ar,as,at}`); `unique(type,text)`.
- Bound Latin/Greek roots that are not English words (`dict`, `spect`) are unsplit `words` rows with the one part of speech their meaning implies. If a root's spelling equals a real English word with another meaning (`pair` worse / a pair, `fat`, `not`), keep ONE row and give each sense its part-of-speech column.
- `words.morpheme_ids` and `words.kind` are obsolete (to be dropped); never write them.
- DDL (ALTER/DROP) cannot go through REST: write a `db/migrate_v2_*.sql` file and ask the user to run it in the Supabase SQL Editor.

## 1. Maintenance toolkit (`scripts/`, Python, key from env `SUPABASE_SECRET_KEY`)

Run from `.claude/skills/add-word/scripts/` (use Python, not PowerShell, for Korean text; write JSON files as UTF-8).

| script | use |
|---|---|
| `fetch_ety.py N` or `fetch_ety.py word ...` | next N words with `etym_checked_at` null (or the given words), current split + condensed Wiktionary etymology |
| `apply_fixes.py batch.json [--force]` | apply decisions; `keep` = unsplit (`parts = []`) and stamps `etym_checked_at`; `split` writes `parts` / `forms`, looks the root up in `words` (creates it if missing), maps prefix/suffix variants to representatives, deletes orphaned prefixes/suffixes. A NEW word needs `meaning_ko`; `pos` sets its noun/verb/adj/adv columns. |
| `verify_all.py` | integrity + spelling check (BROKEN / FORM? / CLOSE / MISMATCH), root count, unchecked count. Run after every batch; fix anything you introduced. |
| `merge_variants.py prefix\|suffix rep "v1 v2" [--apply]` | merge spelling variants (ac/af/ap -> ad) into one representative; dry run by default |

Batch item: `{"word":"react","action":"keep"}` or `{"word":"react","action":"split","prefix":"re","prefix_meaning":"다시","root":"act","root_meaning":"행동하다","suffix":null,"pos":{"verb":"반응하다"}}`. Prefix/suffix/root texts are the **actual spelling** (`ac`, not `ad`); the script maps variants to the representative.

**Progress** lives in the DB: `words.etym_checked_at` (null = not verified yet). Resume with `GET /words?etym_checked_at=is.null`. Work in batches of ~40-50: fetch -> decide -> write `batchNN.json` (scratch dir, not the repo) -> apply -> verify.

**Decision policy** (per word, from Wiktionary + Etymonline):
- Split only if the affix is visible in the English spelling; accept e-drop, y-drop and consonant doubling.
- Keep unsplit when the etymology is unclear, native/Germanic, or a compound (there is one root slot); unsplit = root.
- A root must not be a derived word: `passion` is not a root (`pass` + `ion`); split such words too.
- Avoid homograph collisions (`anti` vs `ante`, `di` = dis variant vs Greek "two"); ask when unsure.
- Variant groups already merged: prefix ad, con, in, ex, dis, sub, ob, ab, pro, super, inter, trans; suffix able, ion, ent, ence, ity, ize, ify, al, ic, or (see `morphemes.variants`).
- Fix source typos in the word list (e.g. `phychologist` -> `psychologist`) before splitting.

## 2. Look up the sources (per word, on demand)

Use both sources. Never bulk-crawl; fetch only the words being decided.

**Wiktionary** (primary, has an API, no key):
- Wikitext: `https://en.wiktionary.org/w/api.php?action=parse&page=<word>&prop=wikitext&format=json&formatversion=2`
- Send a `User-Agent` header (Wikimedia policy), e.g. `word-atlas/1.0 (https://github.com/bandileaf/web)`.
- Read the `===Etymology===` section for templates such as `{{af|en|pre-|dict|-ion}}`, `{{prefix|en|pre|dict}}`, `{{suffix|en|predict|ion}}`, `{{compound|...}}`, and the Latin/Greek origin (`{{der|en|la|dicere}}`).
- Templates vary: `predict` has no `{{af}}`; it reads `from {{m|la|prae-||before}} + {{m|la|dīcō||to say}}`. Map Latin/Greek parts to the English pieces the site uses (`prae-` -> `pre`, `dīcō` -> `dict`), and confirm on Etymonline.
- Page view for the user: `https://en.wiktionary.org/wiki/<word>`

**Etymonline** (cross-check, no API):
- `WebFetch https://www.etymonline.com/word/<word>` (affixes: `/word/pre-`, `/word/-able`).
- Use it to confirm the root and its meaning (e.g. Latin *dicere* "to say"). Do not automate or scrape it beyond that single page per word.

## 3. Decide and confirm before writing

Normally prefix + root + suffix (each optional; more parts are stored, the graph draws one of each). Store prefix/suffix text **without hyphens**. If spelling changes (`create` -> `creat` + `ion`), store the base form and say so. Prefer middle/high-school words. If Wiktionary and Etymonline disagree, or the etymology is unclear, say so and ask; do not guess.

The DB is public, so for new words show a table and wait for the user's OK:

| word | 뜻 (n./v./adj.) | prefix | root | suffix | 출처(Wiktionary / Etymonline) |
|---|---|---|---|---|---|

Write concise Korean meanings. Do not copy long text from the sources; use only the facts (Wiktionary is CC BY-SA).

## 4. Write to Supabase

Use `apply_fixes.py` (it handles lookup, creation, variants and orphans). Key comes from env var `SUPABASE_SECRET_KEY` (loaded by `C:\DEV\env.bat` through `cc.bat`); if empty, tell the user to fill `C:\DEV\env.bat` and restart with `cc.bat`. Never echo, log, or commit the key. For a one-off REST call keep to: `GET /words?word=eq.<w>`, `POST /morphemes?on_conflict=type,text` (`Prefer: resolution=ignore-duplicates`), `POST /words`, `PATCH /words?id=eq.<id>` with `parts` / `forms` / `noun|verb|adj|adv`.

## 5. Verify

Run `verify_all.py`, then report the final `pre + dict + ion` style breakdown and the part-of-speech meanings. The site reads the DB live, so no code change or push is needed. Tell the user to refresh (`Ctrl+F5`) to see the node on the graph.

Do not edit `db/schema.sql`; it is only the initial seed.
