# -*- coding: utf-8 -*-
"""Apply hand-verified decompositions. usage: apply_fixes.py batch.json [--force]

Model: words.parts (text[]) lists the ordered components of a word, each tagged with its table:
  'm12' = morphemes.id 12 (a prefix or suffix), 'w7' = words.id 7 (a root or another word).
  words.forms holds the actual spelling of each part. parts = [] means the word cannot be split (it is a root).

Item: {"word","action":"keep"}                      -> unsplittable; parts = []
   or {"word","action":"split","prefix":"un"|null,"prefix_meaning",
       "root":"happy","root_meaning","suffix":"able"|null,"suffix_meaning"}
   optional on any item: "meaning_ko" (short meaning, required to create a NEW word) and
   "pos": {"noun":"서비스","verb":"제공하다"} = the word's meaning per part of speech (words.noun/verb/adj/adv).
Prefix/suffix texts are the ACTUAL spelling; a text listed in morphemes.variants maps to its representative
(the spelling stays in words.forms). The root is a WORD: it is looked up in words (created if missing, as an
unchecked atomic word using root_meaning). Every processed word gets etym_checked_at.
Words that already have etym_checked_at are skipped unless --force."""
import sys, json, datetime
from sb import req, one, Q

POS = ("noun", "verb", "adj", "adv")


def morpheme_id(t, text, meaning):
    m = one(f"/morphemes?type=eq.{t}&text=eq.{Q(text)}&select=id")
    if m: return m["id"]
    m = one(f"/morphemes?type=eq.{t}&variants=cs.{{{Q(text)}}}&select=id")   # spelling variant -> representative
    if m: return m["id"]
    req("POST", "/morphemes?on_conflict=type,text", [{"type": t, "text": text, "meaning_ko": meaning}],
        "resolution=ignore-duplicates,return=minimal")
    return one(f"/morphemes?type=eq.{t}&text=eq.{Q(text)}&select=id")["id"]


def word_id(text, meaning):
    w = one(f"/words?word=eq.{Q(text)}&select=id")
    if w: return w["id"]
    req("POST", "/words", {"word": text, "meaning_ko": meaning or text}, "return=minimal")
    return one(f"/words?word=eq.{Q(text)}&select=id")["id"]


def apply_one(item, force):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    w = one(f"/words?word=eq.{Q(item['word'])}&select=id,parts,etym_checked_at")
    if not w:
        if not item.get("meaning_ko"): return "NO-WORD (add meaning_ko to insert)"
        req("POST", "/words", {"word": item["word"], "meaning_ko": item["meaning_ko"]}, "return=minimal")
        w = one(f"/words?word=eq.{Q(item['word'])}&select=id,parts,etym_checked_at")
    if w["etym_checked_at"] and not force: return "skip-checked"
    patch = {"etym_checked_at": now}
    patch.update({k: v for k, v in (item.get("pos") or {}).items() if k in POS})
    if item["action"] == "keep":
        patch.update(parts=[], forms=[])
        req("PATCH", f"/words?id=eq.{w['id']}", patch, "return=minimal")
        return "keep"
    parts, forms = [], []
    if item.get("prefix"):
        parts.append(f"m{morpheme_id('prefix', item['prefix'], item.get('prefix_meaning', ''))}"); forms.append(item["prefix"])
    rid = word_id(item["root"], item.get("root_meaning", ""))
    if rid == w["id"]: return "ERROR: root equals the word itself (use keep)"
    parts.append(f"w{rid}"); forms.append(item["root"])
    if item.get("suffix"):
        parts.append(f"m{morpheme_id('suffix', item['suffix'], item.get('suffix_meaning', ''))}"); forms.append(item["suffix"])
    patch.update(parts=parts, forms=forms)
    req("PATCH", f"/words?id=eq.{w['id']}", patch, "return=minimal")
    for old in set(w["parts"]) - set(parts):                         # delete prefix/suffix nobody uses any more
        if old[0] == "m" and not one(f"/words?parts=cs.{{{old}}}&select=id"):
            req("DELETE", f"/morphemes?id=eq.{old[1:]}", prefer="return=minimal")
    return "fixed"


if __name__ == "__main__":
    force, res = "--force" in sys.argv, {}
    for item in json.load(open(sys.argv[1], encoding="utf-8-sig")):
        try: r = apply_one(item, force)
        except Exception as e: r = "ERROR:" + str(e)
        k = r.split(":")[0]; res[k] = res.get(k, 0) + 1
        print(item["word"], "->", r)
    print("summary:", res)
