# -*- coding: utf-8 -*-
"""Resolve and verify every reference the manuscript cites. Nothing is cited from memory.

Two modes, because a literature the author half-remembers fails in two different ways:

  SEED   "I believe this paper exists: <author>, <year>, <title words>, <journal>."
         Crossref is asked for the best match and the record that comes back is
         compared with the stated intent. A disagreement on year, first author or
         title is printed loudly, because that is exactly how a misattributed
         reference (right title, wrong author) survives into a manuscript.

  SEARCH "I need a paper on <topic>." Crossref returns candidates; the author reads
         the record and decides. Nothing is accepted automatically.

Every record is written to _harvest.json with the fields needed to typeset a
Springer author-date entry. Retraction, withdrawal and correction notices are
flagged: Crossref resolving a DOI proves only that the DOI exists.

    python harvest.py seeds   ->  prints the seed-verification table
    python harvest.py search "topic words" [rows]
"""
import io, json, os, re, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "tncc-ref-harvest/1.0 (mailto:sandler.leon@gmail.com)"}
OUT = os.path.join(HERE, "_harvest.json")


def crossref(params):
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read())["message"]["items"]
        except Exception as e:                      # transient 5xx / timeouts
            time.sleep(2 + 2 * attempt)
            last = e
    raise SystemExit("Crossref failed: %s" % last)


def by_doi(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read())["message"]
        except Exception as e:
            time.sleep(2 + 2 * attempt)
            last = e
    return None


def norm(s):
    return re.sub(r"[^a-z0-9 ]", "", (s or "").lower())


def first_author(it):
    a = (it.get("author") or [{}])[0]
    return a.get("family", "")


def year(it):
    for k in ("published-print", "issued", "published-online"):
        p = (it.get(k) or {}).get("date-parts")
        if p and p[0] and p[0][0]:
            return p[0][0]
    return None


def title(it):
    t = it.get("title") or [""]
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t[0])).strip()


def container(it):
    import html
    c = it.get("container-title") or [""]
    return html.unescape(c[0])


def similarity(a, b):
    ta, tb = set(norm(a).split()), set(norm(b).split())
    return len(ta & tb) / float(max(1, len(ta | tb)))


BAD = re.compile(r"retract|withdraw|erratum|corrigendum|correction to|publisher correction", re.I)


def record(it):
    return {
        "doi": it.get("DOI"),
        "title": title(it),
        "authors": [{"family": a.get("family", ""), "given": a.get("given", "")}
                    for a in it.get("author", [])],
        "container": container(it),
        "year": year(it),
        "volume": it.get("volume"),
        "issue": it.get("issue"),
        "page": it.get("page") or it.get("article-number"),
        "type": it.get("type"),
        "cited_by": it.get("is-referenced-by-count"),
        "notice": bool(BAD.search(title(it))) or bool(it.get("update-to")),
        "has_abstract": bool(it.get("abstract")),
    }


def store(key, rec):
    db = {}
    if os.path.exists(OUT):
        db = json.load(io.open(OUT, encoding="utf-8"))
    db[key] = rec
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(db, indent=1, ensure_ascii=False))


