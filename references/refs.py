# -*- coding: utf-8 -*-
"""The manuscript's reference list, built only from verified Crossref records.

Every entry is a DOI that was resolved against Crossref and compared with the
claim it supports (see claims.md). Metadata is cached in refs_cache.json so the
manuscript builds offline and a reference can never drift from its verified
record. Output follows Springer Basic (author-date), as used by Cellulose:

    Hsieh M-C, Koga H, Suganuma K, Nogi M (2017) Hazy transparent cellulose
    nanopaper. Sci Rep 7:41590. https://doi.org/10.1038/srep41590

More than three authors are shortened to the first three followed by "et al".
"""
import html, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "refs_cache.json")

# key -> DOI. Order is irrelevant; the list is sorted by author at output.
DOI = {
    "nogi2009": "10.1002/adma.200803174",
    "jager2009": "10.1063/1.3254239",
    "fukuzumi2009": "10.1021/bm801065u",
    "saito2007": "10.1021/bm0703970",
    "isogai2011": "10.1039/c0nr00583e",
    "hsieh2017": "10.1038/srep41590",
    "fang2014": "10.1039/c4ee02236j",
    "zhu2014": "10.1039/c3ee43024c",
    "nogi2013": "10.1063/1.4804361",
    "xu2016": "10.1039/c6nr02245f",
    "fukuzumi2013": "10.1016/j.carbpol.2012.04.069",
    "henriksson2008": "10.1021/bm800038n",
    "sehaqui2011": "10.1021/bm2008907",
    "klemm2011": "10.1002/anie.201001273",
    "moon2011": "10.1039/c0cs00108b",
    "benitez2017": "10.1039/c7ta02006f",
    "qing2012": "10.15376/biores.7.3.3064-3075",
    "jiang2016": "10.1021/acssuschemeng.5b01653",
    "toivonen2015": "10.1021/acs.biomac.5b00145",
    "sellman2024": "10.1007/s10570-024-06084-4",
    "niskanen2022": "10.1007/s10965-022-03019-0",
    "yang2019": "10.3390/nano9010107",
    "mandal2011": "10.1016/j.carbpol.2011.06.030",
    "bhattacharya2008": "10.1016/j.carbpol.2007.12.005",
    "carneiro2023": "10.1016/j.carbpol.2022.120505",
    "otenda2022": "10.1080/15440478.2020.1848712",
    "kim2011": "10.1007/s10295-010-0812-8",
    "kabeyi2023": "10.1155/2023/5749122",
    "ndikumana2025": "10.3390/pr13123796",
    "hiranobe2024": "10.3390/cleantechnol6020035",
    "scopel2025": "10.1007/s10570-025-06785-4",
    "rinaudo2006": "10.1016/j.progpolymsci.2006.06.001",
    "pillai2009": "10.1016/j.progpolymsci.2009.04.001",
    "melro2021": "10.3390/polym13010001",
    "azeredo2010": "10.1111/j.1750-3841.2009.01386.x",
    "fernandez2024": "10.1021/acssuschemeng.4c01205",
    "szymanska2019": "10.1007/s10570-019-02755-9",
    "ghormade2017": "10.1016/j.ijbiomac.2017.01.112",
    "sirvio2021": "10.1021/acs.biomac.1c00216",
    "aulin2010": "10.1007/s10570-009-9393-y",
    "lavoine2012": "10.1016/j.carbpol.2012.05.026",
    "hubbe2017": "10.15376/biores.12.1.hubbe",
    "azeredo2017": "10.1016/j.indcrop.2016.03.013",
    "shimizu2016": "10.1016/j.memsci.2015.11.002",
    "li2019": "10.1007/s10570-019-02270-x",
    "wang2017": "10.15376/biores.12.4.7774-7783",
    "vishtal2012": "10.15376/biores.7.3.4424-4450",
    "hauptmann2011": "10.1002/pts.941",
    "lyu2019": "10.1016/j.polymer.2019.01.081",
    "arvidsson2015": "10.1021/acs.est.5b00888",
    "spence2011": "10.1007/s10570-011-9533-z",
    "nechyporchuk2016": "10.1016/j.indcrop.2016.02.016",
    "debye1949": "10.1063/1.1698419",
    "debye1957": "10.1063/1.1722830",
    "astm2021": "10.1520/D1003-21",
    "tao2017": "10.1002/aelm.201600539",
    "rol2020": "10.1021/acs.iecr.9b06127",
    "makela2016": "10.1016/j.mee.2016.05.023",
    "semple2022": "10.1016/j.fpsl.2022.100908",
    "guzman2022": "10.1016/j.foodres.2022.111792",
    "kargupta2022": "10.1007/s10570-022-04563-0",
}

