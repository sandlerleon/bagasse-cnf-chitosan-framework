# -*- coding: utf-8 -*-
"""Zenodo deposits for the TNCC / Cellulose paper: one software record (the tagged GitHub
release) and one preprint record (manuscript + Supplementary Information).

Two phases, so the DOIs can be written into the manuscript and cover letter before anything
is published:

    python zenodo_deposit_tncc.py reserve   # create drafts, pre-reserve DOIs -> state file
    python zenodo_deposit_tncc.py publish   # upload files, write metadata, publish

The token is read from ZENODO_TOKEN and never written to disk.
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
STATE = r"C:\YouTube\_tncc_zenodo_state.json"
REPO = r"C:\YouTube\tncc-framework"
TAG = "v1.0.0"
MS_FILES = [
    (os.path.join(REPO, "manuscript", "TNCC_Cellulose_Manuscript_v2.docx"), "TNCC_Cellulose_Manuscript_v2_preprint.docx"),
    (os.path.join(REPO, "manuscript", "TNCC_Supplementary_Information.docx"), "TNCC_Supplementary_Information.docx"),
]

CREATORS = [{"name": "Sandler, Leon", "affiliation": "Independent Researcher",
             "orcid": "0009-0007-4584-808X"}]
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
every parameter is taken from a verified literature source or stated as an assumption, and every
output is a screening estimate rather than a prediction of material behaviour.</strong> Prepared
for submission to <em>Cellulose</em> (Springer).</p>

<p>Transparent rigid packaging is dominated by fossil-derived polymers, while fibre-based packaging
is opaque. Dense cellulose nanofibril and nanocrystal sheets are transparent as flat films, but
whether transparency, wet stiffness and a three-dimensional shape can coexist in one
sugarcane-bagasse-derived package has not been established. The only reported attempt to mould
transparent CNF objects failed because of drying shrinkage. Three consistency screens are applied to
a proposed bagasse CNF-chitosan-wax architecture: an optical screen derived from Debye-Bueche
scattering theory, a wet-stiffness screen for CNF-chitosan sheets, and a geometric forming screen.
Each is propagated through a seeded Monte Carlo analysis (200,000 samples).</p>

<p><strong>Optical.</strong> Bulk haze scales with wall thickness and with the cube of the correlation
length of the void structure. The scattering prefactor is derived (64 pi^4/3), not fitted. A 100 um
wall at 10% haze and 5% void fraction requires a correlation length of about 10 nm or less, and the
closed-form cubic law overestimates scattering by 7x at 80 nm, the top of the reported bagasse
nanofibril range. <strong>Wet stiffness.</strong> Chitosan raises modelled wet stiffness only through
cross-linking, and the benefit disappears in an acidic liquid. <strong>Forming.</strong> Geometry sets
the burden: tray, bowl and cup shapes require total strain tolerances of 0.26, 0.67 and 1.10, and no
combination of the assumed ranges forms the cup (best case 0.96).</p>

<p>The deposit contains the manuscript, the Supplementary Information and, in the software record,
the complete model, the verification suite, every figure script, the reference-verification tooling
and a log of the literature searches behind each statement of absence.</p>"""


def req(method, url, data=None, headers=None, raw=None):
    h = {"Authorization": "Bearer " + TOKEN}
    if headers:
        h.update(headers)
    body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
    if data is not None and raw is None:
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=300) as resp:
            t = resp.read()
            return json.loads(t) if t else {}
    except urllib.error.HTTPError as e:
        raise SystemExit("%s %s -> %s\n%s" % (method, url, e.code, e.read().decode()[:800]))


def metadata(kind, doi):
    m = {"title": TITLE_CODE if kind == "software" else TITLE_PAPER,
         "upload_type": kind, "description": DESCRIPTION, "creators": CREATORS,
         "keywords": KEYWORDS, "access_right": "open",
         "license": "mit-license" if kind == "software" else "cc-by-4.0",
         "related_identifiers": RELATED, "version": TAG.lstrip("v"), "language": "eng",
         "prereserve_doi": {"doi": doi}}
    if kind == "publication":
        m["publication_type"] = "preprint"
    return {"metadata": m}


def reserve():
    if os.path.exists(STATE):
        raise SystemExit("state file exists; drafts already reserved: %s" % STATE)
    out = {}
    for kind in ("software", "publication"):
        dep = req("POST", API + "/deposit/depositions",
                  data={"metadata": {"upload_type": kind, "prereserve_doi": True}})
        out[kind] = {"id": dep["id"], "doi": dep["metadata"]["prereserve_doi"]["doi"],
                     "concept_rec_id": dep.get("conceptrecid"),
                     "bucket": dep["links"]["bucket"]}
        out[kind]["concept_doi"] = "10.5281/zenodo.%s" % dep.get("conceptrecid")
        print("%-11s draft %s  version DOI %s  concept DOI %s" % (
            kind, dep["id"], out[kind]["doi"], out[kind]["concept_doi"]))
    json.dump(out, open(STATE, "w"), indent=1)


def upload(bucket, path, name=None):
    name = name or os.path.basename(path)
    with open(path, "rb") as fh:
        req("PUT", "%s/%s" % (bucket, urllib.parse.quote(name)), raw=fh.read(),
            headers={"Content-Type": "application/octet-stream"})
    print("   uploaded %-52s %8.1f kB" % (name, os.path.getsize(path) / 1024.0))


def publish():
    st = json.load(open(STATE))
    tmp = os.path.join(os.environ.get("TEMP", "."), "bagasse-cnf-chitosan-framework-%s.zip" % TAG)
    subprocess.check_call(["git", "-C", REPO, "archive", "--format=zip",
                           "--prefix=bagasse-cnf-chitosan-framework-%s/" % TAG.lstrip("v"), "-o", tmp, TAG])
    for kind, files in (("software", [(tmp, None)]), ("publication", MS_FILES)):
        d = st[kind]
        print("\n=== %s  draft %s" % (kind, d["id"]))
        for path, name in files:
            if not os.path.exists(path):
                raise SystemExit("missing file: " + path)
            upload(d["bucket"], path, name)
        req("PUT", "%s/deposit/depositions/%s" % (API, d["id"]), data=metadata(kind, d["doi"]))
        pub = req("POST", "%s/deposit/depositions/%s/actions/publish" % (API, d["id"]))
        rec = req("GET", "%s/records/%s" % (API, pub["id"]))
        print("   PUBLISHED  DOI %s  concept %s" % (rec.get("doi"), rec.get("conceptdoi")))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "reserve":
        reserve()
    elif cmd == "publish":
        publish()
    else:
        print(__doc__)
