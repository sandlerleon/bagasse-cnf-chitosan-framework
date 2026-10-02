# -*- coding: utf-8 -*-
"""Scan OpenAlex abstracts for sentences that literally state a quantity, so a numeric
claim can be cited to text I have read rather than to a title."""
import json, re, sys, urllib.parse, urllib.request
UA = {"User-Agent": "tncc-ref-harvest/1.0 (mailto:sandler.leon@gmail.com)"}

def abstract_of(w):
    inv = w.get("abstract_inverted_index")
    if not inv:
        return ""
    pos = {}
    for word, idx in inv.items():
        for i in idx:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))

def scan(query, must, rows=40):
    u = "https://api.openalex.org/works?search=%s&per-page=%d&filter=type:article" % (
        urllib.parse.quote(query), rows)
    j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read())
    for w in j["results"]:
        ab = abstract_of(w)
        sents = [s for s in re.split(r"(?<=[.;])\s+", ab) if all(re.search(m, s, re.I) for m in must)]
        if sents:
            a = (w.get("authorships") or [{}])[0].get("author", {}).get("display_name", "")
            print("- %s (%s) %s\n    doi: %s | %s" % (a, w.get("publication_year"),
                  (w.get("title") or "")[:90], w.get("doi"), (w.get("primary_location") or {}).get("source", {}) and w["primary_location"]["source"].get("display_name")))
            for s in sents[:2]:
                print("    >> " + s[:330])

if __name__ == "__main__":
    scan(sys.argv[1], sys.argv[2].split("&&"), int(sys.argv[3]) if len(sys.argv) > 3 else 40)
