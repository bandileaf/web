---
name: add-word
description: Verify a word's etymology (prefix / root / suffix) against Wiktionary and Etymonline, then register it in the Word Atlas Supabase DB. Use when the user asks to add, register, check, or fix a word (e.g. "predict 추가해줘", "이 단어 어원 확인하고 등록해줘").
---

# add-word

Check a word's morphology with two sources, get the user's confirmation, then insert it into Supabase.
Talk to the user in Korean. Never print the secret key.

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

- One prefix, one root, one suffix at most per word (the site reads one of each). Leave a slot empty if there is none.
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

Order (skip rows that already exist):
1. `GET /words?word=eq.<word>`: stop and report if it exists (ask whether to update).
2. `POST /morphemes?on_conflict=type,text` with `Prefer: resolution=ignore-duplicates,return=representation`, body `[{"type":"prefix","text":"pre","meaning_ko":"이전"}]`. New morphemes only; look up existing ids with `GET /morphemes?type=eq.<t>&text=eq.<x>`.
3. `POST /words` with `Prefer: return=representation`, body `{"word":"predict","meaning_ko":"예측하다"}`.
4. `POST /word_morphemes` with body `[{"word_id":..,"morpheme_id":..,"position":1},...]`, position 1 = prefix, 2 = root, 3 = suffix (keep the order; numbers may skip when a slot is empty).

Use `Invoke-RestMethod` in PowerShell with a UTF-8 body: `-Body ([Text.Encoding]::UTF8.GetBytes($json))`.

## 5. Verify

Re-read `words`, `morphemes`, `word_morphemes` for the new rows and report counts and the final `pre + dict + ion` style breakdown. The site reads the DB live, so no code change or push is needed. Tell the user to refresh (`Ctrl+F5`) to see the node on the graph.

Do not edit `db/schema.sql`; it is only the initial seed.
