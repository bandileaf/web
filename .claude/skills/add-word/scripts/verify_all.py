# -*- coding: utf-8 -*-
"""Integrity + spelling check of the whole DB. usage: verify_all.py
BROKEN   parts/forms length differ, a reference does not exist, a word refers to itself, or a cycle
FORM?    a form is not the referenced word/morpheme text (or a listed variant)
CLOSE    joined forms differ from the word by <=1 char (e/y-drop, doubling): review, usually fine
MISMATCH joined forms do not reconstruct the word: fix it
Model: words.parts = ['m12' (prefix/suffix), 'w7' (word/root)]; parts = [] means the word is a root."""
from sb import all_

ms = {m["id"]: m for m in all_("morphemes")}
ws = {w["id"]: w for w in all_("words")}
bad, split = [], 0
for w in ws.values():
    parts, forms = w["parts"], w["forms"]
    if len(parts) != len(forms): bad.append(("BROKEN", w["word"], forms, "parts/forms length")); continue
    ok = True
    for p, f in zip(parts, forms):
        t, i = p[0], int(p[1:])
        if t == "m":
            if i not in ms: bad.append(("BROKEN", w["word"], forms, p)); ok = False
            elif ms[i]["type"] == "root": bad.append(("BROKEN", w["word"], forms, p + " (root morpheme is obsolete)")); ok = False
            elif f != ms[i]["text"] and f not in ms[i]["variants"]: bad.append(("FORM?", w["word"], forms, f))
        elif t == "w":
            if i not in ws: bad.append(("BROKEN", w["word"], forms, p)); ok = False
            elif i == w["id"]: bad.append(("BROKEN", w["word"], forms, "refers to itself")); ok = False
            elif f != ws[i]["word"]: bad.append(("FORM?", w["word"], forms, f + " != " + ws[i]["word"]))
        else: bad.append(("BROKEN", w["word"], forms, p)); ok = False
    if not parts or not ok: continue
    split += 1
    word, joined = w["word"].lower(), "".join(forms)
    if word == joined or word == joined + "e" or word == joined[:-1] + "e": continue
    tag = "CLOSE" if abs(len(word) - len(joined)) <= 1 and word[:2] == joined[:2] else "MISMATCH"
    bad.append((tag, w["word"], forms, joined))

def cyc(i, seen):                                                    # cycle detection through 'w' parts
    if i in seen: return True
    return any(cyc(int(p[1:]), seen | {i}) for p in ws[i]["parts"] if p[0] == "w" and int(p[1:]) in ws)
for i, w in ws.items():
    if cyc(i, frozenset()): bad.append(("BROKEN", w["word"], w["forms"], "cycle")); break

used_m = {int(p[1:]) for w in ws.values() for p in w["parts"] if p[0] == "m"}
used_w = {int(p[1:]) for w in ws.values() for p in w["parts"] if p[0] == "w"}
roots = [i for i in used_w if i in ws and not ws[i]["parts"]]
print(f"words {len(ws)}, split {split}, roots (unsplit, used by others) {len(roots)}, "
      f"morphemes {len(ms)}, unused morphemes {len(set(ms) - used_m)}, "
      f"unchecked {sum(1 for w in ws.values() if not w['etym_checked_at'])}, flagged {len(bad)}")
for t, word, forms, j in bad: print(f"[{t}] {word:16} forms={forms} {j}")
