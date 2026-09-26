---
name: add-word
description: Maintain the Word Atlas Supabase DB. Verify a word's etymology (prefix / root / suffix) against Wiktionary and Etymonline, then add, fix, or re-check words, merge spelling variants, and verify DB integrity. Use when the user asks to add, register, check, fix, or maintain words (e.g. "predict 추가해줘", "이 단어 어원 확인하고 등록해줘", "남은 단어 검증 이어서 해줘", "DB 점검해줘").
---

# add-word

Check a word's morphology with two sources, get the user's confirmation, then insert it into Supabase.
Talk to the user in Korean. Never print the secret key.

## 0. Maintenance toolkit (`scripts/`, Python, key from env `SUPABASE_SECRET_KEY`)

Run from `.claude/skills/add-word/scripts/` (use Python, not PowerShell, for Korean text; write JSON files as UTF-8).

| script | use |
|---|---|
| `fetch_ety.py N` or `fetch_ety.py word ...` | next N words with `etym_checked_at` null (or the given words), current split + condensed Wiktionary etymology |
| `apply_fixes.py batch.json [--force]` | apply decisions; `keep` just stamps `etym_checked_at`; `split` writes `morpheme_ids` / `forms`, maps spelling variants to representatives, deletes orphaned morphemes. New words need `meaning_ko`. |
| `verify_all.py` | integrity + spelling check (BROKEN / FORM? / CLOSE / MISMATCH) and the count of unchecked words. Run after every batch; fix anything you introduced. |
| `merge_variants.py type rep "v1 v2" [--apply]` | merge spelling variants (ac/af/ap -> ad) into one representative; dry run by default |

Batch item: `{"word":"react","action":"keep"}` or `{"word":"react","action":"split","prefix":"re","prefix_meaning":"다시","root":"act","root_meaning":"행동하다","suffix":null}`. For a NEW root also give `"root_pos":{"noun":"서비스","verb":"제공하다"}` (stored in the `morphemes.noun/verb/adj/adv` text columns, each holding the Korean meaning as that part of speech; the site shows `n. 서비스, v. 제공하다`. Free roots like `service`/`grant` get every real part of speech, bound roots like `dict` only the one their meaning implies; prefixes/suffixes stay null). Part texts are the **actual spelling** (`ac`, not `ad`); the script maps variants to the representative.

**Progress** lives in the DB: `words.etym_checked_at` (null = not verified yet). Resume with `GET /words?etym_checked_at=is.null`. Continue in batches of ~40-50: fetch -> decide -> write `batchNN.json` (scratch dir, not the repo) -> apply -> verify.

**Decision policy** (per word, from Wiktionary + Etymonline):
- Split only if the affix is visible in the English spelling; accept e-drop, y-drop and consonant doubling.
- Keep unsplit when the etymology is unclear, native/Germanic, or a compound (root slot holds one root); unsplit = the word itself as its only root.
- Avoid homograph collisions (`anti` vs `ante`, `di` = dis variant vs Greek "two"); ask when unsure.
- Variant groups already merged: prefix ad, con, in, ex, dis, sub, ob, ab, pro, super, inter, trans; suffix able, ion, ent, ence, ity, ize, ify, al, ic, or (see `morphemes.variants`).
- Fix source typos in the word list (e.g. `phychologist` -> `psychologist`) before splitting.

**Schema changes** (ALTER/DROP) cannot go through REST: write a `db/migrate_v2_*.sql` file and ask the user to run it in the Supabase SQL Editor.

## 1. Look up the sources (per word, on demand)

Use both sources. Never bulk-crawl; fetch only the words the user asked for.

**Wiktionary** (primary, has an API, no key):
- Wikitext: `https://en.wiktionary.org/w/api.php?action=parse&page=<word>&prop=wikitext&format=json&formatversion=2`
- Send a `User-Agent` header (Wikimedia policy), e.g. `word-atlas/1.0 (https://github.com/bandileaf/web)`.
- Read the `===Etymology===` section for templates such as `{{af|en|pre-|dict|-ion}}`, `{{prefix|en|pre|dict}}`, `{{suffix|en|predict|ion}}`, `{{compound|...}}`, and the Latin/Greek origin (`{{der|en|la|dicere}}`).
- Templates vary: `predict` has no `{{af}}`; it reads `from {{m|la|prae-||before}} + {{m|la|dīcō||to say}}`. Map Latin/Greek parts to the English morphemes the site uses (`prae-` -> `pre`, `dīcō` -> `dict`), and confirm on Etymonline.
- Page view for the user: `https://en.wiktionary.org/wiki/<word>`

