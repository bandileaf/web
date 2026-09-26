# -*- coding: utf-8 -*-
"""Apply hand-verified decompositions. usage: apply_fixes.py batch.json [--force]

Model: words.parts (text[]) lists the ordered components of a word, each tagged with its table:
  'm12' = morphemes.id 12 (a prefix or suffix), 'w7' = words.id 7 (a root or another word).
  words.forms holds the actual spelling of each part. parts = [] means the word cannot be split (it is a root).

Item: {"word","action":"keep"}                      -> unsplittable; parts = []
   or {"word","action":"split","prefix":"un"|null,"prefix_meaning","root":"happy","suffix":"able"|null,"suffix_meaning"}
   "pos": {"noun":"서비스","verb":"제공하다"} = the word's meaning per part of speech
   (words.noun/verb/adj/adv/prep/conj; several senses in one column separated by " / "). Required to create a
   NEW word; on an existing word it overwrites only the given columns.
   "root_pos": same shape, required when the root is not in words yet (it is created as an unchecked word).
Prefix/suffix texts are the ACTUAL spelling; a text listed in morphemes.variants maps to its representative
(the spelling stays in words.forms). The root is a WORD, looked up in words. Words have no meaning_ko any more.
Every processed word gets etym_checked_at.
Words that already have etym_checked_at are skipped unless --force."""
import sys, json, datetime
from sb import req, one, Q

POS = ("noun", "verb", "adj", "adv", "prep", "conj")


def insert_word(word, pos):
    """Create an unchecked word whose meaning is given per part of speech (pos = {"noun": "서비스", ...})."""
    pos = {k: v for k, v in (pos or {}).items() if k in POS and v}
    if not pos: raise RuntimeError(f"new word '{word}' needs a part-of-speech meaning (pos / root_pos)")
    row = {"word": word, **pos}
    try:
        req("POST", "/words", row, "return=minimal")
    except RuntimeError as e:
        if "23502" not in str(e): raise                       # legacy NOT NULL meaning_ko (until schema step 6)
        req("POST", "/words", {**row, "meaning_ko": next(iter(pos.values()))}, "return=minimal")


def morpheme_id(t, text, meaning):
    m = one(f"/morphemes?type=eq.{t}&text=eq.{Q(text)}&select=id")
    if m: return m["id"]
    m = one(f"/morphemes?type=eq.{t}&variants=cs.{{{Q(text)}}}&select=id")   # spelling variant -> representative
    if m: return m["id"]
    req("POST", "/morphemes?on_conflict=type,text", [{"type": t, "text": text, "meaning_ko": meaning}],
        "resolution=ignore-duplicates,return=minimal")
    return one(f"/morphemes?type=eq.{t}&text=eq.{Q(text)}&select=id")["id"]


def word_id(text, pos):
    w = one(f"/words?word=eq.{Q(text)}&select=id")
    if w: return w["id"]
    insert_word(text, pos)
    return one(f"/words?word=eq.{Q(text)}&select=id")["id"]


def apply_one(item, force):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    w = one(f"/words?word=eq.{Q(item['word'])}&select=id,parts,etym_checked_at")
    if not w:
        insert_word(item["word"], item.get("pos"))                 # a new word needs its "pos" meanings
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
    rid = word_id(item["root"], item.get("root_pos"))
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
