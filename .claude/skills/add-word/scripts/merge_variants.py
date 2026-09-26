# -*- coding: utf-8 -*-
"""Merge spelling variants into one representative morpheme.
usage: merge_variants.py <type> <rep> "<v1 v2 ...>" [--apply]      (dry run without --apply)
e.g.   merge_variants.py prefix ad "ac af ap ar as at" --apply
Every word using a variant morpheme is remapped to the representative (its words.forms keep the actual
spelling), the representative gets the variants in morphemes.variants, variant rows are deleted.
Variants that have no morpheme row yet are still recorded so future words map to the representative."""
import sys
from sb import req, all_, one, Q

t, rep, variants = sys.argv[1], sys.argv[2], sys.argv[3].split()
apply = "--apply" in sys.argv
r = one(f"/morphemes?type=eq.{t}&text=eq.{Q(rep)}&select=id,variants")
if not r: sys.exit(f"no representative {t}:{rep}")
rows = {v: one(f"/morphemes?type=eq.{t}&text=eq.{Q(v)}&select=id") for v in variants}
remap = {m["id"]: r["id"] for m in rows.values() if m}
changed = []
for w in all_("words"):
    new = []
    for i in w["morpheme_ids"]:
        i = remap.get(i, i)
        if i not in new: new.append(i)
    if new != w["morpheme_ids"]: changed.append((w["id"], w["word"], new))
print(f"{t}:{rep} <- {variants}; morphemes to delete {len(remap)}, words to remap {len(changed)}")
for c in changed[:5]: print("  ", c)
if not apply: sys.exit("dry run (add --apply)")
req("PATCH", f"/morphemes?id=eq.{r['id']}", {"variants": sorted(set(r["variants"]) | set(variants))}, "return=minimal")
for wid, _, new in changed: req("PATCH", f"/words?id=eq.{wid}", {"morpheme_ids": new}, "return=minimal")
if remap:
    req("DELETE", f"/morphemes?id=in.({','.join(map(str, remap))})", prefer="return=minimal")
print("done")