# entries that are not journal articles in Crossref
MANUAL = {
    "fao2024": {
        "authors": [{"family": "FAO", "given": ""}],
        "year": 2024,
        "text": ("FAO (2024) FAOSTAT: crops and livestock products, sugar cane (item 156), "
                 "production quantity (element 5510), world total. Food and Agriculture "
                 "Organization of the United Nations, Rome. https://www.fao.org/faostat/. "
                 "Accessed via Our World in Data, 2 October 2026"),
    },
    "astm2021": {
        "authors": [{"family": "ASTM International", "given": ""}],
        "year": 2021,
        "text": ("ASTM International (2021) ASTM D1003-21: standard test method for haze and "
                 "luminous transmittance of transparent plastics. ASTM International, West "
                 "Conshohocken, PA. https://doi.org/10.1520/D1003-21"),
    },
}

# Standard abbreviations (ISO 4 / CASSI) for the journals used here
ABBR = {
    "Advanced Materials": "Adv Mater",
    "Biomacromolecules": "Biomacromolecules",
    "Nanoscale": "Nanoscale",
    "Scientific Reports": "Sci Rep",
    "Energy & Environmental Science": "Energy Environ Sci",
    "Energy Environ. Sci.": "Energy Environ Sci",
    "Applied Physics Letters": "Appl Phys Lett",
    "Carbohydrate Polymers": "Carbohydr Polym",
    "Angewandte Chemie International Edition": "Angew Chem Int Ed",
    "Chemical Society Reviews": "Chem Soc Rev",
    "Journal of Materials Chemistry A": "J Mater Chem A",
    "BioResources": "BioResources",
    "ACS Sustainable Chemistry & Engineering": "ACS Sustain Chem Eng",
    "Cellulose": "Cellulose",
    "Journal of Applied Physics": "J Appl Phys",
    "Nanomaterials": "Nanomaterials",
    "Journal of Natural Fibers": "J Nat Fibers",
    "Journal of Industrial Microbiology & Biotechnology": "J Ind Microbiol Biotechnol",
    "Journal of Energy": "J Energy",
    "Processes": "Processes",
    "Clean Technologies": "Clean Technol",
    "Progress in Polymer Science": "Prog Polym Sci",
    "Polymers": "Polymers",
    "Journal of Food Science": "J Food Sci",
    "International Journal of Biological Macromolecules": "Int J Biol Macromol",
    "Industrial Crops and Products": "Ind Crops Prod",
    "Journal of Membrane Science": "J Membr Sci",
    "Packaging Technology and Science": "Packag Technol Sci",
    "Polymer": "Polymer",
    "Environmental Science & Technology": "Environ Sci Technol",
    "Journal of Polymer Research": "J Polym Res",
    "Advanced Electronic Materials": "Adv Electron Mater",
    "Industrial & Engineering Chemistry Research": "Ind Eng Chem Res",
    "Microelectronic Engineering": "Microelectron Eng",
    "Food Packaging and Shelf Life": "Food Packag Shelf Life",
    "Food Research International": "Food Res Int",
}


def load():
    if os.path.exists(CACHE):
        return json.load(io.open(CACHE, encoding="utf-8"))
    return {}


def refresh():
    sys.path.insert(0, HERE)
    import harvest as h
    db = load()
    for k, d in DOI.items():
        if k in db or k in MANUAL:
            continue
        it = h.by_doi(d)
        if not it:
            raise SystemExit("Crossref has no record for %s (%s)" % (k, d))
        db[k] = h.record(it)
        db[k]["short"] = (it.get("short-container-title") or [""])[0]
    io.open(CACHE, "w", encoding="utf-8").write(json.dumps(db, indent=1, ensure_ascii=False))
    return db


def initials(given):
    parts = re.split(r"[\s]+", (given or "").strip())
    out = []
    for p in parts:
        if not p:
            continue
        sub = [s for s in p.split("-") if s]
        out.append("-".join(s[0].upper() for s in sub))
    return "".join(out) if len(out) == 1 else " ".join(out).replace(" ", "")


def author_str(authors):
    names = ["%s %s" % (a["family"], initials(a["given"])) if a["given"] else a["family"]
             for a in authors]
    return ", ".join(names[:3]) + (" et al" if len(names) > 3 else "")


def clean(t):
    return re.sub(r"\s+", " ", html.unescape(t or "")).strip()


