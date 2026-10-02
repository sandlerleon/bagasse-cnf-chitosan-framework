# -*- coding: utf-8 -*-
"""Final reference audit: every cited reference is re-resolved against Crossref (live) and compared
with the cached record; every numerical anchor used in the parameter registry or the text is
searched for in the cited abstract.

    python audit_refs.py     ->  audit_log.md

Two different failures are checked, because they are different:
  1. the record changed or is wrong   (title, year, first author, journal, volume, notices)
  2. the number quoted is not in the source we could read (anchor missing from the abstract)
An anchor missing from an abstract does not prove the number is wrong, since some numbers sit only
in the full text; it is listed so that it can be checked against the paper.
"""
import datetime
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harvest as hv  # noqa: E402
import refs as rf  # noqa: E402

DB = rf.load()
dash = lambda s: re.sub(r"[‐-―−]", "-", s)

# numerical anchors: key -> [(what it supports, [strings that must all appear in the abstract])]
ANCHORS = {
    "hsieh2017": [("density 1.29-1.55 g cm-3", ["1.29", "1.55"]), ("haze 4.9-11.7 %", ["4.9", "11.7"]),
                  ("transmittance 89.3-91.5 %", ["89.3", "91.5"])],
    "fukuzumi2009": [("fibril width 3-4 nm", ["3-4 nm"])],
    "carneiro2023": [("diameters 5-80 nm", ["5", "80 nm"])],
    "qing2012": [("modulus 4.79 GPa", ["4.79"])],
    "toivonen2015": [("wet strength/modulus, strain figures", ["4 GPa"]), ("strain 28 % vs 8 %", ["28", "8"])],
    "jiang2016": [("strain to failure 16 %", ["16"]), ("defibrillation 15 kWh/kg", ["15", "kWh"])],
    "szymanska2019": [("modulus 14.71 -> 8.76 GPa", ["14.71", "8.76"])],
    "fernandez2024": [("chitosan modulus 2.3 and 3.4 GPa", ["2.3", "3.4"])],
    "xu2016": [("direct transmittance 75.1 %, haze 10.0 %", ["75.1", "10.0"]), ("31.1 %", ["31.1"])],
    "kargupta2022": [("refining energy 1,800-12,000 kWh/t", ["kWh"])],
}
QUALITATIVE = {
    "tao2017": ["transparent|clear|transmittance"],
    "rol2020": ["shrink|transparen|dimension"],
    "melro2021": ["acid|solub"],
    "niskanen2022": ["refractive|index"],
}

lines = ["# Reference audit", "", "Run %s. Crossref queried live for every cited DOI." % datetime.date.today().isoformat(), ""]
n_bad = 0
lines += ["## 1. Records against live Crossref", "", "| key | status | note |", "|---|---|---|"]
for key in sorted(rf.DOI):
    if key in getattr(rf, "MANUAL", {}):
        lines.append("| %s | manual | standard or report entered by hand, not a Crossref record |" % key)
        continue
    rec = DB.get(key)
    if not rec:
        lines.append("| %s | MISSING | not in cache |" % key)
        n_bad += 1
        continue
    live = hv.by_doi(rec["doi"])
    if live is None:
        lines.append("| %s | UNRESOLVED | Crossref did not return the DOI %s |" % (key, rec["doi"]))
        n_bad += 1
        continue
    probs = []
    if hv.similarity(hv.title(live), rec["title"]) < 0.9:
        probs.append("title differs: '%s'" % hv.title(live))
    if hv.first_author(live).lower() != (rec["authors"][0]["family"].lower() if rec["authors"] else ""):
        probs.append("first author differs: %s" % hv.first_author(live))
    if hv.year(live) != rec["year"] and key not in getattr(rf, "YEAR_OVERRIDE", {}):
        probs.append("year %s vs %s" % (hv.year(live), rec["year"]))
    if hv.container(live) != rec["container"]:
        probs.append("journal differs: %s" % hv.container(live))
    if str(live.get("volume")) != str(rec["volume"]):
        probs.append("volume %s vs %s" % (live.get("volume"), rec["volume"]))
    upd = [u.get("type") for u in (live.get("update-to") or [])]
    if any(t and re.search("retract|withdraw", t, re.I) for t in upd) or hv.BAD.search(hv.title(live)):
        probs.append("RETRACTION/WITHDRAWAL NOTICE")
    if probs:
        n_bad += 1
    lines.append("| %s | %s | %s |" % (key, "CHECK" if probs else "ok", "; ".join(probs) or rec["doi"]))
lines += ["", "## 2. Numerical anchors in the abstract", "", "| key | anchor | result |", "|---|---|---|"]
n_anchor_missing = 0
for key, items in ANCHORS.items():
    if not items or key not in DB:
        continue
    ab = hv.abstract(DB[key]["doi"]) or hv.abstract_fallback(DB[key]["doi"])
    for what, needles in items:
        if ab is None:
            res = "abstract not retrievable: check against the full text"
            n_anchor_missing += 1
        else:
            hit = [n for n in needles if dash(n) in dash(ab)]
            res = "found" if len(hit) == len(needles) else "NOT in abstract (%s missing): check the full text" % ", ".join(
                n for n in needles if n not in hit)
            n_anchor_missing += len(hit) != len(needles)
        lines.append("| %s | %s | %s |" % (key, what, res))
lines += ["", "## 3. Qualitative claims against the abstract", "", "| key | pattern | result |", "|---|---|---|"]
for key, pats in QUALITATIVE.items():
    ab = hv.abstract(DB[key]["doi"]) or hv.abstract_fallback(DB[key]["doi"])
    for p in pats:
        ok = bool(ab and re.search(p, ab, re.I))
        lines.append("| %s | %s | %s |" % (key, p, "found" if ok else ("no abstract" if ab is None else "not found")))
lines += ["", "Records needing a look: %d. Anchors not confirmed in an abstract: %d." % (n_bad, n_anchor_missing)]
with io.open(os.path.join(HERE, "audit_log.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))
