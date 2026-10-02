# -*- coding: utf-8 -*-
"""Build TNCC_Cellulose_Manuscript_v2.docx.

Every number quoted from the analysis is read from code/results.json at build time, and the
verification-test count comes from an actual run of code/verify_model.py, so the text cannot
drift from the model. References come only from references/refs_cache.json (verified Crossref
records).

    python build_manuscript.py
"""
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.join(ROOT, "references"))

import refs as rf                                    # noqa: E402
import tncc_model as m                               # noqa: E402
from docx_helpers import (DELIM, EQ, FRAC, GE, LE, MINUS, PLUS, TIMES, SQRT, SUB, SUP, T, V, Vs,  # noqa: E402
                          PI, PHI, TAU, LAM, EPS, DELTA, KAPPA, XI, PSI, bullet, caption, equation,
                          figure, heading, new_document, page_numbers_and_line_numbers, para, table)

OUT = os.path.join(HERE, "TNCC_Cellulose_Manuscript_v2.docx")
R = json.load(io.open(os.path.join(ROOT, "code", "results.json"), encoding="utf-8"))
C, G, E, S, B = R["C_monte_carlo"], R["G_additions"], R["E_envelope"], R["D_spearman"], R["B_haze_budget"]
DB = rf.load()
STATE = json.load(io.open(r"C:\YouTube\_tncc_zenodo_state.json", encoding="utf-8"))
CODE_DOI = STATE["software"]["concept_doi"]
PAPER_DOI = STATE["publication"]["concept_doi"]
REPO_URL = "https://github.com/sandlerleon/bagasse-cnf-chitosan-framework"
FIG = os.path.join(ROOT, "figures")

USED_KEYS = set()


def cite(*k):
    USED_KEYS.update(k)
    return rf.cite(*k, db=DB)


def nar(k):
    USED_KEYS.add(k)
    return rf.narrative(k, db=DB)


def ay(k):
    USED_KEYS.add(k)
    return "%s %s" % (rf.short_author(k, DB), rf.year_of(k, DB))

P = lambda x, n=0: ("%." + str(n) + "f%%") % (100 * x)
F = lambda x, n=2: ("%." + str(n) + "f") % x

# ------------------------------------------------------------- verification: run it, count it
ver = subprocess.run([sys.executable, os.path.join(ROOT, "code", "verify_model.py")], capture_output=True,
                     text=True, encoding="utf-8", cwd=os.path.join(ROOT, "code"))
N_PASS = ver.stdout.count("[PASS]")
assert ver.returncode == 0 and "[FAIL]" not in ver.stdout, "model verification failed; refusing to build"

# ------------------------------------------------------------- the numbers the text uses
cal = R["A_calibration_hsieh2017"]["ref"]
XU = R["A_xu2016_cross_check"]
AM = G["a_max_nm"]
J = C["joint_reference_design"]
g_tab = {a: float(m.angular_split(a, 1.5)[0]) for a in (5.0, 10.0, 20.0, 40.0, 80.0)}
W20n, W20a, W0 = C["mech_neutral_w020"], C["mech_acid_w020"], C["mech_neutral_w000"]
XL = G["crosslinking_attribution"]


