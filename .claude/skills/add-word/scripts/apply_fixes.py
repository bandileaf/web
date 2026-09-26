# -*- coding: utf-8 -*-
"""Apply hand-verified decompositions. usage: apply_fixes.py batch.json [--force]
Item: {"word","action":"keep"}
   or {"word","action":"split","prefix","prefix_meaning","root","root_meaning","suffix","suffix_meaning"}
Part texts are the ACTUAL spelling in the word. If a text is listed in morphemes.variants, the
representative morpheme id is used and the spelling is stored in words.forms.
"root_pos": {"noun":"서비스","verb":"제공하다"} sets the root's meaning per part of speech when the root is NEW
(keys noun|verb|adj|adv -> morphemes columns; a free root gets every real part of speech, a bound
Latin/Greek root the one its meaning implies).
A new word (not in DB) needs "meaning_ko" and is inserted. Every processed word gets etym_checked_at.
Words that already have etym_checked_at are skipped unless --force."""
import sys, datetime
from sb import req, one, Q


def morpheme_id(t, text, meaning, pos=None):
    m = one(f"/morphemes?type=eq.{t}&text=eq.{Q(text)}&select=id")
    if m: return m["id"]
    m = one(f"/morphemes?type=eq.{t}&variants=cs.{{{Q(text)}}}&select=id")   # spelling variant -> representative
    if m: return m["id"]
    row = {"type": t, "text": text, "meaning_ko": meaning}
    if t == "root" and pos:                           # roots only: per-POS meaning columns
        row.update({k: v for k, v in pos.items() if k in ("noun", "verb", "adj", "adv") and v})
    req("POST", "/morphemes?on_conflict=type,text", [row], "resolution=ignore-duplicates,return=minimal")
    return one(f"/morphemes?type=eq.{t}&text=eq.{Q(text)}&select=id")["id"]


def apply_one(item, force):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    w = one(f"/words?word=eq.{Q(item['word'])}&select=id,morpheme_ids,etym_checked_at")
    if not w:
        if not item.get("meaning_ko"): return "NO-WORD (add meaning_ko to insert)"
        req("POST", "/words", {"word": item["word"], "meaning_ko": item["meaning_ko"]}, "return=minimal")
        w = one(f"/words?word=eq.{Q(item['word'])}&select=id,morpheme_ids,etym_checked_at")
    if w["etym_checked_at"] and not force: return "skip-checked"
    if item["action"] == "keep":
        if not w["morpheme_ids"]:                                  # brand-new unsplit word: root = itself
            i = morpheme_id("root", item["word"], item.get("meaning_ko", ""), item.get("root_pos"))
            req("PATCH", f"/words?id=eq.{w['id']}", {"morpheme_ids": [i], "forms": [item["word"]]}, "return=minimal")
        req("PATCH", f"/words?id=eq.{w['id']}", {"etym_checked_at": now}, "return=minimal")
        return "keep"
    parts = []
    if item.get("prefix"): parts.append(("prefix", item["prefix"], item.get("prefix_meaning", "")))
    parts.append(("root", item["root"], item.get("root_meaning", "")))
    if item.get("suffix"): parts.append(("suffix", item["suffix"], item.get("suffix_meaning", "")))
    ids = [morpheme_id(t, x, m, item.get("root_pos")) for t, x, m in parts]
    req("PATCH", f"/words?id=eq.{w['id']}", {"morpheme_ids": ids, "forms": [x for _, x, _ in parts],
                                             "etym_checked_at": now}, "return=minimal")
    for old in set(w["morpheme_ids"]) - set(ids):                  # delete morphemes nobody uses any more
        if not one(f"/words?morpheme_ids=cs.{{{old}}}&select=id"):
            req("DELETE", f"/morphemes?id=eq.{old}", prefer="return=minimal")
    return "fixed"


if __name__ == "__main__":
    import json
    force, res = "--force" in sys.argv, {}
    for item in json.load(open(sys.argv[1], encoding="utf-8-sig")):
        try: r = apply_one(item, force)
        except Exception as e: r = "ERROR:" + str(e)
        k = r.split(":")[0]; res[k] = res.get(k, 0) + 1
        print(item["word"], "->", r)
    print("summary:", res)
