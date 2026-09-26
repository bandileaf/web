# -*- coding: utf-8 -*-
"""Integrity + spelling check of the whole DB. usage: verify_all.py
BROKEN   morpheme_ids/forms length differ or an id does not exist
FORM?    a form is neither the representative text nor one of its variants
CLOSE    joined forms differ from the word by <=1 char (e/y-drop, doubling): review, usually fine
MISMATCH joined forms do not reconstruct the word: fix it
Also prints how many words still have etym_checked_at = null."""
from sb import all_

ms = {m["id"]: m for m in all_("morphemes")}
ws = all_("words")
bad, n = [], 0
for w in ws:
    ids, forms = w["morpheme_ids"], w["forms"]
    if not ids: bad.append(("BROKEN", w["word"], forms, "no morpheme_ids")); continue
    if len(forms) != len(ids) or any(i not in ms for i in ids):
        bad.append(("BROKEN", w["word"], forms, ids)); continue
    for f, i in zip(forms, ids):
        if f != ms[i]["text"] and f not in ms[i]["variants"]: bad.append(("FORM?", w["word"], forms, f))
    if len(ids) < 2: continue
    n += 1
    word, joined = w["word"].lower(), "".join(forms)
    if word == joined or word == joined + "e" or word == joined[:-1] + "e": continue
    tag = "CLOSE" if abs(len(word) - len(joined)) <= 1 and word[:2] == joined[:2] else "MISMATCH"
    bad.append((tag, w["word"], forms, joined))
used = {i for w in ws for i in w["morpheme_ids"]}
print(f"words {len(ws)}, split {n}, morphemes {len(ms)}, unused morphemes {len(set(ms) - used)}, "
      f"unchecked {sum(1 for w in ws if not w['etym_checked_at'])}, flagged {len(bad)}")
for t, word, forms, j in bad: print(f"[{t}] {word:16} forms={forms} {j}")