def abbr(rec):
    c = clean(rec["container"])
    return ABBR.get(c, ABBR.get(rec.get("short", ""), c))


PROPER = {"Louisiana"}                      # proper nouns that must keep their capital
YEAR_OVERRIDE = {"melro2021": 2021}         # Polymers volume 13 is the 2021 volume (online 2020-12-22)


def sentence_case(t):
    """Springer sets article titles in sentence case. Publishers' titles are often Title
    Case, so lower-case ordinary capitalised words, but never touch acronyms (TEMPO, CNF),
    tokens with digits or internal capitals, or the proper nouns listed above. A title that
    is already in sentence case is returned unchanged. A capital is kept at the start of a
    sentence (after '.' or '?'), but not after a colon."""
    words = t.split()
    long_all = [w for w in words if len(re.sub(r"\W", "", w)) > 3]
    long_caps = [w for w in long_all if re.match(r"^\W*[A-Z][a-z]+", w)]
    if not long_all or len(long_caps) / float(len(long_all)) < 0.5:
        return t
    HYPH = "-‐‑–"

    def core(tok, first):
        if tok in ("A", "An", "The") and not first:
            return tok.lower()
        if tok in PROPER or tok.isupper() or re.search(r"\d", tok) or re.search(r"[a-z][A-Z]", tok):
            return tok
        if re.match(r"^[A-Z][a-z]+$", tok):
            return tok if first else tok.lower()
        return tok

    def fix(tok, first):
        m = re.match(r"^(\W*)(.*?)(\W*)$", tok)
        lead, mid, trail = m.group(1), m.group(2), m.group(3)
        parts = re.split("([%s])" % HYPH, mid)
        mid2 = "".join(p if re.match("^[%s]$" % HYPH, p) else core(p, first and i == 0)
                       for i, p in enumerate(parts))
        return lead + mid2 + trail

    out, first = [], True
    for w in words:
        out.append(fix(w, first))
        first = w.endswith((".", "?"))
    return " ".join(out)


def entry(key, db=None):
    db = db or load()
    if key in MANUAL:
        return MANUAL[key]["text"]
    r = db[key]
    pages = r["page"] or ""
    vol = r["volume"] or ""
    if pages:
        loc = "%s:%s" % (vol, pages.replace("-", "–"))
    elif r.get("issue"):
        loc = "%s(%s)" % (vol, r["issue"])        # no page or article number in the record
    else:
        loc = vol
    title = sentence_case(clean(r["title"])).rstrip(".")
    title = re.sub(r": (A|An|The) ", lambda mo: ": " + mo.group(1).lower() + " ", title)
    punct = "" if title.endswith("?") else "."
    return "%s (%s) %s%s %s %s. https://doi.org/%s" % (
        author_str(r["authors"]), year_of(key, db), title, punct, abbr(r), loc, r["doi"])


def first_family(key, db):
    if key in MANUAL:
        return MANUAL[key]["authors"][0]["family"]
    return db[key]["authors"][0]["family"]


def year_of(key, db):
    if key in YEAR_OVERRIDE:
        return YEAR_OVERRIDE[key]
    return MANUAL[key]["year"] if key in MANUAL else db[key]["year"]


def short_author(key, db):
    if key in MANUAL:
        return MANUAL[key]["authors"][0]["family"]
    a = db[key]["authors"]
    if len(a) == 1:
        return a[0]["family"]
    if len(a) == 2:
        return "%s and %s" % (a[0]["family"], a[1]["family"])
    return "%s et al." % a[0]["family"]


def cite(*keys, db=None):
    """In-text citation, chronological then alphabetical: (Nogi et al. 2009; Hsieh et al. 2017)."""
    db = db or load()
    ks = sorted(keys, key=lambda k: (year_of(k, db), first_family(k, db)))
    return "(" + "; ".join("%s %s" % (short_author(k, db), year_of(k, db)) for k in ks) + ")"


def narrative(key, db=None):
    """Narrative form: Hsieh et al. (2017)."""
    db = db or load()
    return "%s (%s)" % (short_author(key, db), year_of(key, db))


def all_entries(used=None):
    db = load()
    keys = [k for k in list(DOI) + [m for m in MANUAL if m not in DOI] if used is None or k in used]
    keys = sorted(set(keys), key=lambda k: (first_family(k, db).lower(), year_of(k, db)))
    return [(k, entry(k, db)) for k in keys]


if __name__ == "__main__":
    db = refresh()
    for k, e in all_entries():
        print("%-18s %s" % (k, e))
    print("\n%d references" % len(all_entries()))
