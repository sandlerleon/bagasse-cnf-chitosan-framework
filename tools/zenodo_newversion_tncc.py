# -*- coding: utf-8 -*-
"""Publish v1.1.0 Zenodo versions of the TNCC code and manuscript records.

Lessons carried over from the earlier deposits:
  * Zenodo's read schema is not its write schema: full metadata is supplied in write form.
  * A new version inherits the previous version's files; they are deleted from the draft first.
  * A new version must branch from the LATEST record, resolved from the concept id.

The token is read from ZENODO_TOKEN and never written to disk.

    python zenodo_newversion_tncc.py [--dry]
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

TOKEN = os.environ.get("ZENODO_TOKEN")
if not TOKEN:
    raise SystemExit("ZENODO_TOKEN is not set in the environment")
API = "https://zenodo.org/api"
REPO = r"C:\YouTube\tncc-framework"
TAG, VERSION = "v1.1.0", "1.1.0"
CODE_CONCEPT, PAPER_CONCEPT = "23111544", "23111546"
DRY = "--dry" in sys.argv

R = json.load(open(os.path.join(REPO, "code", "results.json"), encoding="utf-8"))
LC, JT, KX = R["L_cup_requirement"], R["J_thickness_coupling"], R["K_wax_bounded"]
bud = R["E_envelope"]["strain_budgets"]

CREATORS = [{"name": "Sandler, Leon", "affiliation": "Independent Researcher", "orcid": "0009-0007-4584-808X"}]
TITLE_PAPER = ("Toward transparent rigid packaging from sugarcane bagasse: a consistency-testing "
               "framework for nanocellulose-chitosan sheets")
TITLE_CODE = ("TNCC consistency-testing model: optical haze budget, wet stiffness and forming strain "
              "budget for a transparent nanocellulose-chitosan package")
KEYWORDS = ["cellulose nanofibrils", "transparent nanopaper", "chitosan", "sugarcane bagasse",
            "thermoforming", "consistency testing", "optical haze", "Monte Carlo uncertainty",
            "sustainable packaging"]
RELATED = [{"identifier": "https://github.com/sandlerleon/bagasse-cnf-chitosan-framework",
            "relation": "isSupplementTo", "scheme": "url"}]

DESCRIPTION = """<p><strong>A theoretical and computational study. No experiments were performed;
every parameter range is traced to a cited source or stated as an assumption, and every output is a
screening estimate rather than a prediction of material behaviour.</strong> Prepared for submission to
<em>Cellulose</em> (Springer). Version %(v)s responds to review.</p>

<p>Three consistency screens (optical, wet stiffness, forming) are applied to a proposed bagasse
CNF-chitosan-wax architecture and propagated through a seeded Monte Carlo analysis (200,000 samples,
seed 20261002).</p>

<p><strong>New in %(v)s.</strong> (1) Optical-model validation: rough-surface and coarse-population
scattering are added as bounded sensitivities; they narrow but do not close the gap to the haze of
published clear nanopaper, and they show the correlation-length threshold is necessary, not
sufficient. (2) Seven prior schemes: pass shares move by tens of percentage points; the thresholds,
the orderings and the cup bound do not. (3) Thickness coupling: stiffness sets a minimum wall
thickness (median %(tn).0f um neutral, %(ta).0f um acidic) and thickness sets the haze, so the liquid
changes the optical budget. (4) A bounded wax-layer sensitivity: added haze and, for coating before
forming, a narrower forming window; liquid containment remains untested, so all feasibility results
are provisional. (5) The cup needs a flange wrinkling strain above %(wr).2f (strain budgets: tray
%(b1).2f, bowl %(b2).2f, cup %(b3).2f). (6) A final reference audit, figure-data tables, a Data
availability statement and a revised AI-use statement. The verification suite grows from 43 to 58
checks. Results of version 1.0.0 are unchanged.</p>

