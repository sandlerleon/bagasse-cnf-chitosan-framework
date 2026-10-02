# -*- coding: utf-8 -*-
"""Documented literature searches behind the manuscript's statements of absence.

The manuscript says that no report of thermoforming or deep-drawing a dense nanocellulose
sheet, and no optical data for transparent bagasse-CNF sheets, was found. A statement of
absence is only as good as the search behind it, so each query, the date, the source and
the returned titles are recorded here and reproduced in SI Section S4. Relevance was judged
by reading every returned title; a hit is listed as relevant only if it concerns the thing
searched for.

    python search_log.py   ->  search_log.md
"""
import datetime
import json
import os
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "tncc-search-log/1.0 (mailto:sandler.leon@gmail.com)"}
QUERIES = [
    ("F1", "thermoforming of cellulose nanofibril films"),
    ("F2", "deep drawing nanocellulose film"),
    ("F3", "thermoformable nanopaper three-dimensional shaping"),
    ("F4", "hot pressing mold forming cellulose nanofibril sheet cup"),
    ("B1", "sugarcane bagasse cellulose nanofibril film optical transmittance haze"),
    ("B2", "transparent nanopaper from sugarcane bagasse"),
    ("B3", "agricultural residue cellulose nanofibril transparent film total transmittance"),
    ("W1", "wax coating transparent cellulose nanofibril film haze"),
    ("C1", "chitosan cellulose nanofibril transparent film wet strength"),
]


def fetch(q, n=12):
    u = "https://api.openalex.org/works?search=%s&per-page=%d&filter=type:article" % (urllib.parse.quote(q), n)
    j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read())
    out = []
    for w in j["results"]:
        a = ((w.get("authorships") or [{}])[0].get("author") or {}).get("display_name", "")
        out.append((a, w.get("publication_year"), (w.get("title") or "").strip(), w.get("doi")))
    return j["meta"]["count"], out


if __name__ == "__main__":
    today = datetime.date.today().isoformat()
    lines = ["# Literature search log", "", "Source: OpenAlex works API, journal articles, relevance-ranked. Run on %s." % today, ""]
    for tag, q in QUERIES:
        count, rows = fetch(q)
        lines.append("## %s  \"%s\"" % (tag, q))
        lines.append("Matches reported by the index: %d. First %d titles:" % (count, len(rows)))
        lines.append("")
        for a, y, t, d in rows:
            lines.append("- %s (%s) %s  %s" % (a, y, t[:150], d or ""))
        lines.append("")
    open(os.path.join(HERE, "search_log.md"), "w", encoding="utf-8").write("\n".join(lines))
    print("wrote search_log.md (%d queries)" % len(QUERIES))
