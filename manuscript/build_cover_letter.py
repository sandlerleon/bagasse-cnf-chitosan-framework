# -*- coding: utf-8 -*-
"""Cover letter for submission to Cellulose (Springer). Numbers come from results.json."""
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
from docx_helpers import bullet, new_document, para  # noqa: E402

R = json.load(io.open(os.path.join(ROOT, "code", "results.json"), encoding="utf-8"))
G, E = R["G_additions"], R["E_envelope"]
LC, JT, PR, KX = R["L_cup_requirement"], R["J_thickness_coupling"], R["I_prior_robustness"], R["K_wax_bounded"]
IDS = json.load(io.open(os.path.join(HERE, "identifiers.json"), encoding="utf-8"))
CODE_DOI = IDS["code_concept_doi"]
PAPER_DOI = IDS["paper_concept_doi"]
REPO = IDS["repository"]
bud = E["strain_budgets"]
a10 = G["a_max_nm"]["t100_haze10_phi05"]
best = E["forming_tolerance_h10"]["max"]
ver = subprocess.run([sys.executable, os.path.join(ROOT, "code", "verify_model.py")], capture_output=True, text=True,
                     encoding="utf-8", cwd=os.path.join(ROOT, "code"))
N_PASS = ver.stdout.count("[PASS]")
assert ver.returncode == 0 and "[FAIL]" not in ver.stdout

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
para(doc, "**No experiments are reported, and I make no claim that the proposed material works.** The contribution is a set of "
     "quantitative constraints and a statement of which measurements would resolve the uncertainty that remains:", align="justify")
bullet(doc, "**An optical screen with a derived scattering prefactor.** Debye\u2013Bueche scattering theory gives the bulk haze of a dense "
       "nanofibril wall without a fitted constant. Under the stated assumptions, a 100 \u00b5m wall at 10%% haze and 5%% voids needs a "
       "correlation length of about %.0f nm or less. The screen does not by itself reproduce the haze of published clear nanopaper, "
       "and the manuscript tests what could close the gap (rough surfaces, a coarse residual population) rather than hiding it." % a10)
bullet(doc, "**A wet-stiffness screen.** Chitosan\u2019s modelled benefit is carried mainly by physical cross-linking (median gain "
       "%+.1f GPa with it, %+.1f GPa without) and is small and of uncertain sign in an acidic liquid." % (
           G["crosslinking_attribution"]["median_gain_with_crosslinking_GPa"], G["crosslinking_attribution"]["median_gain_without_crosslinking_GPa"]))
bullet(doc, "**A forming screen showing that geometry sets the burden.** A tray, bowl and cup need total strain tolerances of %.2f, "
       "%.2f and %.2f; no combination of the assumed ranges forms the cup (best case %.2f), which would need a flange "
       "wrinkling strain above %.2f. The result is stated for drawing a flat sheet and is not claimed as a universal impossibility." % (
           bud["tray (lid-like)"], bud["bowl"], bud["cup"], best, LC["eps_wrinkle_needed_cup_at_best_tensile"]))
bullet(doc, "**What only the combination returns.** Stiffness fixes a minimum wall thickness and thickness fixes the haze, so the "
       "liquid the package must resist changes the optical budget (median minimum thickness %.0f \u00b5m in a neutral liquid, %.0f \u00b5m "
       "in an acidic one). A wax layer applied before forming narrows the forming window of the shallowest geometry. Neither "
       "follows from a single screen." % (JT["t_min_at_median_E_um"]["neutral"], JT["t_min_at_median_E_um"]["acid"]))
bullet(doc, "**A ranking of the unknowns** by influence, and falsifiable predictions with numerical thresholds, so that the first "
       "measurements are the informative ones.")
para(doc, "The work is deliberately candid about its limits. Eleven of nineteen parameter ranges are assumptions and are labelled as "
     "such, and the analysis was repeated under seven prior schemes to separate what is robust (the thresholds, the cup bound and "
     "the ordering of the cases) from what is not (the pass shares, which move by tens of percentage points). Liquid containment "
     "is untested, so every feasibility result is presented as provisional. The code is checked against independent limits (%d "
     "automated verification checks passed; these check the implementation and are not experimental validation), and every "
     "reference was resolved against its Crossref record by script and audited again before submission. In doing so I found "
     "that all three transparency references in an earlier draft were misattributed; they are corrected. Statements of absence, "
     "for example that no transparent formed nanocellulose wall has been reported, rest on documented searches that are included "
     "in the Supplementary Information." % N_PASS, align="justify")
para(doc, "I recognise that a study without experiments sits at the edge of what the journal usually publishes. I have therefore "
     "written it so that its value does not depend on the proposed material working: it defines thresholds that an experimenter "
     "can test, and it identifies where feasibility fails under stated assumptions. If the Editor considers another article type "
     "more suitable, I would welcome guidance.", align="justify")
para(doc, "**Data and code.** The model, verification suite, figure scripts, the numerical tables behind the figures, reference-"
     "checking tooling and search log are openly available at %s (MIT licence) and archived on Zenodo, https://doi.org/%s. The "
     "manuscript and Supplementary Information are archived as a preprint, https://doi.org/%s." % (REPO, CODE_DOI, PAPER_DOI), align="justify")
para(doc, "**Declarations.** The manuscript is original, has not been published elsewhere other than as the preprint noted above, and "
     "is not under consideration at any other journal. I am the sole author and approve the submission. I have no competing "
     "interests, and the work received no external funding. Generative AI (Claude, Anthropic) was used as an assistive tool for code "
     "drafting, code review, figure-script drafting, literature-record retrieval scripts, and drafting and language editing of the manuscript text, as documented in "
     "the Methods (Section 5.5). I defined the research question, requirements and assumptions, directed the workflow and the "
     "verification criteria, reviewed the interpretation of the literature and approved all conclusions. No AI-generated data, "
     "references or conclusions were accepted without my verification, and I take full responsibility for the accuracy, integrity "
     "and interpretation of the work.", align="justify")
para(doc, "Thank you for considering the manuscript.", space_after=8)
para(doc, "Yours sincerely,", space_after=2)
para(doc, "Leon Sandler")
doc.save(OUT)
print("saved", OUT)
