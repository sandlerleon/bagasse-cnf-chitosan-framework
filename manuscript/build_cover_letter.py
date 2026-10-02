# -*- coding: utf-8 -*-
"""Cover letter for submission to Cellulose (Springer). Numbers come from results.json."""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
from docx_helpers import bullet, new_document, para  # noqa: E402

R = json.load(io.open(os.path.join(ROOT, "code", "results.json"), encoding="utf-8"))
G, E = R["G_additions"], R["E_envelope"]
STATE = json.load(io.open(r"C:\YouTube\_tncc_zenodo_state.json", encoding="utf-8"))
CODE_DOI = STATE["software"]["concept_doi"]
PAPER_DOI = STATE["publication"]["concept_doi"]
REPO = "https://github.com/sandlerleon/bagasse-cnf-chitosan-framework"
bud = E["strain_budgets"]
a10 = G["a_max_nm"]["t100_haze10_phi05"]
best = E["forming_tolerance_h10"]["max"]

OUT = os.path.join(HERE, "TNCC_Cover_Letter_Cellulose.docx")
doc = new_document(size=11, line=1.15)

para(doc, "Leon Sandler", bold=True, space_after=0)
para(doc, "Independent Researcher", space_after=0)
para(doc, "Northbrook, Illinois, USA", space_after=0)
para(doc, "sandler.leon@gmail.com | ORCID 0009-0007-4584-808X", space_after=10)
para(doc, "2 October 2026", space_after=10)
para(doc, "The Editor-in-Chief", space_after=0)
para(doc, "*Cellulose*", space_after=10)
para(doc, "**Submission: Toward transparent rigid packaging from sugarcane bagasse: a consistency-testing framework for "
     "nanocellulose\u2013chitosan sheets**", space_after=8)
para(doc, "Dear Editor,", space_after=6)
para(doc, "I submit the above manuscript as an original research article, theoretical and computational in kind, for consideration in "
     "*Cellulose*. It concerns a question the journal\u2019s readers will recognise: dense cellulose nanofibril and nanocrystal sheets are "
     "transparent as flat films, but can transparency, wet stiffness and a three-dimensional shape coexist in a single "
     "agricultural-residue-derived package wall? The literature demonstrates each property separately, mostly on flat films, and "
     "records one failure at the package scale: wet-moulded CNF objects were not transparent or dimensionally stable because of "
     "drying shrinkage. I treat the question as a consistency test, checking each requirement against what the literature supports "
     "or against a physical bound and allowing the answer to be no.", align="justify")
para(doc, "**No experiments are reported, and I make no claim that the proposed material works.** The contribution is a "
     "framework and what it returns:", align="justify")
bullet(doc, "**An optical screen with a derived scattering prefactor.** Debye\u2013Bueche scattering theory gives the bulk haze of a dense "
       "nanofibril wall without a fitted constant, and fixes a haze budget by thickness and correlation length: for a 100 \u00b5m wall, "
       "10%% haze and 5%% voids, the correlation length must be about %.0f nm or less. The common cubic law overestimates scattering "
       "by a factor of 7 at 80 nm, the top of the reported bagasse nanofibril range." % a10)
bullet(doc, "**A wet-stiffness screen.** In the screen, chitosan\u2019s benefit is carried by physical cross-linking (median gain "
       "%+.1f GPa with it, %+.1f GPa without) and disappears in an acidic liquid." % (
           G["crosslinking_attribution"]["median_gain_with_crosslinking_GPa"], G["crosslinking_attribution"]["median_gain_without_crosslinking_GPa"]))
bullet(doc, "**A forming screen showing that geometry sets the burden.** A tray, bowl and cup need total strain tolerances of %.2f, "
       "%.2f and %.2f; no combination of the assumed ranges forms the cup (best case %.2f)." % (
           bud["tray (lid-like)"], bud["bowl"], bud["cup"], best))
bullet(doc, "**A ranking of the unknowns** by influence, and falsifiable predictions with numerical thresholds, so that the first "
       "measurements are the informative ones.")
para(doc, "The work is deliberately candid about its limits. Eleven of nineteen parameter ranges are assumptions and are labelled as "
     "such; the screens represent bulk scattering only and do not by themselves reproduce the haze of published clear nanopaper, "
     "which the manuscript reports rather than hides. The code is checked against independent limits (43 verification checks), and "
     "every reference was resolved against its Crossref record by script. In doing so I found that all three transparency references "
     "in an earlier draft were misattributed; they are corrected. Statements of absence, for example that no transparent formed "
     "nanocellulose wall has been reported, rest on documented searches that are included in the Supplementary Information.",
     align="justify")
para(doc, "**Data and code.** The model, verification suite, figure scripts, reference-checking tooling and search log are openly "
     "available at %s (MIT licence) and archived on Zenodo, https://doi.org/%s. The manuscript and Supplementary Information are "
     "archived as a preprint, https://doi.org/%s." % (REPO, CODE_DOI, PAPER_DOI), align="justify")
para(doc, "**Declarations.** The manuscript is original, has not been published elsewhere other than as the preprint noted above, and "
     "is not under consideration at any other journal. I am the sole author and approve the submission. I have no competing "
     "interests, and the work received no external funding. An earlier concept document on this architecture was prepared for an "
     "open-innovation challenge and was never published; the present manuscript is a different, quantitative analysis. In line with "
     "Springer Nature policy, my use of generative AI (Claude, Anthropic) as a drafting and analysis aid is documented in the "
     "Methods (Section 5.5); I directed the work, reviewed all content and take full responsibility for it.", align="justify")
para(doc, "Thank you for considering the manuscript.", space_after=8)
para(doc, "Yours sincerely,", space_after=2)
para(doc, "Leon Sandler")
doc.save(OUT)
print("saved", OUT)
