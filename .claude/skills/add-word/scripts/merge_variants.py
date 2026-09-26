# -*- coding: utf-8 -*-
"""Merge spelling variants of a PREFIX or SUFFIX into one representative morpheme.
usage: merge_variants.py <prefix|suffix> <rep> "<v1 v2 ...>" [--apply]      (dry run without --apply)
e.g.   merge_variants.py prefix ad "ac af ap ar as at" --apply
Every word whose parts use a variant morpheme ('m<id>') is remapped to the representative (words.forms keep the
actual spelling), the representative gets the variants in morphemes.variants, variant rows are deleted.
Variants that have no morpheme row yet are still recorded so future words map to the representative."""
import sys
from sb import req, all_, one, Q

t, rep, variants = sys.argv[1], sys.argv[2], sys.argv[3].split()
if t not in ("prefix", "suffix"): sys.exit("type must be prefix or suffix (roots are words now)")
apply = "--apply" in sys.argv
r = one(f"/morphemes?type=eq.{t}&text=eq.{Q(rep)}&select=id,variants")
if not r: sys.exit(f"no representative {t}:{rep}")
rows = {v: one(f"/morphemes?type=eq.{t}&text=eq.{Q(v)}&select=id") for v in variants}
remap = {f"m{m['id']}": f"m{r['id']}" for m in rows.values() if m}
changed = []
for w in all_("words"):
    parts, forms, seen = [], [], set()
    for p, f in zip(w["parts"], w["forms"]):
        p = remap.get(p, p)
        if p in seen: continue                                         # a word using both variants keeps one
        seen.add(p); parts.append(p); forms.append(f)
    if parts != w["parts"]: changed.append((w["id"], w["word"], parts, forms))
print(f"{t}:{rep} <- {variants}; morphemes to delete {len(remap)}, words to remap {len(changed)}")
for c in changed[:5]: print("  ", c)
if not apply: sys.exit("dry run (add --apply)")
req("PATCH", f"/morphemes?id=eq.{r['id']}", {"variants": sorted(set(r["variants"]) | set(variants))}, "return=minimal")
for wid, _, parts, forms in changed: req("PATCH", f"/words?id=eq.{wid}", {"parts": parts, "forms": forms}, "return=minimal")
if remap:
    req("DELETE", f"/morphemes?id=in.({','.join(k[1:] for k in remap)})", prefer="return=minimal")
print("done")
