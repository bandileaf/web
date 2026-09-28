# -*- coding: utf-8 -*-
"""Daily-use importance (1 = most common .. 5 = rarest, None = not found in either list).

Source: Oxford 5000 (CEFR a1-c1) first; words it misses fall back to the BNC/COCA 25k word-family
list, whose 1k-25k frequency band is bucketed into 5 (1-5k->1 ... 21-25k->5). Both lists are
snapshotted under data/ (built from oxfordlearnersdictionaries.com and eapfoundation.com/vocab/general/bnccoca,
2026-09) so lookups work offline. Bound Latin/Greek roots (dict, spect) are real words in neither list
and correctly come back None."""
import csv, io, os, re

_DIR = os.path.join(os.path.dirname(__file__), "data")


def _load(path, val):
    out = {}
    with io.open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["word"]] = val(row)
    return out


_OXFORD = _load(os.path.join(_DIR, "oxford5000_cefr.csv"), lambda r: int(r["level"]))
_COCA = _load(os.path.join(_DIR, "coca_bnc_band.csv"), lambda r: int(r["band"]))

# British <-> American spelling variants (both source lists are British-spelled)
_SUF_PAIRS = [("ize", "ise"), ("ized", "ised"), ("izes", "ises"), ("izing", "ising"), ("ization", "isation"),
              ("yze", "yse"), ("yzed", "ysed"), ("yzes", "yses"), ("yzing", "ysing")]


def _variants(w):
    out = set()
    if w.endswith("or") and len(w) > 4: out.add(w[:-2] + "our")             # labor -> labour
    if w.endswith("er") and len(w) > 4: out.add(w[:-2] + "re")              # center -> centre
    for suf, rep in _SUF_PAIRS:
        if w.endswith(suf): out.add(w[:-len(suf)] + rep)                    # analyze -> analyse
    if w.endswith("og") and len(w) > 4: out.add(w + "ue")                   # catalog -> catalogue
    if re.search(r"[bcdfgklmnprstz]$", w) and len(w) > 3:                   # fulfill <-> fulfil
        out.add(w + w[-1])
        if len(w) > 1 and w[-1] == w[-2]: out.add(w[:-1])
    return out


def importance_of(word):
    w = word.strip().lower()
    if w in _OXFORD: return _OXFORD[w]
    for v in _variants(w):
        if v in _OXFORD: return _OXFORD[v]
    if w in _COCA: return (_COCA[w] - 1) // 5 + 1
    for v in _variants(w):
        if v in _COCA: return (_COCA[v] - 1) // 5 + 1
    return None


if __name__ == "__main__":                                                  # quick check: importance.py word ...
    import sys
    for w in sys.argv[1:]: print(w, "->", importance_of(w))