<p>Every figure is a bounded model estimate, not a measured or predicted material property.</p>""" % dict(
    v=VERSION, tn=JT["t_min_at_median_E_um"]["neutral"], ta=JT["t_min_at_median_E_um"]["acid"],
    wr=LC["eps_wrinkle_needed_cup_at_best_tensile"], b1=bud["tray (lid-like)"], b2=bud["bowl"], b3=bud["cup"])


def req(method, url, data=None, headers=None, raw=None):
    h = {"Authorization": "Bearer " + TOKEN}
    if headers:
        h.update(headers)
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    if data is not None and raw is None:
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=180) as resp:
            t = resp.read()
            return json.loads(t) if t else {}
    except urllib.error.HTTPError as e:
        raise SystemExit("%s %s -> %s\n%s" % (method, url, e.code, e.read().decode()[:600]))


def metadata(kind):
    m = {"title": TITLE_CODE if kind == "software" else TITLE_PAPER, "upload_type": kind, "description": DESCRIPTION,
         "creators": CREATORS, "keywords": KEYWORDS, "access_right": "open",
         "license": "mit-license" if kind == "software" else "cc-by-4.0", "related_identifiers": RELATED,
         "version": VERSION, "language": "eng"}
    if kind != "software":
        m["upload_type"] = "publication"
        m["publication_type"] = "preprint"
    return {"metadata": m}


def latest(concept):
    rec = req("GET", "%s/records/%s/versions/latest" % (API, concept))
    print("concept %s -> latest record %s (version %s)" % (concept, rec["id"], rec.get("metadata", {}).get("version")))
    return str(rec["id"])


def new_version(parent_id, kind, files):
    print("\n=== %s record, parent %s" % (kind, parent_id))
    dep = req("POST", "%s/deposit/depositions/%s/actions/newversion" % (API, parent_id))
    draft_url = dep["links"]["latest_draft"]
    draft = req("GET", draft_url)
    did = draft["id"]
    print("   draft %s" % did)
    for f in draft.get("files", []):
        req("DELETE", "%s/deposit/depositions/%s/files/%s" % (API, did, f["id"]))
    print("   inherited files removed: %d" % len(draft.get("files", [])))
    bucket = draft["links"]["bucket"]
    for path, name in files:
        with open(path, "rb") as fh:
            req("PUT", "%s/%s" % (bucket, urllib.parse.quote(name)), raw=fh.read(),
                headers={"Content-Type": "application/octet-stream"})
        print("   uploaded %-52s %8.1f kB" % (name, os.path.getsize(path) / 1024.0))
    req("PUT", "%s/deposit/depositions/%s" % (API, did), data=metadata(kind))
    print("   metadata written")
    if DRY:
        print("   DRY RUN - not publishing; draft left at %s" % draft_url)
        return None
    pub = req("POST", "%s/deposit/depositions/%s/actions/publish" % (API, did))
    rec = req("GET", "%s/records/%s" % (API, pub["id"]))
    print("   PUBLISHED  version DOI %s  concept DOI %s" % (rec.get("doi"), rec.get("conceptdoi")))
    return rec


def main():
    tmp = os.path.join(os.environ.get("TEMP", "."), "bagasse-cnf-chitosan-framework-%s.zip" % TAG)
    subprocess.check_call(["git", "-C", REPO, "archive", "--format=zip", "--prefix=bagasse-cnf-chitosan-framework-%s/" % VERSION,
                           "-o", tmp, TAG])
    print("code archive: %s (%.1f MB)" % (tmp, os.path.getsize(tmp) / 1e6))
    ms = [(os.path.join(REPO, "manuscript", "TNCC_Cellulose_Manuscript_v3.docx"), "TNCC_Cellulose_Manuscript_v3_preprint.docx"),
          (os.path.join(REPO, "manuscript", "TNCC_Supplementary_Information.docx"), "TNCC_Supplementary_Information.docx")]
    for p, _ in ms:
        if not os.path.exists(p):
            raise SystemExit("missing " + p)
    new_version(latest(CODE_CONCEPT), "software", [(tmp, os.path.basename(tmp))])
    new_version(latest(PAPER_CONCEPT), "publication", ms)


if __name__ == "__main__":
    main()