# ---------------------------------------------------------------------------
# key: (intended first author, intended year, title words, intended journal word)
SEEDS = {
    # --- transparent nanocellulose and nanopaper
    "nogi2009":      ("Nogi", 2009, "Optically transparent nanofiber paper", "Adv"),
    "fukuzumi2009":  ("Fukuzumi", 2009, "Transparent and flexible films from TEMPO-oxidized cellulose nanofibers", "Biomacro"),
    "saito2007":     ("Saito", 2007, "Cellulose nanofibers prepared by TEMPO-mediated oxidation of native cellulose", "Biomacro"),
    "isogai2011":    ("Isogai", 2011, "TEMPO-oxidized cellulose nanofibers", "Nanoscale"),
    "hsieh2017":     ("Hsieh", 2017, "Hazy transparent cellulose nanopaper", "Sci"),
    "fang2014":      ("Fang", 2014, "Highly transparent paper with tunable haze for green electronics", "Energy"),
    "zhu2014":       ("Zhu", 2014, "Transparent paper: fabrications, properties, and device applications", "Energy"),
    "apl2013":       ("", 2013, "High thermal stability of optical transparency in cellulose nanofiber paper", "Appl"),
    "song2016":      ("", 2016, "Highly transparent, low-haze, hybrid cellulose nanopaper as electrodes for flexible electronics", "Nanoscale"),
    "fukuzumi2013":  ("Fukuzumi", 2013, "Influence of TEMPO-oxidized cellulose nanofibril length on film properties", "Carbohydr"),
    "nogiyano2008":  ("Nogi", 2008, "Transparent nanocomposites based on cellulose produced by bacteria offer potential innovation in the electronics device industry", "Adv"),
    "iwamoto2005":   ("Iwamoto", 2005, "Optically transparent composites reinforced with plant fiber-based nanofibers", "Appl"),
    "henriksson2008":("Henriksson", 2008, "Cellulose nanopaper structures of high toughness", "Biomacro"),
    "sehaqui2011":   ("Sehaqui", 2011, "Strong and tough cellulose nanopaper with high specific surface area and porosity", "Biomacro"),
    "klemm2011":     ("Klemm", 2011, "Nanocelluloses: a new family of nature-based materials", "Angew"),
    "moon2011":      ("Moon", 2011, "Cellulose nanomaterials review: structure, properties and nanocomposites", "Chem"),
    "dufresne2013":  ("Dufresne", 2013, "Nanocellulose: a new ageless bionanomaterial", "Mater"),
    "benitez2017":   ("Ben", 2017, "Cellulose nanofibril nanopapers and bioinspired nanocomposites: a review to understand the mechanical property space", "Mater"),
    # --- bagasse
    "mandal2011":    ("Mandal", 2011, "Isolation of nanocellulose from waste sugarcane bagasse (SCB) and its characterization", "Carbohydr"),
    "bhattacharya2008": ("Bhattacharya", 2008, "Isolation, preparation and characterization of cellulose microfibers obtained from bagasse", "Carbohydr"),
    "cardona2010":   ("Cardona", 2010, "Production of bioethanol from sugarcane bagasse: Status and perspectives", "Bioresour"),
    "canilha2012":   ("Canilha", 2012, "Bioconversion of sugarcane biomass into ethanol: an overview about composition, pretreatment methods, detoxification of hydrolysates, enzymatic saccharification, and ethanol fermentation", "J"),
    # --- chitosan
    "rinaudo2006":   ("Rinaudo", 2006, "Chitin and chitosan: properties and applications", "Prog"),
    "toivonen2015":  ("Toivonen", 2015, "Water-resistant, transparent hybrid nanopaper by physical cross-linking with chitosan", "Biomacro"),
    "azeredo2010":   ("Azeredo", 2010, "Nanocellulose reinforced chitosan composite films as affected by nanofiller loading and plasticizer content", "J"),
    "pillai2009":    ("Pillai", 2009, "Chitin and chitosan polymers: chemistry, solubility and fiber formation", "Prog"),
    "ghormade2017":  ("Ghormade", 2017, "Can fungi compete with marine sources for chitosan production", "Int"),
    # --- barrier and packaging
    "aulin2010":     ("Aulin", 2010, "Oxygen and oil barrier properties of microfibrillated cellulose films and coatings", "Cellulose"),
    "lavoine2012":   ("Lavoine", 2012, "Microfibrillated cellulose its barrier properties and applications in cellulosic materials: a review", "Carbohydr"),
    "hubbe2017":     ("Hubbe", 2017, "Nanocellulose in thin films, coatings, and plies for packaging applications: a review", "Bio"),
    "azeredo2017":   ("Azeredo", 2017, "Nanocellulose in bio-based food packaging applications", "Ind"),
    "shimizu2016":   ("Shimizu", 2016, "Water-resistant and high oxygen-barrier nanocellulose films with interfibrillar cross-linkages formed through multivalent metal ions", "J"),
    # --- forming
    "vishtal2012":   ("Vishtal", 2012, "Deep-drawing of paper and paperboard: the role of material properties", "Bio"),
    "hauptmann2011": ("Hauptmann", 2011, "New quality level of packaging components from paperboard through technology development", "Packag"),
    # --- energy, LCA
    "spence2011":    ("Spence", 2011, "A comparative study of energy consumption and physical properties of microfibrillated cellulose produced by different processing methods", "Cellulose"),
    "nechyporchuk2016": ("Nechyporchuk", 2016, "Production of cellulose nanofibrils: A review of recent advances", "Ind"),
    "arvidsson2015": ("Arvidsson", 2015, "Life cycle assessment of cellulose nanofibrils production by mechanical treatment and two different pretreatment processes", "Environ"),
    # --- optics
    "debye1949":     ("Debye", 1949, "Scattering by an inhomogeneous solid", "J"),
    "debye1957":     ("Debye", 1957, "Scattering by an inhomogeneous solid. II. The correlation function and its application", "J"),
}