**Etymonline** (cross-check, no API):
- `WebFetch https://www.etymonline.com/word/<word>` (affixes: `/word/pre-`, `/word/-able`).
- Use it to confirm the root and its meaning (e.g. Latin *dicere* "to say"). Do not automate or scrape it beyond that single page per word.

## 2. Decide the decomposition

- Normally prefix + root + suffix (each optional). The graph shows one of each type per word; extra parts are stored but not drawn.
- Store morpheme text **without hyphens** (`pre`, `ion`); the `type` column says prefix / root / suffix.
- The root is the core morpheme: an English base (`use`, `happy`) or a bound Latin/Greek root (`dict`, `struct`, `port`), not a derived word. `prediction` = `pre` + `dict` + `ion`, not `predict` + `ion`.
- If spelling changes (`create` -> `creat` + `ion`), store the base form and say so.
- Prefer middle/high-school level words. Confirm the word is common enough.
- If Wiktionary and Etymonline disagree, or the etymology is unclear, say so and ask; do not guess.

## 3. Confirm before writing

The DB is public, so show a table and wait for the user's OK:

| word | 뜻 | prefix | root (뜻) | suffix | 출처(Wiktionary / Etymonline) |
|---|---|---|---|---|---|

Write concise Korean meanings (`meaning_ko`) for the word and for any new morpheme.
Do not copy long text from the sources; use only the facts (Wiktionary is CC BY-SA).

## 4. Insert into Supabase

Base: `https://gdqotnfcarjgfghourdm.supabase.co/rest/v1`, key from env var `SUPABASE_SECRET_KEY` (loaded by `C:\DEV\env.bat` through `cc.bat`). If it is empty, tell the user to fill `C:\DEV\env.bat` and restart with `cc.bat`. Never echo, log, or commit the key.

Headers: `apikey: $env:SUPABASE_SECRET_KEY`, `Content-Type: application/json`.

Schema v2: there is no `word_morphemes` table. A word stores its ordered morpheme ids and actual spellings itself:
- `words.morpheme_ids bigint[]` (e.g. `{3,15,24}`, shown as `3-15-24`), in word order: prefix, root, suffix.
- `words.forms text[]` (e.g. `{pre,dict,ion}`): the actual spelling of each part. For a variant such as `ac` in accept, `morpheme_ids` holds the representative (`ad`) and `forms` holds `ac`.
- `morphemes.variants text[]`: spelling variants of the representative `text` (`ad` -> `{ac,af,ap,ar,as,at}`). Before creating a morpheme, check `GET /morphemes?type=eq.<t>&variants=cs.{<x>}`; if `<x>` is a variant, reuse the representative.

Order (skip rows that already exist):
1. `GET /words?word=eq.<word>`: stop and report if it exists (ask whether to update).
2. `POST /morphemes?on_conflict=type,text` with `Prefer: resolution=ignore-duplicates,return=representation`, body `[{"type":"prefix","text":"pre","meaning_ko":"이전"}]`. New morphemes only; look up existing ids with `GET /morphemes?type=eq.<t>&text=eq.<x>`.
3. `POST /words` with `Prefer: return=representation`, body `{"word":"predict","meaning_ko":"예측하다","morpheme_ids":[3,15],"forms":["pre","dict"]}`. More than three parts is allowed.

Use `Invoke-RestMethod` in PowerShell with a UTF-8 body: `-Body ([Text.Encoding]::UTF8.GetBytes($json))`.

## 5. Verify

Re-read `words` and `morphemes` for the new rows, check every id in `morpheme_ids` exists and `forms` has the same length, and report the final `pre + dict + ion` style breakdown (with the `3-15-24` ids). The site reads the DB live, so no code change or push is needed. Tell the user to refresh (`Ctrl+F5`) to see the node on the graph.

Do not edit `db/schema.sql`; it is only the initial seed.