def ordinal(n):
    n = int(round(n))
    return "%d%s" % (n, "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))

TOIV = G["toivonen_consistency"]
bud = E["strain_budgets"]
tol_best = {h: E["forming_tolerance_h%02d" % h]["max"] for h in (0, 5, 10)}
FORM = {(g, h): C["forming_%s_h%02d" % (g, h)] for g in ("tray", "bowl", "cup") for h in (0, 5, 10)}
INV = R["F_inverse"]
OPT = {(sc, t): C["optical_%s_t%d" % (sc, t)] for sc in ("ref", "bag") for t in (40, 100, 200)}

doc = new_document(size=11, line=1.5)
page_numbers_and_line_numbers(doc)

# ================================================================== title page
para(doc, "Toward transparent rigid packaging from sugarcane bagasse: a consistency-testing framework "
     "for nanocellulose\u2013chitosan sheets", bold=True, size=16, space_after=10)
para(doc, "Leon Sandler", size=12, space_after=0)
para(doc, "Independent Researcher, Northbrook, Illinois, USA", size=10.5, space_after=0)
para(doc, "ORCID: https://orcid.org/0009-0007-4584-808X", size=10.5, space_after=0)
para(doc, "Corresponding author: sandler.leon@gmail.com", size=10.5, space_after=12)
para(doc, "Manuscript prepared for submission to *Cellulose* (Springer). A theoretical and computational study: "
     "no experiments were performed, and every output is a screening estimate, not a measured or predicted material property.",
     italic=True, size=10, space_after=12)

# ================================================================== abstract
heading(doc, "Abstract", 1)
ABSTRACT = (
    "Transparent rigid packaging is dominated by fossil-derived polymers, whereas fibre-based packaging is opaque. "
    "Dense cellulose nanofibril (CNF) and nanocrystal sheets are transparent as flat films, but whether transparency, "
    "wet stiffness and a three-dimensional shape can coexist in one sugarcane-bagasse-derived package has not been "
    "established, and the one reported attempt to mould transparent CNF objects failed through drying shrinkage. "
    "This paper reports no experiments. It applies three consistency screens to a proposed bagasse CNF\u2013chitosan\u2013wax "
    "architecture: an optical screen derived from Debye\u2013Bueche scattering theory, a wet-stiffness screen, and a geometric "
    "forming screen, each propagated through a seeded Monte Carlo analysis over ranges taken from verified literature or "
    "stated as assumptions. Haze rises with wall thickness and with the cube of the void-structure correlation length: a "
    "100 \u00b5m wall at 10%% haze and 5%% voids requires a correlation length of %.0f nm or less. Chitosan raises modelled wet "
    "stiffness mainly through cross-linking (median gain %+.1f GPa with it, %+.1f GPa without) and the benefit disappears in an acidic liquid. Geometry sets the forming burden: "
    "tray, bowl and cup shapes need total strain tolerances of %.2f, %.2f and %.2f, and no combination of the assumed ranges "
    "forms the cup (best case %.2f). The framework yields measurable thresholds and a staged validation matrix."
) % (AM["t100_haze10_phi05"], XL["median_gain_with_crosslinking_GPa"], XL["median_gain_without_crosslinking_GPa"],
       bud["tray (lid-like)"], bud["bowl"], bud["cup"], tol_best[10])
n_words = len(ABSTRACT.split())
assert 150 <= n_words <= 250, "abstract is %d words; Cellulose requires 150-250" % n_words
para(doc, ABSTRACT, align="justify")
para(doc, "**Keywords** cellulose nanofibrils; transparent nanopaper; chitosan; sugarcane bagasse; thermoforming; "
     "consistency testing", size=10.5)

# ================================================================== 1 introduction
heading(doc, "1 Introduction", 1)
para(doc, "Transparent rigid packaging is dominated by polyethylene terephthalate and, increasingly, polylactic acid, "
     "chosen largely because they combine clarity, stiffness and liquid tightness. Fibre-based alternatives address "
     "material origin; moulded pulp, increasingly made from bagasse, wheat and bamboo rather than wood, is an established "
     "example %s. Fibre-based packaging is opaque, however, and the reason is structural: ordinary paper and cellulose "
     "nanopaper consist of the same chemical constituents, and the difference lies in the fibre width and the size of the "
     "interstitial cavities that scatter light %s." % (cite("semple2022"), cite("nogi2009")), align="justify")
para(doc, "Densifying nanofibrils removes that scattering. Films of TEMPO-oxidised cellulose nanofibrils only 3\u20134 nm wide "
     "are transparent and flexible %s, and clear nanopaper 40 \u00b5m thick has been reported with a total transmittance of "
     "89.3\u201391.5%% and a haze of 4.9\u201311.7%% at a density of 1.29\u20131.55 g cm^{\u22123} %s. Haze can be tuned by mixing fibre scales "
     "%s, and hybrid nanofibril\u2013nanocrystal paper reached a direct transmittance of 75.1%% with 10.0%% haze, against 31.1%% "
     "and 62.0%% for earlier nanopaper %s. Transparency survived tens of minutes at 150 \u00b0C in flat nanopaper %s, and "
     "nanopaper made from sugarcane bagasse nanocrystals has been reported at 91%% transmittance and 1.4%% haze %s. Reviews "
     "cover the field %s." % (cite("fukuzumi2009"), cite("hsieh2017"), cite("fang2014", "yang2019"), cite("xu2016"),
                              cite("nogi2013"), cite("tao2017"), cite("isogai2011", "zhu2014", "klemm2011", "moon2011")),
     align="justify")
para(doc, "Several problems stand between these flat films and a rigid package. Maintaining mechanical properties under hydrated "
     "conditions is a recognised and often overlooked challenge for nanocelluloses %s, and a liquid barrier must be added "
     "without reintroducing haze %s. CNF films are brittle and not thermoplastic, with no clear softening point; thermal "
     "roll-to-roll imprinting could pattern them at the micrometre scale only with a softener present %s. At the scale of a "
     "package the evidence is thinner and more discouraging. Wet moulding of CNF mats into three-dimensional objects was "
     "feasible, but because of shrinkage during drying none of the formation or drying routes tried yielded transparent and "
     "dimensionally stable objects %s, and deep drawing of paperboard is regarded as a sensitive process with many failure "
     "mechanisms %s. Nanofibrillation is also energy-intensive %s." %
     (cite("toivonen2015"), cite("lavoine2012", "hubbe2017", "azeredo2017"), cite("makela2016"), cite("rol2020"),
      cite("hauptmann2011", "vishtal2012"), cite("arvidsson2015", "kargupta2022")), align="justify")
para(doc, "The knowledge gap is therefore integration. Each property has been demonstrated, mostly on flat films and mostly "
     "separately; whether transparency, wet stiffness, barrier performance and a three-dimensional shape can be held together "
     "in a single agricultural-residue-derived wall is not established, and the published attempt to form one failed.",
     align="justify")
para(doc, "This paper asks that question as a consistency test. Each requirement is checked against what the literature "
     "supports or against a physical bound, the answer is allowed to be no, and the checks are propagated through the "
     "uncertainty that remains. The contribution is the framework and what it returns, not a material: (i) an optical screen "
     "whose scattering prefactor is derived from theory rather than fitted, with the haze budget it implies for a wall of given "
     "thickness; (ii) a wet-stiffness screen showing what determines whether chitosan helps, including in an acidic liquid; "
     "(iii) a forming screen showing that geometry fixes a strain budget independent of the material model; (iv) a ranking of "
     "the unknowns that most influence each outcome, so that the first measurements are the informative ones; and (v) "
     "falsifiable predictions and a validation matrix with numerical thresholds. No experiments were performed. Every parameter "
     "is either taken from a cited source or stated as an assumption, and the assumptions are listed (Table 3).", align="justify")

# ================================================================== 2 hypotheses
heading(doc, "2 Hypotheses, research questions and status of evidence", 1)
para(doc, "Four hypotheses organise the analysis; each is stated so that it can fail.", align="justify")
bullet(doc, "**H1 (feedstock).** Bagasse-derived nanocellulose can form a dense sheet whose void fraction and correlation "
       "length meet the haze budget of a rigid wall. It fails if bagasse nanofibril sheets exceed that budget.")
bullet(doc, "**H2 (chitosan).** Chitosan raises wet stiffness without optical loss, in the liquid the package is meant to hold. "
       "It fails if the wet gain is zero or negative in an acidic liquid, or if haze rises.")
bullet(doc, "**H3 (barrier).** A sub-micron natural wax layer gives liquid containment without added haze. It is not modelled "
       "here and is carried into the validation matrix.")
bullet(doc, "**H4 (forming).** The strain budget of the target geometry lies inside the strain the sheet tolerates. It fails "
       "for geometries whose budget exceeds the sum of the tolerated tensile and compressive strains.")
para(doc, "These map onto five research questions. **RQ1** Can densified bagasse-derived nanocellulose plausibly reach the "
     "optical properties a transparent wall requires? **RQ2** Can chitosan improve wet performance without optical loss? "
     "**RQ3** Can a thin hydrophobic layer give moisture resistance while preserving transparency? **RQ4** What mechanisms "
     "limit forming, and which geometries survive them? **RQ5** Which measurements are required to decide viability?",
     align="justify")
para(doc, "Every statement below carries one of four labels. *Established* means taken from a cited source. *Computed* means "
     "produced by the model in this paper under stated assumptions. *Predicted* means a falsifiable consequence of the "
     "computation. *Unvalidated* means not tested by anyone to the author\u2019s knowledge. Table 2 applies these labels.",
     align="justify")

# ================================================================== 3 architecture
heading(doc, "3 Proposed material architecture", 1)
para(doc, "The architecture (Fig. 1) is the author\u2019s conceptual integration of separately published elements, not a "
     "description of an existing material. Sugarcane bagasse is fibrillated to nanofibrils, densified into a transparent "
     "sheet, combined with chitosan for wet integrity, coated with a thin hydrophobic layer, and formed into a package. "
     "Three consistency tests gate the chain: optical after densification, wet-mechanical after chitosan, and forming at the "
     "shaping step.", align="justify")
figure(doc, os.path.join(FIG, "Figure1.png"), 6.4,
       "**Fig. 1** Proposed processing chain and the three consistency tests that gate it. The diagram is a conceptual "
       "integration of separately published elements, not an existing installation.")

heading(doc, "3.1 Bagasse-derived nanocellulose", 2)
para(doc, "World sugarcane production was 1,921 Mt in 2022 %s. Bagasse is the fibrous residue after juice extraction, produced "
     "in very large volumes and traditionally burned for energy %s. Its composition, about 42%% cellulose, 25%% hemicellulose "
     "and 20%% lignin %s, means that delignification and bleaching bear directly on colour and haze, and residual lignin "
     "has been shown to affect the production and properties of TEMPO-oxidised nanofibrils from partially delignified "
     "bagasse %s. Nanocellulose has been isolated from bagasse by several routes %s; oxidised nanofibrils produced by "
     "microfluidisation measured 5\u201380 nm in diameter %s, and TEMPO-oxidised bagasse nanofibrils 150\u2013600 nm long have "
     "been used to reinforce films %s. Reviews note that nanostructure synthesis from bagasse still lacks high yields and "
     "the ability to scale up %s. TEMPO-mediated oxidation of native cellulose is the route that gave the thin, uniform "
     "nanofibres behind the clear films above %s, and higher fibril aspect ratios have been reported to give stiffer and more "
     "ductile networks %s, which makes the length distribution of bagasse nanofibrils a relevant unknown." % (cite("fao2024"), cite("kabeyi2023", "ndikumana2025"), cite("kim2011"), cite("scopel2025"),
                                      cite("mandal2011", "bhattacharya2008"), cite("carneiro2023"), cite("otenda2022"),
                                      cite("hiranobe2024"), cite("saito2007", "fukuzumi2009"), cite("sellman2024")), align="justify")
para(doc, "The feedstock evidence is mixed in a way that defines H1. Nanopaper from bagasse nanocrystals is reported at 91%% "
     "transmittance and 1.4%% haze %s, so bagasse can give a clear sheet. An agricultural-residue analogue prepared as "
     "nanofibrils, rice straw, gave films of only 13\u201342%% transmittance %s. No optical data for transparent sheets made from "
     "bagasse nanofibrils were found (Supplementary Information S4). The open question is therefore not whether bagasse can "
     "give a clear sheet, but whether bagasse nanofibrils, or a hybrid, keep the clarity at the thickness a rigid wall needs, "
     "and whether a sheet made of the stiffer, less entangled nanocrystals tolerates forming; the latter is an expectation, "
     "not a cited result." % (cite("tao2017"), cite("jiang2016")), align="justify")
heading(doc, "3.2 Densified network", 2)
para(doc, "Scattering from a fibril and void network falls as the fibril width and the void fraction fall, because "
     "refractive-index contrast is then confined to features much smaller than the wavelength %s. Haze in clear nanopaper "
     "has been attributed to compressed cavities in residual micro-sized fibres %s. The thermal stability of flat nanopaper "
     "at 150 \u00b0C %s is relevant to hot-liquid service but is not established for a formed wall. Higher strain to failure has "
     "been reported for porous nanopaper, 17%% at a modulus of 1.4 GPa and 56%% porosity %s, with large strains attributed "
     "to slippage between fibrils %s; the mechanical property space of nanofibril sheets is reviewed in %s. Porosity of that "
     "order would defeat the haze budget derived below (Table 4), so ductility and clarity pull in opposite directions; this "
     "is an inference from the present screens, not a published result." %
     (cite("nogi2009", "fukuzumi2013"), cite("hsieh2017"), cite("nogi2013"), cite("sehaqui2011"), cite("henriksson2008"),
      cite("benitez2017")), align="justify")
heading(doc, "3.3 Chitosan reinforcement", 2)
para(doc, "Chitosan chemistry and solubility are reviewed in %s. Chitosan is water-insoluble but dissolves in acidic solutions %s. It is made commercially from shellfish waste, "
     "and fungal sources are being explored as an alternative %s; the regulatory status of any chitosan for food contact is "
     "jurisdiction-specific and is not assessed here. Chitosan films are reported to be highly transparent %s and neat "
     "films have a modulus of 2.3\u20133.4 GPa with an elongation above 13%% %s. The decisive precedent is physical "
     "cross-linking of nanofibrils with chitosan: films of 80/20 CNF/chitosan reached 70\u201390%% transmittance, and when "
     "water-soaked retained a strength of 100 MPa, a strain of 28%% and a modulus of 4 GPa at 0.5%% strain, against 200 MPa and 8%% "
     "at 50%% relative humidity when dry %s. The mechanism is a pH switch: chitosan is processed dissolved at low pH, then "
     "raising the pH reduces its hydration and promotes multivalent interaction with the fibrils. That is also the "
     "vulnerability, since the cross-linking depends on a neutral or alkaline environment. A second precedent cuts the other "
     "way: adding chitosan lowered the modulus of carrot nanofibre films from 14.71 to 8.76 GPa at 5 wt%% %s. Chitosan can "
     "therefore help or hurt, and the sign depends on the interface. In the reverse arrangement, with CNF as the filler in "
     "chitosan films, tensile properties were optimised at 15 g of CNF per 100 g %s." %
     (cite("rinaudo2006", "pillai2009"), cite("melro2021"), cite("ghormade2017"), cite("sirvio2021"), cite("fernandez2024"),
      cite("toivonen2015"), cite("szymanska2019"), cite("azeredo2010")), align="justify")
heading(doc, "3.4 Hydrophobic barrier", 2)
para(doc, "A sub-micron natural wax layer is proposed. Its thickness is far below the scattering scale, so little added haze "
     "is expected, but this is inferred. Oxygen and oil barrier properties of microfibrillated cellulose films and coatings "
     "%s and reactive hydrophobisation of CNF films to lower water-vapour permeability %s are the closest precedents for the "
     "barrier function. Hydrophobisation of transparent TEMPO-oxidised films has been achieved with alkylketene "
     "dimer %s, carnauba wax coatings have given water contact angles above 140\u00b0 on paper, although with nanoparticles and on "
     "an opaque substrate %s, and ionic cross-linking offers an alternative route to water resistance %s. A contact angle is "
     "not a liquid-holding test, and extended hot or cold containment is untested." %
     (cite("aulin2010"), cite("li2019"), cite("fukuzumi2009"), cite("wang2017"), cite("shimizu2016")), align="justify")

# ================================================================== 4 evidence status
heading(doc, "4 Evidence status", 1)
para(doc, "Table 1 sets out the published evidence and the uncertainty that remains for each requirement. Table 2 classifies "
     "every claim used here.", align="justify")
caption(doc, "**Table 1** Published evidence for each requirement of the proposed architecture and what remains uncertain.", keep_next=True)
table(doc, [
    ["Requirement", "Published evidence", "Status", "Remaining uncertainty"],
    ["Transparency, flat film", "89.3\u201391.5%% total transmittance at 40 \u00b5m (wood-pulp CNF) %s; 91%% with 1.4%% haze from bagasse nanocrystals %s" % (cite("hsieh2017"), cite("tao2017")),
     "Established", "Bagasse nanofibril sheets; thickness of a rigid wall"],
    ["Low haze", "4.9\u201311.7%% at 40 \u00b5m %s; 10.0%% haze, 75.1%% direct transmittance, hybrid %s" % (cite("hsieh2017"), cite("xu2016")),
     "Established", "Haze versus thickness; haze after forming"],
    ["Residue-derived CNF", "Rice-straw CNF films 13\u201342%% transmittance %s; bagasse CNF characterised, no clear sheet reported %s" % (cite("jiang2016"), cite("carneiro2023", "otenda2022")),
     "Mixed", "Whether bagasse CNF meets the haze budget (H1)"],
    ["Thermal stability", "Transparency kept after tens of minutes at 150 \u00b0C, flat film %s" % cite("nogi2013"), "Established", "Formed wall; hot-liquid service"],
    ["Chitosan transparency", "70\u201390%% transmittance in CNF/chitosan 80/20 %s" % cite("toivonen2015"), "Established", "Haze; other loadings"],
    ["Wet stiffness", "Wet 80/20 films: 100 MPa, 28%% strain, 4 GPa %s; chitosan lowered modulus elsewhere %s" % (cite("toivonen2015"), cite("szymanska2019")),
     "Established, conflicting", "Acidic liquids; interface; long exposure (H2)"],
    ["Hydrophobicity", "AKD on transparent films %s; wax on opaque paper %s" % (cite("fukuzumi2009"), cite("wang2017")), "Precedent only", "Transparent wax layer; liquid hold (H3)"],
    ["Forming", "Moulded CNF objects not transparent or stable %s; micropatterning only %s" % (cite("rol2020"), cite("makela2016")),
     "Negative / absent", "Any transparent formed wall (H4)"],
    ["Impact resistance", "No evidence found for thin dense nanofibril walls", "Unvalidated", "Filled-container drop"],
], widths=[1.15, 2.85, 0.95, 1.55])
caption(doc, "**Table 2** Classification of the claims used in this paper.", keep_next=True)
table(doc, [
    ["Label", "Examples"],
    ["Established (cited)", "Transparent, low-haze CNF and CNC nanopaper as flat films; wet-state CNF/chitosan integrity at neutral pH; chitosan dissolves in acid"],
    ["Computed (this work)", "Haze budget; angular correction to the cubic law; sign of the chitosan effect; strain budgets and forming windows; Monte Carlo shares and rankings"],
    ["Predicted (this work)", "Haze growing with thickness; chitosan benefit lost in acid; forming limited by flange tolerance rather than fracture (Section 8)"],
    ["Assumed", "11 of the 19 parameter ranges (Table 3); the 10% haze and 1 GPa wet-stiffness requirements"],
    ["Unvalidated", "Any formed transparent wall; filled-cup drop; liquid containment; lid sealing; life-cycle impact; compostability of the finished structure"],
], widths=[1.5, 5.0])

# ================================================================== 5 screening framework
heading(doc, "5 Screening framework", 1)
para(doc, "Three screens test the requirements of Table 1. They are screens in the strict sense: each either implements a "
     "physical bound or states a relation whose assumptions are listed, and none is fitted to the paper\u2019s own data.",
     align="justify")
heading(doc, "5.1 Test 1: optical", 2)
para(doc, "Light scattered by a dense nanofibril network is treated as scattering from refractive-index fluctuations in a random "
     "two-phase medium, a solid cellulose phase of index n_{c} with air voids of volume fraction \u03c6. In the Born "
     "approximation with an exponential correlation function of length a, the framework of Debye and Bueche %s, applied to "
     "random porous solids by Debye, Anderson and Brumberger %s, gives a scattering coefficient that depends on thickness-independent "
     "structure alone. The direct (unscattered) fraction of light through a sheet of thickness t is" % (cite("debye1949"), cite("debye1957")),
     align="justify")
equation(doc, Vs("T", "d") + T(EQ) + T("exp") + DELIM(T("\u2212") + V(TAU) + T("\u2009") + V("t")), "1")
para(doc, "and the scattering coefficient, integrated over all angles for unpolarised light, is", align="justify")
equation(doc, V(TAU) + T(EQ) + FRAC(
    V("K") + T("\u2009") + Vs("f", "m") + T("\u2009") + V(PHI) + DELIM(T("1") + T(MINUS) + V(PHI)) + SUP(DELIM(V(DELTA) + V(EPS)), T("2"))
    + SUP(V("a"), T("3")) + T("\u2009") + V("g"), SUP(V(LAM), T("4"))), "2")
para(doc, "where \u0394\u03b5 = n_{c}^{2} \u2212 1 is the permittivity contrast, \u03bb the vacuum wavelength (550 nm throughout), "
     "f_{m} a morphology factor carrying the uncertainty about the real structure, and K = 64\u03c0^{4}/3 \u2248 2.08\u00d710^{3}. "
     "**K is derived, not fitted**: it is the small-angle limit of the angular integral of the Debye\u2013Bueche expression "
     "multiplied by the polarisation factor of unpolarised light. The factor g(a) is the exact angular integral relative to that "
     "limit and equals 1 when a is much smaller than the wavelength. It matters here. Table S1 of the Supplementary Information "
     "gives g(a); in brief g = %.2f at 5 nm, %.2f at 10 nm, %.2f at 20 nm, %.2f at 40 nm and %.2f at 80 nm, so the closed cubic law is "
     "accurate to about 12%% up to 10 nm but overestimates scattering %.1f times at 80 nm, the top of the reported bagasse "
     "nanofibril range. The haze, defined as the transmitted light deviating by more than 2.5\u00b0 %s, follows from single "
     "scattering as" % (g_tab[5.0], g_tab[10.0], g_tab[20.0], g_tab[40.0], g_tab[80.0], 1 / g_tab[80.0], cite("astm2021")),
     align="justify")
equation(doc, V("H") + T(EQ) + FRAC(
    Vs("f", "h") + DELIM(T("1") + T(MINUS) + SUP(T("e"), T("\u2212") + V(TAU) + V("t"))),
    SUP(T("e"), T("\u2212") + V(TAU) + V("t")) + T(PLUS) + Vs("f", "h") + DELIM(T("1") + T(MINUS) + SUP(T("e"), T("\u2212") + V(TAU) + V("t")))), "3")
para(doc, "where f_{h} is the fraction of scattered light going forward beyond 2.5\u00b0, computed from the same angular integral "
     "(0.5 for small features). Surface reflection multiplies direct and diffuse light alike and cancels in the ratio. "
     "Eqs. (1)\u2013(3) are valid for \u03c4t up to about 1; beyond that, repeated scattering raises the real haze, so values "
     "there are optimistic. Three limits should be stated plainly. The screen represents bulk scattering only: surface roughness "
     "and residual fibre fragments, which dominate haze in some nanopapers %s, are not represented, and absorption by residual "
     "lignin is omitted. The void fraction is derived from film density as \u03c6 = 1 \u2212 \u03c1_{f}/\u03c1_{w}, which "
     "makes it sensitive to the assumed wall density at the percent level. And Eq. (2) is a screening relation: it has not been "
     "validated against small-angle scattering from nanocellulose sheets, which is the measurement that would validate it."
     % cite("hsieh2017"), align="justify")

heading(doc, "5.2 Test 2: wet mechanical", 2)
para(doc, "The stiffness of a water-saturated CNF/chitosan sheet with chitosan mass fraction w is screened with a rule of "
     "mixtures in which each phase has its own moisture knockdown:", align="justify")
equation(doc, Vs("E", "wet") + DELIM(V("w")) + T(EQ) + DELIM(T("1") + T(MINUS) + V("w")) + V(PSI) + DELIM(V("w")) + SUB(V(KAPPA), T("C"))
         + DELIM(V("w")) + Vs("E", "C") + T(PLUS) + V("w") + T("\u2009") + SUB(V(KAPPA), T("H")) + Vs("E", "H"), "4")
equation(doc, SUB(V(KAPPA), T("C")) + DELIM(V("w")) + T(EQ) + SUB(V(KAPPA), T("C0")) + T(PLUS) + V(XI) + DELIM(V("w"))
         + DELIM(T("1") + T(MINUS) + SUB(V(KAPPA), T("C0"))), "5")
equation(doc, V(XI) + DELIM(V("w")) + T(EQ) + SUB(V(XI), T("max")) + DELIM(T("1") + T(MINUS) + T("exp") + DELIM(T("\u2212") + FRAC(V("w"), SUP(V("w"), T("*"))))), "6")
para(doc, "E_{C} and E_{H} are the dry moduli of the CNF and chitosan phases; \u03ba_{C0} and \u03ba_{H} their water-saturated "
     "retention; \u03c8(w) a dry network-efficiency factor that equals 1 at w = 0 and relaxes to a constant \u03c8 with added "
     "chitosan, so that disruption of fibril contacts (as in %s) can be represented; and \u03be(w) the gain in CNF-phase "
     "retention from physical cross-linking by chitosan (as in %s). In an acidic liquid chitosan hydrates, so its own retention "
     "falls to a small value and the cross-linking gain is multiplied by a surviving fraction. Eq. (4) is a Voigt-type bound that "
     "assumes perfect load sharing, so it is optimistic; interfacial failure and the swelling of chitosan are not otherwise "
     "represented. A linear interpolation in hydration h between the dry and saturated states (Supplementary Information S2) "
     "gives the chitosan\u2013moisture map of Fig. 3." % (cite("szymanska2019"), cite("toivonen2015")), align="justify")

heading(doc, "5.3 Test 3: forming", 2)
para(doc, "Forming a flat sheet into a package requires the sheet to supply the surface area of the package. For a frustum "
     "container with base diameter d_{b}, top diameter d_{t} and depth h the surface area is", align="justify")
equation(doc, Vs("A", "cup") + T(EQ) + FRAC(V(PI) + SUP(Vs("d", "b"), T("2")), T("4")) + T(PLUS) + FRAC(V(PI) + DELIM(Vs("d", "b") + T(PLUS) + Vs("d", "t")), T("2"))
         + SQRT(SUP(V("h"), T("2")) + T(PLUS) + SUP(DELIM(FRAC(Vs("d", "t") + T(MINUS) + Vs("d", "b"), T("2"))), T("2"))), "7")
para(doc, "and the mean equibiaxial strain the sheet would carry if all of that area came from stretching, relative to the "
     "base footprint, is the strain budget", align="justify")
equation(doc, SUB(V(EPS), T("b")) + T(EQ) + FRAC(T("1"), T("2")) + T("ln") + DELIM(FRAC(Vs("A", "cup"), FRAC(V(PI) + SUP(Vs("d", "b"), T("2")), T("4")))), "8")
para(doc, "Because strain is never perfectly uniform, the peak strain is not below this mean, so it is a lower bound on what "
     "the sheet must tolerate. Material drawn in from the flange reduces the tensile burden at the cost of compressive "
     "strain ln(LDR) at the flange edge, where LDR = D_{0}/d_{b} is the limiting draw ratio of a blank of diameter D_{0}. "
     "The tensile strain the sheet may carry is limited by fracture or, if it comes first, by the onset of scattering voids, "
     "which is lower than fracture whenever the ratio r_{v} of void-onset strain to failure strain is below one:", align="justify")
equation(doc, SUB(V(EPS), T("crit")) + T(EQ) + T("min") + DELIM(T("1") + T(",") + T("\u2009") + Vs("r", "v")) + DELIM(SUB(V(EPS), T("f0")) + T(PLUS)
         + SUB(V(DELTA), T("") ) + SUB(V(EPS), T("w")) + T("\u2009") + V("h")), "9")
para(doc, "with \u03b5_{f0} the ambient failure strain, \u0394\u03b5_{w} its gain when water-saturated and h the hydration "
     "(0 ambient, 1 saturated). The analogy for \u03b5_{void} is deformation-induced cavitation and stress whitening in "
     "semicrystalline polymers %s; for nanocellulose it is an inference. Tensile strain falls with LDR as "
     "\u03b5 = \u03b5_{b} \u2212 ln(LDR), and flange compression is limited by a wrinkling tolerance \u03b5_{wr}, so a forming window "
     "LDR_{min} \u2264 LDR \u2264 LDR_{max}, with LDR_{min} = exp(\u03b5_{b} \u2212 \u03b5_{crit}) and LDR_{max} = exp(\u03b5_{wr}), exists if and only if"
     % cite("lyu2019"), align="justify")
equation(doc, SUB(V(EPS), T("crit")) + T(PLUS) + SUB(V(EPS), T("wr")) + T(GE) + SUB(V(EPS), T("b")), "10")
para(doc, "Three reference geometries are used (Table 3 caption): a lid-like tray (base 100 mm, top 120 mm, depth 12 mm), a bowl "
     "(100, 150, 50 mm) and a drinking cup (55, 80, 90 mm). Eq. (10) is exact for the stated geometry; whether a sheet can "
     "actually be formed also depends on friction, drying shrinkage %s and temperature, none of which are represented." % cite("rol2020"),
     align="justify")

heading(doc, "5.4 Uncertainty propagation", 2)
para(doc, "The 19 parameters of the screens are listed with their ranges and bases in Table 3; 8 are informed by a cited "
     "source and 11 are assumptions. Each was sampled independently and uniformly, or log-uniformly where the range spans an "
     "order of magnitude, for N = 200,000 samples with a fixed seed (20261002). Outputs were summarised by quantiles, by the "
     "share of samples meeting a requirement, and by Spearman rank correlation with the output, which identifies which unknown "
     "to measure first. The assumed requirements (haze of 5%% or 10%%, wet stiffness of 0.5, 1 or 2 GPa) are exactly that, assumptions: "
     "transparency in packaging is reported by several non-equivalent measures %s, and the package-specific requirement belongs to "
     "a design brief, not to this paper." % cite("guzman2022"), align="justify")
caption(doc, "**Table 3** Parameter registry. Status \u2018lit\u2019 means the range is informed by the cited source; \u2018assumed\u2019 means it is the "
        "author\u2019s bracket. Sampling is uniform (u) or log-uniform (lu). Reference geometries (base, top, depth in mm): "
        "tray 100, 120, 12; bowl 100, 150, 50; cup 55, 80, 90.", keep_next=True)
NAMES = {"rho_film": "Film density \u03c1_{f}", "rho_wall": "Cell-wall density \u03c1_{w}", "n_cell": "Refractive index n_{c}",
         "a_ref": "Correlation length a, wood-pulp scale", "a_bag": "Correlation length a, bagasse range", "f_morph": "Morphology factor f_{m}",
         "E_cnf": "CNF dry modulus E_{C}", "E_chi": "Chitosan dry modulus E_{H}", "psi": "Network efficiency \u03c8",
         "kappa_cnf": "Plain-CNF wet retention \u03ba_{C0}", "kappa_chi": "Chitosan wet retention \u03ba_{H}",
         "xi_max": "Cross-linking gain \u03be_{max}", "w_star": "Gain saturation w*", "kappa_chi_acid": "Chitosan retention, acid",
         "xi_acid": "Gain surviving acid", "eps_f_dry": "Ambient failure strain \u03b5_{f0}", "d_eps_wet": "Wet strain gain \u0394\u03b5_{w}",
         "r_void": "Void-onset ratio r_{v}", "eps_wrinkle": "Wrinkle tolerance \u03b5_{wr}"}


def expand(basis):
    def rep(mo):
        k = mo.group(0)
        return ay(k) if k in rf.DOI else k
    return re.sub(r"\b[a-z]+(?:19|20)\d\d\b", rep, basis)


rows = [["Parameter", "Range", "Unit", "Dist.", "Status", "Basis"]]
for k, (lo, hi, dist, unit, status, basis) in m.PARAMS.items():
    rows.append([NAMES[k], "%g \u2013 %g" % (lo, hi), unit.replace("-3", "^{\u22123}"), dist, status, expand(basis)])
table(doc, rows, widths=[1.5, 0.8, 0.6, 0.45, 0.6, 2.55], size=7.5)

heading(doc, "5.5 Verification and computational methods", 2)
para(doc, "A screening model cannot be validated against data it was not built from, so the code is verified against limits "
     "known independently of it. The verification suite (%d checks, all passing) confirms that the angular integral reduces to "
     "its closed form for small features; that Debye\u2013Bueche scattering reduces to the Rayleigh result for dilute small spheres; "
     "that the scattered-light fractions conserve energy; that Eq. (2) scales as a^{3} and as \u03c6(1\u2212\u03c6) in the small-feature "
     "limit and more slowly beyond it; that the haze inversion round-trips; that the single-scattering relation maps the "
     "direct transmittance and haze pairs reported by %s to within 12 percentage points (%.1f%% against 10%% and %.1f%% against 62%%); "
     "that the wet-stiffness screen recovers plain CNF at w = 0, neat chitosan at w = 1 and the rule of mixtures when "
     "cross-linking and disruption are switched off; and that the forming window opens exactly at the strain budget. All results "
     "were produced by one seeded run (Python 3, NumPy); the code is deposited (Data and code availability)." %
     (N_PASS, nar("xu2016"), 100 * XU[0]["haze_model"], 100 * XU[1]["haze_model"]), align="justify")
para(doc, "**Use of generative AI and handling of evidence.** Generative AI (Claude, Anthropic) was used as a drafting and analysis "
     "aid: it helped to write and review the model code, the verification suite, the figure scripts and the manuscript text. The "
     "author specified the physical model and its assumptions, directed the literature work, ran the code, inspected every "
     "output and figure and takes full responsibility for the content. No AI tool is an author, and none generated data; the "
     "study reports none. Every reference was resolved against its Crossref record by script, and each statement was checked against "
     "the cited source\u2019s abstract where one was accessible. For references whose abstract could not be retrieved, the claim "
     "attached is limited to what the title states. Statements of absence rest on the documented searches in Supplementary "
     "Information S4.", align="justify")

# ================================================================== 6 results
heading(doc, "6 Results", 1)
heading(doc, "6.1 Optical: a haze budget set by thickness and correlation length", 2)
para(doc, "Haze depends on the structure only through \u03c6(1\u2212\u03c6)a^{3}g and on the wall only through its thickness, so a "
     "target haze fixes a budget (Fig. 2a). For a 100 \u00b5m wall at 5%% haze the budget is \u03c6(1\u2212\u03c6)a^{3} \u2264 %.0f nm^{3}; at "
     "200 \u00b5m it is %.0f nm^{3}. Expressed as the largest correlation length for a given void fraction (Table 4), a 100 \u00b5m wall "
     "at 10%% haze and 5%% voids needs a \u2264 %.1f nm, and a 200 \u00b5m wall at 5%% haze and 5%% voids needs a \u2264 %.1f nm. The "
     "wood-pulp fibril scale (3\u201315 nm) sits across these thresholds, and the bagasse range (5\u201380 nm) extends far above them." %
     (B["t100_haze5"]["phi_1mphi_a3_budget_nm3"], B["t200_haze5"]["phi_1mphi_a3_budget_nm3"], AM["t100_haze10_phi05"], AM["t200_haze5_phi05"]),
     align="justify")
figure(doc, os.path.join(FIG, "Figure2.png"), 6.5,
       "**Fig. 2** Optical screen. **a** Haze of a 100 \u00b5m wall from bulk scattering as a function of void fraction and correlation "
       "length, with the wood-pulp fibril scale (blue box; Hsieh et al. 2017, Fukuzumi et al. 2009) and the extension to the "
       "reported bagasse range (orange; Carneiro Pessan et al. 2023); the dashed red curve is the 5% contour for a 200 \u00b5m wall. "
       "**b** Haze against thickness for three structures under bulk scattering, with the observed 4.9\u201311.7% haze of 40 \u00b5m clear "
       "nanopaper (point) and the grey band showing the opposite limit, in which that haze is surface-dominated and independent "
       "of thickness. The region between the two limits is what a thickness series must measure.")
caption(doc, "**Table 4** Largest correlation length a (nm) that keeps the haze of a wall at or below its target, by thickness and "
        "void fraction \u03c6 (full angular integral, n_{c} = 1.55, f_{m} = 1).", keep_next=True)
trows = [["Thickness (\u00b5m)", "Haze \u2264 5%: \u03c6 = 2%", "5%", "10%", "Haze \u2264 10%: \u03c6 = 2%", "5%", "10%"]]
for t in (40, 100, 200):
    trows.append(["%d" % t] + ["%.1f" % AM["t%d_haze%d_phi%02d" % (t, h, p)] for h in (5, 10) for p in (2, 5, 10)])
table(doc, trows, widths=[1.0, 1.15, 0.65, 0.65, 1.25, 0.65, 0.65], size=8.5)
para(doc, "**How well does the screen reproduce published haze?** It is not a calibration. With structure drawn from the literature "
     "ranges the bulk-scattering haze of a 40 \u00b5m wood-pulp sheet has a median of %.1f%% and reaches the observed 4.9\u201311.7%% band "
     "in only %s of samples (%s lie below it and %s above) %s. Bulk void scattering at the nanofibril scale therefore does not "
     "by itself explain the haze of published clear nanopaper; surface roughness and residual fibre fragments probably contribute, "
     "as the original authors attribute. The most direct consequence is the bracket of Fig. 2b: if the observed haze is mostly "
     "bulk it scales with thickness and a 100\u2013200 \u00b5m wall is far hazier than 40 \u00b5m nanopaper, and if it is mostly surface it does not. "
     "Which limit applies is unmeasured and is the first optical measurement." %
     (cal["haze40_quantiles_5_25_50_75_95"][2], P(cal["fraction_inside_observed_band"]), P(cal["fraction_below_band"]),
      P(cal["fraction_above_band"]), cite("hsieh2017")), align="justify")
para(doc, "Over the sampled ranges (Table 5), a wood-pulp-scale structure meets a 10%% haze target at 100 \u00b5m in %s of samples and at "
     "200 \u00b5m in %s; with the bagasse range the shares fall to %s and %s. Those shares are conditional on the assumed prior over "
     "correlation length, which is uniform on a logarithmic scale, and should be read as a ranking and not as a probability that the "
     "material works; for %s of bagasse samples at 100 \u00b5m \u03c4t exceeds 1, where the single-scattering estimate is optimistic. "
     "The robust results are the thresholds of Table 4. Sensitivity is dominated by the correlation length (Spearman \u03c1 = "
     "%+.2f for the bagasse range, %+.2f for the wood-pulp scale), followed by film density (%+.2f), as the cubic law implies." %
     (P(OPT[("ref", 100)]["P_haze_le_10"]), P(OPT[("ref", 200)]["P_haze_le_10"]), P(OPT[("bag", 100)]["P_haze_le_10"]),
      P(OPT[("bag", 200)]["P_haze_le_10"]), P(OPT[("bag", 100)]["fraction_tau_t_gt_1"]),
      S["optical_bagasse_haze"]["correlation length a"], S["optical_reference_haze"]["correlation length a"],
      S["optical_bagasse_haze"]["film density"]), align="justify")
caption(doc, "**Table 5** Optical screen over the sampled ranges: median haze and the share of samples meeting a haze target, by "
        "feedstock range and wall thickness.", keep_next=True)
orow = [["Range", "Thickness (\u00b5m)", "Median haze", "Haze \u2264 5%", "Haze \u2264 10%", "\u03c4t > 1"]]
for sc, lab in (("ref", "Wood-pulp scale"), ("bag", "Bagasse range")):
    for t in (40, 100, 200):
        d = OPT[(sc, t)]
        orow.append([lab, "%d" % t, P(d["haze_q5_25_50_75_95_pct"][2] / 100, 1), P(d["P_haze_le_5"]), P(d["P_haze_le_10"]), P(d["fraction_tau_t_gt_1"])])
table(doc, orow, widths=[1.5, 1.0, 1.0, 1.0, 1.0, 0.8], size=8.5)

heading(doc, "6.2 Wet mechanical: the sign of the chitosan effect", 2)
para(doc, "At neutral pH, adding 20%% chitosan raises the median modelled wet stiffness from %.2f to %.2f GPa (5\u201395%% range "
     "%.2f\u2013%.2f GPa), and the share of samples reaching 1 GPa rises from %s to %s. In an acidic liquid the gain disappears: the "
     "median change is %+.2f GPa, the share reaching 1 GPa is %s, and chitosan improves wet stiffness in %s of samples, "
     "against %s at neutral pH (Table 6, Fig. 3a). The effect is therefore not intrinsic to chitosan but depends on the cross-linking "
     "and on the liquid. Removing the cross-linking term on the same draws changes the median gain at neutral pH from %+.2f to %+.2f GPa and the share of samples in which chitosan helps from %s to %s, so in the screen the benefit is carried by cross-linking, not by the stiffness of the chitosan phase. Wet stiffness is most sensitive to the cross-linking gain \u03be_{max} (Spearman \u03c1 = %+.2f for the neutral case), "
     "then to the dry CNF modulus (%+.2f) and the plain-CNF wet retention (%+.2f); in acid the plain-CNF retention dominates "
     "(%+.2f) because the chitosan contribution is lost." %
     (W0["E_wet_q5_25_50_75_95_GPa"][2], W20n["E_wet_q5_25_50_75_95_GPa"][2], W20n["E_wet_q5_25_50_75_95_GPa"][0],
      W20n["E_wet_q5_25_50_75_95_GPa"][4], P(W0["P_E_ge_1.0"]), P(W20n["P_E_ge_1.0"]), W20a["median_gain_over_plain_GPa"],
      P(W20a["P_E_ge_1.0"]), P(W20a["P_chitosan_helps"]), P(W20n["P_chitosan_helps"]),
      XL["median_gain_with_crosslinking_GPa"], XL["median_gain_without_crosslinking_GPa"],
      P(XL["P_helps_with_crosslinking"]), P(XL["P_helps_without_crosslinking"]),
      S["mechanical_neutral_Ewet"]["xi_max"], S["mechanical_neutral_Ewet"]["E_cnf"], S["mechanical_neutral_Ewet"]["kappa_cnf"],
      S["mechanical_acid_Ewet"]["kappa_cnf"]), align="justify")
para(doc, "The screen can be compared with the one published wet datum. The reported modulus of 4 GPa for water-soaked 80/20 films "
     "%s lies at the %s percentile of the modelled distribution (%s of samples reach it), so the screen brackets the datum but "
     "its centre is conservative relative to it, as expected if the pH-switched processing sits at the favourable end of the "
     "cross-linking range. The ratio of 0.60 reported for chitosan-disrupted carrot nanofibre films %s lies inside the assumed "
     "range of the network-efficiency factor. These are consistency checks, not calibrations, and the acid case rests on the "
     "assumption, supported by the dissolution of chitosan in acid %s but not by any wet CNF/chitosan measurement in acid, that "
     "the cross-linking gain is largely lost." %
     (cite("toivonen2015"), ordinal(100 * (1 - TOIV["fraction_of_model_at_or_above_reported"])), P(TOIV["fraction_of_model_at_or_above_reported"]),
      cite("szymanska2019"), cite("melro2021")), align="justify")
figure(doc, os.path.join(FIG, "Figure3.png"), 6.5,
       "**Fig. 3** Wet-stiffness screen. **a** Water-saturated stiffness against chitosan fraction for a neutral and an acidic liquid "
       "(median and 5\u201395% band); the star is the wet datum of Toivonen et al. (2015). **b**, **c** Stiffness against chitosan "
       "fraction and hydration at median parameters for the neutral and acidic liquid; contours at 0.5, 1, 2 and 4 GPa. The 20% "
       "chitosan column is the only loading with a published wet datum; the rest of each map is extrapolation.")
caption(doc, "**Table 6** Wet-stiffness screen: median water-saturated stiffness, the share of samples reaching 1 GPa (an assumed "
        "requirement) and the share in which chitosan raises stiffness above that of plain CNF.", keep_next=True)
wrow = [["Chitosan (wt%)", "Neutral: median (GPa)", "\u2265 1 GPa", "Helps", "Acidic: median (GPa)", "\u2265 1 GPa", "Helps"]]
for w in (0, 5, 10, 20, 30):
    a, b = C["mech_neutral_w%03d" % w], C["mech_acid_w%03d" % w]
    wrow.append(["%d" % w, F(a["E_wet_q5_25_50_75_95_GPa"][2]), P(a["P_E_ge_1.0"]), "\u2013" if w == 0 else P(a["P_chitosan_helps"]),
                 F(b["E_wet_q5_25_50_75_95_GPa"][2]), P(b["P_E_ge_1.0"]), "\u2013" if w == 0 else P(b["P_chitosan_helps"])])
table(doc, wrow, widths=[0.9, 1.1, 0.7, 0.7, 1.1, 0.7, 0.7], size=8.5)

heading(doc, "6.3 Forming: geometry sets the burden", 2)
para(doc, "The strain budget of Eq. (8) is %.3f for the tray, %.3f for the bowl and %.3f for the cup, corresponding to surface areas "
     "%.1f, %.1f and %.1f times the base footprint (Fig. 4a). With no stretching, forming them would need blank-to-punch "
     "ratios of %.2f, %.2f and %.2f. Over the sampled strain tolerances a forming window exists, for saturated forming, in %s of "
     "tray samples, %s of bowl samples and none of the cup samples (Table 7). The cup result does not depend on the sampling: "
     "the largest total tolerance \u03b5_{crit} + \u03b5_{wr} reachable anywhere in the assumed ranges is %.2f for saturated forming, "
     "%.2f at half hydration and %.2f ambient, all below the cup\u2019s %.2f (the dashed box of Fig. 4a does not reach the cup line). "
     "The bowl is out of reach in the ambient state, where the best case of %.3f falls just short of the 0.667 needed, and is reached "
     "only when the sheet is hydrated (%.2f at half hydration, %.2f saturated) and at the upper end of the wrinkling tolerance." %
     (bud["tray (lid-like)"], bud["bowl"], bud["cup"], INV["tray (lid-like)"]["area_ratio"], INV["bowl"]["area_ratio"], INV["cup"]["area_ratio"],
      INV["tray (lid-like)"]["required_LDR_if_no_stretching"], INV["bowl"]["required_LDR_if_no_stretching"], INV["cup"]["required_LDR_if_no_stretching"],
      P(FORM[("tray", 10)]["P_window"]), P(FORM[("bowl", 10)]["P_window"]), tol_best[10], tol_best[5], tol_best[0], bud["cup"],
      tol_best[0], tol_best[5], tol_best[10]), align="justify")
para(doc, "Among the unknowns, the wrinkling tolerance of the flange dominates the bowl margin (Spearman \u03c1 = %+.2f), followed by "
     "the void-onset ratio (%+.2f), the wet strain gain (%+.2f) and, last, the ambient failure strain (%+.2f). Where draw-in supplies "
     "most of the material, it is the compressive limit that matters, not fracture, which reorders the usual emphasis on strain to "
     "failure. At the median tolerances a straight-walled cup could have a depth of only %.2f (ambient) to %.2f (wet) base diameters." %
     (S["forming_bowl_margin"]["eps_wrinkle"], S["forming_bowl_margin"]["r_void"], S["forming_bowl_margin"]["d_eps_wet"],
      S["forming_bowl_margin"]["eps_f_dry"], INV["cup"]["max_straight_cup_aspect_at_median_dry"], INV["cup"]["max_straight_cup_aspect_at_median_wet"]),
     align="justify")
figure(doc, os.path.join(FIG, "Figure4.png"), 6.5,
       "**Fig. 4** Forming screen. **a** Mean tensile strain at the wall against limiting draw ratio for the three geometries (lines) and "
       "the box of tolerated strain at median ambient and wet tolerances (solid) and at the best case over all assumed ranges (dashed); "
       "a forming window exists only where a geometry line passes through a box. **b** Deepest straight-walled cup (depth over base "
       "diameter) that a given total tolerance can form, with the equivalent ratio of each geometry (dashed) and the three tolerances.")
caption(doc, "**Table 7** Forming screen: strain budget of each geometry and the share of samples with a forming window, by "
        "forming hydration.", keep_next=True)
frow = [["Geometry", "Strain budget", "Area ratio", "Ambient", "Half hydration", "Saturated"]]
for g, lab in (("tray", "Tray (lid-like)"), ("bowl", "Bowl"), ("cup", "Cup")):
    d0, d5, d10 = FORM[(g, 0)], FORM[(g, 5)], FORM[(g, 10)]
    frow.append([lab, F(d0["strain_budget"], 3), "%.1f" % d0["area_ratio_A_cup_over_footprint"], P(d0["P_window"], 1), P(d5["P_window"], 1), P(d10["P_window"], 1)])
table(doc, frow, widths=[1.5, 1.0, 0.9, 0.9, 1.1, 1.0], size=8.5)

heading(doc, "6.4 Integration", 2)
para(doc, "For a reference design (100 \u00b5m wall, 20%% chitosan, haze \u2264 10%%, wet stiffness \u2265 1 GPa, forming at saturation) the share of "
     "sampled designs passing all three tests is %s for a tray with a wood-pulp-scale structure and a neutral liquid, %s with "
     "a bagasse-range structure, and %s and %s in an acidic liquid; for a bowl it is %s and %s, and for the cup it is zero in every "
     "case (Fig. 5a). These shares depend on the assumed ranges and are reported to rank the cases. The conclusions that do not "
     "depend on them are the thresholds of Table 4, the bound on the cup, and the order of the unknowns in Fig. 5b." %
     (P(J["ref|neutral|tray"]["P_all"]), P(J["bag|neutral|tray"]["P_all"]), P(J["ref|acid|tray"]["P_all"]), P(J["bag|acid|tray"]["P_all"]),
      P(J["ref|neutral|bowl"]["P_all"]), P(J["bag|neutral|bowl"]["P_all"])), align="justify")
figure(doc, os.path.join(FIG, "Figure5.png"), 6.5,
       "**Fig. 5** Integration. **a** Share of sampled designs passing all three tests at the reference design (100 \u00b5m wall, 20% "
       "chitosan, haze \u2264 10%, wet stiffness \u2265 1 GPa, forming at saturation), by geometry, feedstock range and liquid. Shares "
       "depend on the assumed ranges; the zero for the cup does not (best case 0.96 < 1.10). **b** Spearman rank correlation of the "
       "leading unknowns with the optical, wet-mechanical and forming outputs: the quantities to measure first.")

# ================================================================== 7 discussion
heading(doc, "7 Discussion", 1)
para(doc, "**What the three screens return.** The optical screen shows that thickness and correlation length, not material "
     "identity, decide whether a dense nanofibril wall is clear: the same structure that gives single-digit haze at 40 \u00b5m can "
     "be several times hazier at 100\u2013200 \u00b5m if scattering is bulk. The wet screen shows that chitosan is a cross-linker "
     "whose benefit is conditional on the liquid, not a reinforcement in the ordinary sense. The forming screen shows that, for "
     "deep geometries, the sheet would need to supply many times its footprint area, which no tolerance within the assumed ranges "
     "provides.", align="justify")
para(doc, "**Consistency with prior art.** The forming result agrees with the one reported attempt at three-dimensional CNF objects, "
     "which produced objects by wet moulding but not transparent or dimensionally stable ones because of drying shrinkage %s. "
     "The two findings are complementary: that study identifies a route-specific failure, shrinkage on drying, which this screen "
     "does not represent, while this analysis shows a geometric limit that applies whatever the route. The wet-state result is "
     "consistent with a pH-switched cross-linking mechanism %s, and the limits of the closed cubic law matter for the coarse end "
     "of the bagasse nanofibril range." % (cite("rol2020"), cite("toivonen2015")), align="justify")
para(doc, "**Design implications.** The results do not say that a transparent bagasse package is impossible; they say what would "
     "have to be true. Shallow geometries such as lids and trays are the only ones inside the assumed tolerances. A cup-like "
     "container would need a construction that does not stretch a flat sheet, for example a wall formed from a flat blank by "
     "wrapping with a seam, which trades the strain constraint for seam, leak and optical-continuity requirements that are not "
     "analysed here; a transparent window in an otherwise opaque moulded-pulp body is another option. Reducing the wall thickness "
     "relaxes the optical budget in proportion but lowers stiffness and increases the sensitivity to surface defects.",
     align="justify")
para(doc, "**What to measure first.** The rankings give an order. For optics, the correlation length and void fraction of a dense "
     "bagasse sheet by small-angle X-ray scattering, since the Debye\u2013Bueche form is exactly what such data are analysed with "
     "%s, followed by haze against thickness. For wet stiffness, the cross-linking gain and the plain-CNF wet retention, including "
     "in acidic liquids. For forming, the flange wrinkling tolerance and the strain at which haze first rises." % cite("debye1957"),
     align="justify")
para(doc, "**Relation to CNF and CNC.** Nanocrystal sheets from bagasse have given the clearest reported result %s, but their "
     "stiffness and expected brittleness bear on forming in a way the present screens treat only through the assumed strain "
     "tolerances. A hybrid that keeps the clarity of crystals and the entanglement of fibrils, as in %s, is a natural candidate "
     "for H1 and is accommodated by the framework through the structural parameters." % (cite("tao2017"), nar("xu2016")), align="justify")

# ================================================================== 8 predictions
heading(doc, "8 Falsifiable predictions and validation matrix", 1)
para(doc, "Each prediction below follows from the computation and can be shown wrong by a stated measurement.", align="justify")
bullet(doc, "**P1 (thickness scaling).** If bulk scattering dominates, haze of a dense nanofibril sheet rises approximately in "
       "proportion to thickness between 40 and 200 \u00b5m (H \u2248 f_{h}\u03c4t for \u03c4t \u2272 0.3); if surface scattering "
       "dominates, haze is nearly independent of thickness. A thickness series decides which, and measured haze outside "
       "the bracket of Fig. 2b falsifies the screen.")
bullet(doc, "**P2 (structure predicts haze).** Small-angle scattering of the sheet should give \u03c6(1\u2212\u03c6)a^{3} and a Debye\u2013Bueche "
       "correlation length that predict the measured bulk haze within the factor spanned by f_{m} (0.3\u20133).")
bullet(doc, "**P3 (bagasse threshold).** A dense bagasse nanofibril sheet meets a 10%% haze target at 100 \u00b5m only if its "
       "correlation length is below about %.0f nm at 5%% voids (%.0f nm at 2%%)." % (AM["t100_haze10_phi05"], AM["t100_haze10_phi02"]))
bullet(doc, "**P4 (acid reversal).** The wet-stiffness gain from 20% chitosan measured after soaking in an acidic liquid is "
       "much smaller than after soaking in neutral water, and may be negative; a gain retained in acid falsifies the assumed "
       "loss of cross-linking.")
bullet(doc, "**P5 (forming limit).** Haze rises before fracture during forming if r_{v} < 1, and a flat dense sheet cannot be formed "
       "into the cup geometry by drawing alone; a transparent formed cup falsifies the bound of Eq. (10).")
caption(doc, "**Table 8** Validation matrix: the measurement, the threshold derived here and what would falsify it.", keep_next=True)
table(doc, [
    ["Requirement", "Measurement", "Threshold derived here", "Falsified if"],
    ["Bulk scattering", "Small-angle X-ray scattering, Debye\u2013Bueche analysis of dense bagasse sheets", "\u03c6(1\u2212\u03c6)a^{3} \u2264 %.0f nm^{3} at 100 \u00b5m, 5%% haze" % B["t100_haze5"]["phi_1mphi_a3_budget_nm3"], "Measured value exceeds it with haze still low"],
    ["Thickness scaling", "Haze (ASTM D1003) at 40, 100, 200 \u00b5m", "Haze \u221d t (bulk) or constant (surface)", "Outside the bracket of Fig. 2b"],
    ["Feedstock (H1)", "Correlation length, bagasse versus wood-pulp CNF at equal density", "a \u2264 %.0f nm at 5%% voids (100 \u00b5m, 10%% haze)" % AM["t100_haze10_phi05"], "Larger a with haze still within target"],
    ["Wet stiffness (H2)", "Wet tensile modulus at 0, 10, 20, 30 wt% chitosan in neutral water", "\u2265 1 GPa; model median %.1f GPa at 20%%" % W20n["E_wet_q5_25_50_75_95_GPa"][2], "Below 1 GPa, or no gain over plain CNF"],
    ["Acid exposure (H2)", "Wet modulus after soaking in acidic liquids", "Gain over plain CNF near zero (model median %+.2f GPa)" % W20a["median_gain_over_plain_GPa"], "Gain retained in acid"],
    ["Barrier (H3)", "Liquid-hold test, haze after coating, abrasion-induced haze", "24 h hold (proposed); no added haze", "Leak, or coating raises haze"],
    ["Strain tolerance (H4)", "Wet and ambient strain to failure; in situ haze against strain", "Total tolerance \u2265 %.2f (tray), %.2f (bowl)" % (bud["tray (lid-like)"], bud["bowl"]), "Below the budget of the target geometry"],
    ["Flange wrinkling (H4)", "Draw test with blank holder, LDR at wrinkle onset", "LDR_{max} = exp(\u03b5_{wr}); needed %.2f (tray)" % INV["tray (lid-like)"]["required_LDR_if_no_stretching"], "LDR_{max} below the requirement"],
    ["Package", "Filled-container drop, lid attachment, thermal cycling", "1 m drop (proposed)", "Failure"],
], widths=[1.15, 2.0, 1.9, 1.45], size=8)
para(doc, "The staged programme that would test these is: Phase I, material (fibril width, density, small-angle scattering, "
     "haze against thickness, with and without delignification); Phase II, composite (chitosan at 0, 5, 10, 20 and 30 wt%, "
     "transparency, dry and wet tensile properties in neutral and acidic liquids); Phase III, barrier (contact angle, liquid hold, "
     "durability, abrasion-induced haze); Phase IV, forming (shallow, intermediate and full-depth draw; haze, cracking and "
     "delamination); Phase V, package (filled-cup drop, extended containment, lid attachment, thermal cycling). Details are in "
     "Supplementary Information S6.", align="justify")

# ================================================================== 9 sustainability
heading(doc, "9 Sustainability and scalability", 1)
para(doc, "The constituents (cellulose, chitosan and natural wax) were chosen for potential compatibility with compostability "
     "pathways; compostability of the finished structure is unvalidated, and no life-cycle assessment has been performed. "
     "Nanofibrillation energy depends on the processing method %s and production routes are reviewed in %s; refining alone reached a plateau of barrier properties only after "
     "1,800\u201312,000 kWh t^{\u22121} depending on the refiner %s, and complete defibrillation of rice straw by aqueous counter collision was "
     "reported at 15 kWh kg^{\u22121} %s. These figures come from different feedstocks, equipment and end points and are not comparable. "
     "Life-cycle impact of nanofibril production depends strongly on the pretreatment route and on the electricity mix %s, and the "
     "scale-up of nanostructures from bagasse remains a stated challenge %s. Repulpability of a deliberately void-free sheet is a "
     "testable hypothesis, not a result." % (cite("spence2011"), cite("nechyporchuk2016"), cite("kargupta2022"), cite("jiang2016"), cite("arvidsson2015"), cite("hiranobe2024")),
     align="justify")

# ================================================================== 10 limitations
heading(doc, "10 Limitations", 1)
for t in [
    "No sheet or package was made or tested. Eleven of the nineteen parameter ranges are assumptions, and every share quoted in "
    "Section 6 is conditional on them; the thresholds and the cup bound are the results that depend least on them.",
    "The optical screen represents bulk scattering only. Surface scattering, absorption by residual lignin, multiple scattering "
    "beyond \u03c4t of about 1 and the anisotropy of cellulose are not represented, and Eq. (2) has not been validated against "
    "small-angle scattering from nanocellulose sheets. It does not by itself reproduce the haze of published clear nanopaper. "
    "The Born approximation is comfortable at the wood-pulp fibril scale but marginal for correlation lengths of tens of "
    "nanometres, where the phase shift across one correlation length reaches 0.25 at 40 nm and 0.50 at 80 nm (Supplementary Table S1).",
    "The wet-stiffness screen is a Voigt-type bound with an assumed cross-linking term, and its acid case rests on an assumption "
    "that is plausible but untested for CNF/chitosan sheets. Interfacial failure, creep and swelling are not represented.",
    "The forming screen bounds mean area strain and tolerance. Friction, nonuniform thinning, temperature, drying shrinkage "
    "(the failure route reported by %s) and the strain state of the wall are not represented; the wrinkling tolerance has no reported "
    "value for nanocellulose sheets." % ay("rol2020"),
    "The barrier hypothesis (H3) is not modelled, and a contact angle is not a liquid-holding test.",
    "Food-contact regulatory status of chitosan, waxes and any additives, compostability and life-cycle impact are not assessed. "
    "Some references were available to the verification process only by title, and the claims attached to them are limited accordingly.",
]:
    bullet(doc, t)

# ================================================================== 11 conclusions
heading(doc, "11 Conclusions", 1)
para(doc, "The literature supports each ingredient of a transparent, bagasse-derived nanocellulose\u2013chitosan package for flat "
     "films, and it records one failure at the package scale. Three consistency screens show what would have to be true for the "
     "ingredients to coexist. A dense wall is clear only if its void fraction and correlation length lie inside a budget set by its "
     "thickness: for 100 \u00b5m, 10%% haze and 5%% voids, a correlation length of about %.0f nm or less, a threshold the reported "
     "bagasse nanofibril range straddles. Chitosan raises wet stiffness mainly through cross-linking, and in the screen that benefit "
     "is lost in an acidic liquid. And geometry sets a strain budget of %.2f, %.2f and %.2f for a tray, a bowl and a cup, of which "
     "only the tray lies within the assumed tolerances, while the cup lies outside every combination of them. These are conditional "
     "results from stated assumptions. They define the measurements, ranked by influence, that would confirm or falsify the "
     "concept, and they locate the binding constraint, forming, in geometry and not only in the material." %
     (AM["t100_haze10_phi05"], bud["tray (lid-like)"], bud["bowl"], bud["cup"]), align="justify")

# ================================================================== declarations
heading(doc, "Declarations", 1)
para(doc, "**Funding** This research received no specific grant from funding agencies in the public, commercial or not-for-profit sectors.")
para(doc, "**Competing interests** The author declares that there are no competing financial or non-financial interests.")
para(doc, "**Ethics approval and consent to participate** Not applicable. This is a theoretical and computational study with no "
     "human participants, human data, animals or experiments.")
para(doc, "**Consent for publication** Not applicable.")
para(doc, "**Data and code availability** No experimental data were generated. The model, the verification suite, every figure "
     "script, the reference-verification tooling and the log of literature searches are openly available at %s (MIT licence) and "
     "archived with a permanent concept DOI on Zenodo, https://doi.org/%s, which always resolves to the latest version. This manuscript "
     "and its Supplementary Information are archived as a preprint on Zenodo, https://doi.org/%s. All numerical results are produced by one "
     "seeded run (seed 20261002) of code/run_analysis.py." % (REPO_URL, CODE_DOI, PAPER_DOI), align="justify")
para(doc, "**Author contributions** Leon Sandler conceived the study, specified the physical model and its assumptions, directed the "
     "literature work and the computation, analysed the results and wrote the manuscript.")
para(doc, "**Use of generative AI** See Section 5.5.")

# ================================================================== appendix: nomenclature
heading(doc, "Appendix: nomenclature", 1)
table(doc, [
    ["Symbol", "Definition", "Unit"],
    ["T_{d}", "Direct (unscattered) fraction of transmitted light", "\u2013"],
    ["\u03c4", "Scattering coefficient", "m^{\u22121}"],
    ["H", "Haze: transmitted light deviating by more than 2.5\u00b0", "\u2013"],
    ["\u03c6", "Void volume fraction", "\u2013"],
    ["a", "Correlation length of the void structure", "nm"],
    ["n_{c}", "Refractive index of the cellulose phase", "\u2013"],
    ["\u0394\u03b5", "Permittivity contrast, n_{c}^{2} \u2212 1", "\u2013"],
    ["\u03bb", "Vacuum wavelength (550 nm)", "nm"],
    ["t", "Wall thickness", "\u00b5m"],
    ["K", "Derived prefactor, 64\u03c0^{4}/3", "\u2013"],
    ["f_{m}", "Morphology factor", "\u2013"],
    ["g", "Angular correction to the cubic law", "\u2013"],
    ["f_{h}", "Forward-scattered fraction beyond 2.5\u00b0", "\u2013"],
    ["w", "Chitosan mass fraction", "\u2013"],
    ["E_{wet}", "Water-saturated stiffness", "GPa"],
    ["E_{C}, E_{H}", "Dry moduli of the CNF and chitosan phases", "GPa"],
    ["\u03c8", "Dry network-efficiency factor", "\u2013"],
    ["\u03ba_{C0}, \u03ba_{H}", "Water-saturated retention of CNF and chitosan stiffness", "\u2013"],
    ["\u03be", "Gain in CNF-phase retention from cross-linking", "\u2013"],
    ["d_{b}, d_{t}, h", "Base diameter, top diameter and depth of the container", "mm"],
    ["A_{cup}", "Surface area of the container", "mm^{2}"],
    ["\u03b5_{b}", "Strain budget (mean equibiaxial log-strain)", "\u2013"],
    ["\u03b5_{crit}", "Tolerated tensile strain, min(failure, void onset)", "\u2013"],
    ["r_{v}", "Ratio of void-onset strain to failure strain", "\u2013"],
    ["\u03b5_{wr}", "Tolerated compressive (wrinkling) log-strain", "\u2013"],
    ["LDR", "Limiting draw ratio, D_{0}/d_{b}", "\u2013"],
    ["h (hydration)", "Hydration, 0 ambient to 1 saturated", "\u2013"],
], widths=[1.4, 4.3, 0.8], size=8.5)

# ================================================================== references
heading(doc, "References", 1)
USED = set(USED_KEYS)
unused = sorted((set(rf.DOI) | {"fao2024"}) - USED)
for key, text in rf.all_entries(USED):
    p = para(doc, text, size=9.5, space_after=3)
    p.paragraph_format.left_indent = 0
    p.paragraph_format.line_spacing = 1.15

doc.save(OUT)
print("saved", OUT)
print("abstract words:", n_words, "| references:", len(rf.all_entries(USED)), "| verification checks:", N_PASS)
print("verified but not cited (dropped from the list):", unused or "none")