def seeds():
    ok = bad = 0
    for key, (au, yr, ti, jr) in SEEDS.items():
        params = {"query.bibliographic": ti, "rows": 5}
        if au:
            params["query.author"] = au
        params["filter"] = "from-pub-date:%d,until-pub-date:%d" % (yr - 1, yr + 1)
        items = crossref(params)
        best, bs = None, -1
        for it in items:
            s = similarity(ti, title(it))
            if s > bs:
                best, bs = it, s
        time.sleep(0.4)
        if best is None or bs < 0.55:
            print("?? %-16s NO CONFIDENT MATCH (best title sim %.2f)  intended: %s %d %s"
                  % (key, bs, au or "(author unknown)", yr, ti[:60]))
            if best:
                print("     nearest : %s | %s | %s %s" % (first_author(best), title(best)[:70],
                                                          container(best), year(best)))
            bad += 1
            continue
        rec = record(best)
        store(key, rec)
        flags = []
        if au and norm(au) not in norm(first_author(best)):
            flags.append("FIRST AUTHOR is %s, not %s" % (first_author(best), au))
        if year(best) != yr:
            flags.append("YEAR is %s, not %s" % (year(best), yr))
        if rec["notice"]:
            flags.append("NOTICE/UPDATE FLAG")
        if flags:
            bad += 1
        else:
            ok += 1
        a = ", ".join("%s %s" % (x["family"], (x["given"] or "")[:1]) for x in rec["authors"][:4])
        print("%s %-16s sim %.2f | %s%s | %s %s %s:%s | %s" % (
            "!!" if flags else "ok", key, bs, a, " et al" if len(rec["authors"]) > 4 else "",
            rec["container"][:28], rec["year"], rec["volume"], rec["page"], rec["doi"]))
        for f in flags:
            print("     >>>", f)
    print("\n%d clean, %d needing a look" % (ok, bad))


def abstract(doi):
    """Abstract text: Crossref when deposited, otherwise PubMed (matched by DOI)."""
    it = by_doi(doi)
    if it and it.get("abstract"):
        import html
        t = html.unescape(re.sub(r"<[^>]+>", " ", it["abstract"]))
        return re.sub(r"\s+", " ", t).strip()
    try:
        u = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&term="
             + urllib.parse.quote(doi + "[doi]"))
        ids = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read())
        ids = ids["esearchresult"]["idlist"]
        if not ids:
            return None
        u = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&id=" + ids[0])
        x = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read().decode("utf8")
        parts = re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", x, re.S)
        import html
        return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", " ".join(parts)))).strip() or None
    except Exception:
        pass
    return None


def abstract_fallback(doi):
    """OpenAlex (inverted index) then Semantic Scholar, for records Crossref/PubMed lack."""
    try:
        u = "https://api.openalex.org/works/doi:" + urllib.parse.quote(doi)
        j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read())
        inv = j.get("abstract_inverted_index")
        if inv:
            pos = {}
            for w, idx in inv.items():
                for i in idx:
                    pos[i] = w
            return " ".join(pos[i] for i in sorted(pos))
    except Exception:
        pass
    try:
        u = "https://api.semanticscholar.org/graph/v1/paper/DOI:%s?fields=abstract" % urllib.parse.quote(doi)
        j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read())
        if j.get("abstract"):
            return j["abstract"]
    except Exception:
        pass
    return None


def search(q, rows=8):
    items = crossref({"query.bibliographic": q, "rows": rows * 3,
                      "filter": "type:journal-article", "sort": "relevance"})
    items = [it for it in items if it.get("author") and not re.search(r"\.s\d+$", it.get("DOI", ""))]
    for it in items[:rows]:
        rec = record(it)
        a = ", ".join("%s %s" % (x["family"], (x["given"] or "")[:1]) for x in rec["authors"][:3])
        print("- %s%s (%s) %s | %s %s:%s | %s | cited %s%s" % (
            a, " et al" if len(rec["authors"]) > 3 else "", rec["year"], rec["title"][:95],
            rec["container"][:26], rec["volume"], rec["page"], rec["doi"], rec["cited_by"],
            " | NOTICE" if rec["notice"] else ""))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "seeds":
        seeds()
    elif len(sys.argv) > 2 and sys.argv[1] == "doi":
        for d in sys.argv[2:]:
            it = by_doi(d)
            if not it:
                print("NOT FOUND", d); continue
            rec = record(it)
            a = ", ".join("%s %s" % (x["family"], (x["given"] or "")[:1]) for x in rec["authors"][:4])
            print("%s | %s (%s) | %s | %s %s:%s | notice=%s" % (
                d, a, rec["year"], rec["title"][:90], rec["container"][:30], rec["volume"],
                rec["page"], rec["notice"]))
    elif len(sys.argv) > 2 and sys.argv[1] == "abstract":
        for d in sys.argv[2:]:
            print("=== %s" % d)
            print(abstract(d) or abstract_fallback(d) or "(no abstract available from any source)")
            print()
    elif len(sys.argv) > 2 and sys.argv[1] == "search":
        search(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 8)
    else:
        print(__doc__)
