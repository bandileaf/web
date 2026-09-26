# -*- coding: utf-8 -*-
"""usage: fetch_ety.py N | fetch_ety.py word1 word2 ...
With a number: the next N words whose etym_checked_at is null, with the current split and a
condensed Wiktionary English etymology. With words: just those words. Fetch one page per word;
never bulk-crawl beyond the batch you are deciding."""
import sys, re, json, urllib.request, urllib.parse
from sb import all_, req, Q

ms = {m["id"]: m for m in all_("morphemes")}


def ety(word):
    u = ("https://en.wiktionary.org/w/api.php?action=parse&prop=wikitext&format=json&formatversion=2&page="
         + urllib.parse.quote(word))
    r = urllib.request.Request(u, headers={"User-Agent": "word-atlas/1.0 (https://github.com/bandileaf/web)"})
    try: t = json.loads(urllib.request.urlopen(r, timeout=20).read())["parse"]["wikitext"]
    except Exception as e: return "ERR " + str(e)
    m = re.search(r"==English==(.*?)(\n==[^=]|\Z)", t, re.S)
    if not m: return "no English section"
    out = []
    for e in re.findall(r"===+Etymology[ 0-9]*===+\s*(.*?)(?=\n===|\Z)", m.group(1), re.S):
        e = re.sub(r"\{\{(?:cog|cog\+|l|link)\|[^}]*\}\}", "", e)
        e = re.sub(r"\{\{(?:m|m\+|der|inh|bor|af|affix|prefix|suffix|compound|surf|root|con|confix)\|([^}]*)\}\}",
                   lambda x: "{" + x.group(0)[2:-2] + "}", e)
        out.append(re.sub(r"\s+", " ", e)[:330])
    return " || ".join(out)[:700] or "(none)"


if sys.argv[1].isdigit():
    todo = [w for w in all_("words") if not w["etym_checked_at"]][:int(sys.argv[1])]
else:
    todo = [w for a in sys.argv[1:] for w in req("GET", f"/words?word=eq.{Q(a)}") or [{"word": a, "meaning_ko": "?", "morpheme_ids": []}]]
for w in todo:
    cur = "+".join(ms[i]["text"] for i in w["morpheme_ids"] if i in ms)
    print(f"## {w['word']} [{cur}] {w['meaning_ko']}\n   {ety(w['word'])}")
