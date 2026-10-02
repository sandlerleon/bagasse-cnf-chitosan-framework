# -*- coding: utf-8 -*-
"""Build TNCC_Supplementary_Information.docx (S1-S10). Numbers come from code/results.json and
the model; references from the verified cache."""
import io
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.join(ROOT, "references"))

import refs as rf                                              # noqa: E402
import tncc_model as m                                         # noqa: E402
from docx_helpers import (DELIM, FRAC, SUB, SUP, T, V, Vs, PI, TAU, LAM, EPS, DELTA,   # noqa: E402
                          EQ, PLUS, MINUS, SQRT, bullet, caption, equation, heading, new_document,
                          page_numbers_and_line_numbers, para, table)

OUT = os.path.join(HERE, "TNCC_Supplementary_Information.docx")
R = json.load(io.open(os.path.join(ROOT, "code", "results.json"), encoding="utf-8"))
C, G, E, S, B, F_ = R["C_monte_carlo"], R["G_additions"], R["E_envelope"], R["D_spearman"], R["B_haze_budget"], R["F_inverse"]
DB = rf.load()
ay = lambda k: "%s %s" % (rf.short_author(k, DB), rf.year_of(k, DB))
P = lambda x, n=0: ("%." + str(n) + "f%%") % (100 * x)

_ver = subprocess.run([sys.executable, os.path.join(ROOT, "code", "verify_model.py")], capture_output=True, text=True,
                      encoding="utf-8", cwd=os.path.join(ROOT, "code"))
N_PASS = _ver.stdout.count("[PASS]")
assert _ver.returncode == 0 and "[FAIL]" not in _ver.stdout, "verification failed"

doc = new_document(size=10.5, line=1.3)
page_numbers_and_line_numbers(doc, line_numbers=False)

para(doc, "Supplementary Information", bold=True, size=15, space_after=2)
para(doc, "Toward transparent rigid packaging from sugarcane bagasse: a consistency-testing framework for "
     "nanocellulose–chitosan sheets", italic=True, space_after=2)
para(doc, "Leon Sandler, Independent Researcher, Northbrook, Illinois, USA. sandler.leon@gmail.com", size=10, space_after=8)
para(doc, "Contents: S1 optical screen (derivation, angular correction, calibration checks, full haze budget); S2 wet-stiffness "
     "screen; S3 forming geometry; S4 literature dataset, per-reference support and documented searches; S5 uncertainty "
     "propagation and sensitivity; S6 experimental matrix; S7 surface and coarse scattering; S8 prior schemes and the robustness panel; S9 thickness "
     "coupling; S10 wax-layer sensitivity. All numbers are produced by code/run_analysis.py (seed 20261002) and are "
     "reproduced by running that script.", size=10)

# ================================================================== S1
heading(doc, "S1 Optical screen", 1)
heading(doc, "S1.1 Derivation of Eq. (2)", 2)
para(doc, "Take a medium whose permittivity fluctuates about its mean by δε(r) with correlation function "
     "⟨δε(0)δε(r)⟩ = ⟨δε^{2}⟩γ(r). In the first Born approximation the light scattered per "
     "unit volume into a unit solid angle at scattering angle θ, for unpolarised incident light of vacuum wavelength λ, is "
     "(Debye and Bueche 1949)", align="justify")
equation(doc, FRAC(T("dΣ"), T("dΩ")) + T(EQ) + FRAC(SUP(V(PI), T("2")), SUP(V(LAM), T("4"))) + T(" ")
         + T("⟨") + SUP(DELIM(V(DELTA) + V(EPS)), T("2")) + T("⟩ ") + V("Γ") + DELIM(V("q")) + T(" ")
         + FRAC(T("1") + T(PLUS) + SUP(T("cos"), T("2")) + V("θ"), T("2")), "S1")
para(doc, "where Γ(q) = ∫γ(r)e^{iq·r}d^{3}r and q = 2k sin(θ/2) with k = 2πn̄/λ. The factor (1 + cos^{2}θ)/2 "
     "accounts for the polarisation of the scattered light. For an exponential correlation function γ(r) = exp(−r/a), the form "
     "that characterises random hole structures in a solid (Debye et al. 1957),", align="justify")
equation(doc, V("Γ") + DELIM(V("q")) + T(EQ) + FRAC(T("8") + V(PI) + SUP(V("a"), T("3")),
                                                    SUP(DELIM(T("1") + T(PLUS) + SUP(V("q"), T("2")) + SUP(V("a"), T("2"))), T("2"))), "S2")
para(doc, "For a solid cellulose phase of index n_{c} and air voids of volume fraction φ, ⟨δε^{2}⟩ = φ(1−φ)(n_{c}^{2} − 1)^{2}. "
     "Integrating Eq. (S1) over the sphere, with u = cos θ and q^{2} = 2k^{2}(1−u), gives the scattering coefficient "
     "τ = 2π ∫ dΣ/dΩ du over u from −1 to 1. In the limit qa ≪ 1 this reduces to "
     "τ = (64π^{4}/3)φ(1−φ)(Δε)^{2}a^{3}/λ^{4} (Eq. 2 with g = 1). The numerical factor follows from "
     "∫(1+u^{2})/2 du = 4/3 over −1 to 1 together with the prefactor of Eq. (S1) and the Debye–Bueche value Γ(0) = 8πa^{3}: "
     "4π × π^{2} × 8π × (2/3) = 64π^{4}/3 ≈ 2078. The exact angular integral relative to this "
     "limit is g(a). The code evaluates it by Gauss–Legendre quadrature (48 nodes) and splits the integral into the "
     "backward hemisphere, the forward hemisphere beyond 2.5° and the forward cone within 2.5°, which gives f_{h} and the "
     "back-scattered fraction.", align="justify")
para(doc, "**Check against an independent result.** For dilute small spheres of volume V and index contrast close to one, the "
     "correlation integral reduces to Γ(0) = V, and Eq. (S1) integrated over angle must reproduce Rayleigh scattering, "
     "τ = Nσ with σ = (2π^{5}/3)D^{6}/λ^{4}[(m^{2}−1)/(m^{2}+2)]^{2}. The verification suite finds a ratio of 1.013 for D = 20 nm, "
     "φ = 10^{−3} and m = 1.01; the residual is the (m^{2}+2) local-field factor, which the Born treatment omits.", align="justify")
heading(doc, "S1.2 The angular correction g(a)", 2)
caption(doc, "**Table S1** Angular correction to the cubic law for n̄ = 1.5 and λ = 550 nm: g is the exact turbidity relative to its "
        "small-feature limit; f_{h} the share of scattered light that goes forward beyond 2.5°; f_{b} the share scattered backward.", keep_next=True)
rows = [["a (nm)", "g(a)", "Cubic law overestimates τ by", "f_{h}", "f_{b}", "kΔn a"]]
for a in (1.0, 2.0, 5.0, 10.0, 15.0, 20.0, 30.0, 40.0, 60.0, 80.0, 120.0):
    g, fh, fb = [float(x) for x in m.angular_split(a, 1.5)]
    kdn = 2 * math.pi / m.LAMBDA0 * 0.55 * a * 1e-9
    rows.append(["%g" % a, "%.3f" % g, "×%.2f" % (1 / g), "%.3f" % fh, "%.3f" % fb, "%.2f" % kdn])
table(doc, rows, widths=[0.8, 0.8, 1.7, 0.8, 0.8, 0.9], size=9)
KDN = {a_: 2 * math.pi / m.LAMBDA0 * 0.55 * a_ * 1e-9 for a_ in (3.0, 10.0, 40.0, 80.0)}
para(doc, "The last column, k\u0394n a with \u0394n = 0.55, is the phase shift across one correlation length. The Born approximation "
     "requires it to be small. It is %.2f at 3 nm, %.2f at 10 nm, %.2f at 40 nm and %.2f at 80 nm, so the approximation is comfortable "
     "at the wood-pulp fibril scale and marginal at the coarse end of the bagasse range (tens of nanometres and above), where results "
     "should be read as indicative." % (KDN[3.0], KDN[10.0], KDN[40.0], KDN[80.0]), align="justify")
heading(doc, "S1.3 Calibration checks", 2)
cal = R["A_calibration_hsieh2017"]
para(doc, "No fitting is done. The checks compare the screen with published values.", align="justify")
bullet(doc, "**Haze of clear nanopaper at 40 µm** (%s: 4.9–11.7%%; density 1.29–1.55 g cm^{−3}; fibre width 3–15 nm). "
       "Wood-pulp-scale structure, 200,000 samples: haze quantiles (5, 25, 50, 75, 95%%) = %s %%; %s of samples inside the observed "
       "band, %s below and %s above. For the bagasse range the quantiles are %s %%, with %s inside, %s below and %s above." % (
           ay("hsieh2017"), ", ".join("%.1f" % x for x in cal["ref"]["haze40_quantiles_5_25_50_75_95"]),
           P(cal["ref"]["fraction_inside_observed_band"]), P(cal["ref"]["fraction_below_band"]), P(cal["ref"]["fraction_above_band"]),
           ", ".join("%.1f" % x for x in cal["bag"]["haze40_quantiles_5_25_50_75_95"]), P(cal["bag"]["fraction_inside_observed_band"]),
           P(cal["bag"]["fraction_below_band"]), P(cal["bag"]["fraction_above_band"])))
bullet(doc, "**Radiative relation** (%s): from a reported direct transmittance the single-scattering slab gives a haze of %.1f%% "
       "(direct 75.1%%, reported haze 10.0%%) and %.1f%% (direct 31.1%%, reported 62.0%%). The relation is therefore good to about "
       "10 percentage points, independent of any structural assumption." % (
           ay("xu2016"), 100 * R["A_xu2016_cross_check"][0]["haze_model"], 100 * R["A_xu2016_cross_check"][1]["haze_model"]))
bullet(doc, "**Lowest reported haze.** A haze of 1.4%% at 91%% transmittance has been reported for super-clear nanopaper from "
       "bagasse nanocrystals (%s); the thickness is not given in the abstract, so it is not used as a quantitative check. It "
       "is, however, of the order of the median haze of the wood-pulp-scale screen at 40 µm (%.1f%%)." % (
           ay("tao2017"), cal["ref"]["haze40_quantiles_5_25_50_75_95"][2]))
heading(doc, "S1.4 Complete haze budget", 2)
caption(doc, "**Table S2** Haze budget by thickness and target. τ_{max} is the largest scattering coefficient compatible with the "
        "target at f_{h} = 0.5; the budget is φ(1−φ)a^{3}g (nm^{3}, with n_{c} = 1.55, f_{m} = 1); a_{max} is the largest "
        "correlation length at each void fraction using the full angular integral.", keep_next=True)
rows = [["t (µm)", "Haze target", "τ_{max} (m^{−1})", "Budget (nm^{3})", "a_{max}, φ = 1%", "2%", "5%", "10%"]]
for t in (40, 100, 200):
    for h in (5, 10):
        b = B["t%d_haze%d" % (t, h)]
        rows.append(["%d" % t, "%d%%" % h, "%.0f" % b["tau_max_per_m"], "%.1f" % b["phi_1mphi_a3_budget_nm3"]] +
                    ["%.1f" % G["a_max_nm"]["t%d_haze%d_phi%02d" % (t, h, p)] for p in (1, 2, 5, 10)])
table(doc, rows, widths=[0.6, 0.8, 0.9, 1.0, 1.0, 0.55, 0.55, 0.55], size=8.5)

# ================================================================== S2
heading(doc, "S2 Wet-stiffness screen", 1)
para(doc, "**Hydration interpolation.** For the chitosan–moisture map the stiffness at hydration h (0 ambient, 1 water-saturated) "
     "is the linear interpolation between the dry rule of mixtures and the saturated value of Eq. (4):", align="justify")
equation(doc, Vs("E", "hyd") + DELIM(V("w") + T(", ") + V("h")) + T(EQ) + Vs("E", "dry") + DELIM(V("w")) + T(MINUS) + V("h")
         + DELIM(Vs("E", "dry") + DELIM(V("w")) + T(MINUS) + Vs("E", "wet") + DELIM(V("w"))), "S3")
para(doc, "with E_{dry}(w) = (1−w)ψ(w)E_{C} + wE_{H} and ψ(w) = 1 + (ψ − 1)[1 − exp(−w/0.05)], so that w = 0 recovers plain CNF "
     "exactly. In an acidic liquid κ_{H} is replaced by κ_{H,acid} and ξ(w) is multiplied by the surviving fraction.", align="justify")
caption(doc, "**Table S3** Water-saturated stiffness (GPa), quantiles over 200,000 samples, and the share of samples meeting each "
        "assumed requirement.", keep_next=True)
rows = [["w (wt%)", "Liquid", "5%", "25%", "50%", "75%", "95%", "≥ 0.5", "≥ 1", "≥ 2", "Helps"]]
for w in (0, 5, 10, 20, 30):
    for liq in ("neutral", "acid"):
        d = C["mech_%s_w%03d" % (liq, w)]
        q = d["E_wet_q5_25_50_75_95_GPa"]
        rows.append(["%d" % w, liq] + ["%.2f" % x for x in q] + [P(d["P_E_ge_0.5"]), P(d["P_E_ge_1.0"]), P(d["P_E_ge_2.0"]),
                                                                     "–" if w == 0 else P(d["P_chitosan_helps"])])
table(doc, rows, widths=[0.55, 0.65, 0.45, 0.45, 0.45, 0.45, 0.45, 0.5, 0.45, 0.45, 0.55], size=8)
xl = G["crosslinking_attribution"]
para(doc, "**Attribution to cross-linking.** At 20 wt%% chitosan in a neutral liquid, with the cross-linking term removed on the same "
     "draws, the median change in wet stiffness is %+.2f GPa and chitosan helps in %s of samples, against %+.2f GPa and %s with it. "
     "**Consistency with published values.** The wet modulus of 4 GPa reported for water-soaked 80/20 films (%s) is reached or "
     "exceeded by %s of modelled samples (modelled 5, 25, 50, 75, 95%% quantiles: %s GPa). The ratio of 8.76/14.71 = %.2f reported "
     "when chitosan was added to carrot nanofibre films (%s) lies inside the assumed range of ψ (%.1f–%.1f)." % (
         xl["median_gain_without_crosslinking_GPa"], P(xl["P_helps_without_crosslinking"]), xl["median_gain_with_crosslinking_GPa"],
         P(xl["P_helps_with_crosslinking"]), ay("toivonen2015"), P(G["toivonen_consistency"]["fraction_of_model_at_or_above_reported"]),
         ", ".join("%.2f" % x for x in G["toivonen_consistency"]["model_E_wet_w20_q5_25_50_75_95"]), G["szymanska_consistency"]["reported_ratio"],
         ay("szymanska2019"), m.PARAMS["psi"][0], m.PARAMS["psi"][1]), align="justify")

# ================================================================== S3
heading(doc, "S3 Forming geometry", 1)
para(doc, "**Window condition.** A blank of diameter D_{0} = LDR·d_{b} drawn into a container of surface area A_{cup} must supply "
     "A_{cup} − πD_{0}^{2}/4 of area by stretching. With uniform equibiaxial thinning the mean tensile log-strain is "
     "ε = ½ ln[A_{cup}/(πD_{0}^{2}/4)] = ε_{b} − ln(LDR), with ε_{b} the strain budget of Eq. (8). The tensile limit "
     "ε ≤ ε_{crit} gives LDR ≥ exp(ε_{b} − ε_{crit}). The compressive circumferential log-strain at the flange edge, "
     "ln(D_{0}/d_{b}) = ln(LDR), is limited by the wrinkling tolerance, so LDR ≤ exp(ε_{wr}). The two bounds are compatible exactly when "
     "ε_{b} − ε_{crit} ≤ ε_{wr}, which is Eq. (10). For a straight-walled cup of depth h and diameter d the budget is "
     "½ ln(1 + 4h/d), so the deepest cup a total tolerance ε can form has h/d = (e^{2ε} − 1)/4 (Fig. 4b).", align="justify")
para(doc, "**The peak is not below the mean.** For any nonuniform distribution of the log-area strain over the sheet with a given "
     "mean, the maximum is at least the mean, so ε_{b} − ln(LDR) is a lower bound on the peak tensile strain. The verification "
     "suite tests this on random nonuniform splits. Friction at the punch radius and local thinning raise the peak further, so the "
     "window condition is necessary, not sufficient.", align="justify")
caption(doc, "**Table S4** Reference geometries (mm) and strain budgets.", keep_next=True)
rows = [["Geometry", "d_{b}", "d_{t}", "h", "A_{cup} (mm^{2})", "A_{cup}/footprint", "ε_{b}", "LDR, no stretching", "Equivalent straight h/d"]]
for g, (d_b, d_t, h) in m.GEOMETRY.items():
    a = m.cup_area(d_b, d_t, h)
    b = m.strain_budget(d_b, d_t, h)
    rows.append([g[0].upper() + g[1:], "%g" % d_b, "%g" % d_t, "%g" % h, "%.0f" % a, "%.2f" % (a / (math.pi * d_b ** 2 / 4)), "%.3f" % b,
                 "%.2f" % math.sqrt(a / (math.pi * d_b ** 2 / 4)), "%.2f" % ((math.exp(2 * b) - 1) / 4)])
table(doc, rows, widths=[1.1, 0.5, 0.5, 0.5, 0.9, 0.9, 0.55, 1.0, 0.9], size=8.5)
caption(doc, "**Table S5** Total strain tolerance ε_{crit} + ε_{wr}: extremes over all assumed ranges (corner enumeration; the "
        "function is monotone in every parameter, so the extremes lie at corners) and the share of samples with a forming window.", keep_next=True)
rows = [["Hydration", "Minimum", "Maximum", "Tray", "Bowl", "Cup"]]
for h, lab in ((0, "Ambient"), (5, "Half"), (10, "Saturated")):
    env = E["forming_tolerance_h%02d" % h]
    rows.append([lab, "%.3f" % env["min"], "%.3f" % env["max"]] + [P(C["forming_%s_h%02d" % (g, h)]["P_window"], 1) for g in ("tray", "bowl", "cup")])
table(doc, rows, widths=[1.1, 0.9, 0.9, 0.8, 0.8, 0.8], size=9)
para(doc, "Budgets are %.3f (tray), %.3f (bowl) and %.3f (cup). The cup budget exceeds the largest tolerance reachable at any "
     "hydration (%.3f at saturation), so no sampling can open a window; the bowl budget lies between the ambient maximum (%.3f) and the "
     "half-hydrated maximum (%.3f)." % (E["strain_budgets"]["tray (lid-like)"], E["strain_budgets"]["bowl"], E["strain_budgets"]["cup"],
                                         E["forming_tolerance_h10"]["max"], E["forming_tolerance_h00"]["max"], E["forming_tolerance_h05"]["max"]), align="justify")

# ================================================================== S4
heading(doc, "S4 Literature dataset, support and searches", 1)
para(doc, "**How the evidence was handled.** Each reference was resolved against its Crossref record by script "
     "(references/harvest.py) and compared with the intended author, year and title; mismatches were investigated before use. "
     "This found that all three of the transparency references in the first version of this manuscript were wrongly attributed "
     "(wrong first author, wrong pages or both); they are corrected here. Each statement was then checked against the cited "
     "source’s abstract where one could be retrieved (Crossref, PubMed, OpenAlex or Semantic Scholar). Table S7 states, for every "
     "reference, whether the statements attached to it rest on an abstract that was read or are limited to what the title says. "
     "Full texts were not available to the verification process.", align="justify")
ABSTRACT_READ = {"nogi2009", "fukuzumi2009", "hsieh2017", "fang2014", "nogi2013", "xu2016", "fukuzumi2013", "henriksson2008",
                 "sehaqui2011", "toivonen2015", "qing2012", "jiang2016", "sellman2024", "niskanen2022", "yang2019", "carneiro2023",
                 "otenda2022", "kim2011", "kabeyi2023", "ndikumana2025", "hiranobe2024", "melro2021", "azeredo2010", "fernandez2024",
                 "szymanska2019", "ghormade2017", "sirvio2021", "wang2017", "vishtal2012", "hauptmann2011", "lyu2019", "arvidsson2015",
                 "kargupta2022", "debye1949", "debye1957", "astm2021", "tao2017", "rol2020", "makela2016", "semple2022", "guzman2022",
                 "lavoine2012", "hubbe2017", "benitez2017", "jager2009"}
DATASET = {"fao2024"}
caption(doc, "**Table S6** Numerical anchors taken from the literature and where each is used.", keep_next=True)
table(doc, [
    ["Quantity", "Value", "Source", "Used for"],
    ["Total transmittance, clear nanopaper, 40 µm", "89.3–91.5%", ay("hsieh2017"), "Context; Table 1"],
    ["Haze, clear nanopaper, 40 µm", "4.9–11.7%", ay("hsieh2017"), "Calibration check (S1.3)"],
    ["Density, clear nanopaper", "1.29–1.55 g cm^{−3}", ay("hsieh2017"), "Range of ρ_{f}"],
    ["Fibre width, clear nanopaper", "3–15 nm", ay("hsieh2017"), "Range of a (wood-pulp scale)"],
    ["TOCN width", "3–4 nm", ay("fukuzumi2009"), "Lower end of a"],
    ["Bagasse nanofibril diameter, microfluidised", "5–80 nm", ay("carneiro2023"), "Range of a (bagasse)"],
    ["Direct transmittance and haze, hybrid CNF/CNC", "75.1% and 10.0% (earlier: 31.1% and 62.0%)", ay("xu2016"), "Radiative-relation check"],
    ["Transmittance and haze, bagasse CNC nanopaper", "91% and 1.4% (thickness not given)", ay("tao2017"), "H1 framing"],
    ["Rice-straw CNF film transmittance", "13–42%", ay("jiang2016"), "H1 framing"],
    ["Neat CNF film modulus", "4.79 GPa; about 4 GPa", "%s; %s" % (ay("qing2012"), ay("jiang2016")), "Range of E_{C}"],
    ["Carrot CNF film modulus, with and without chitosan", "14.71 to 8.76 GPa at 5 wt%", ay("szymanska2019"), "Range of ψ; E_{C} upper bound"],
    ["Neat chitosan film modulus; elongation", "2.3–3.4 GPa; above 13%", ay("fernandez2024"), "Range of E_{H}"],
    ["80/20 CNF/chitosan, wet", "100 MPa, 28% strain, 4 GPa at 0.5% strain", ay("toivonen2015"), "Consistency check; Δε_{w}"],
    ["80/20 CNF/chitosan, 50% RH", "200 MPa, 8% strain", ay("toivonen2015"), "Range of ε_{f0}"],
    ["Rice-straw CNF film strain at break", "16%", ay("jiang2016"), "Range of ε_{f0}"],
    ["Porous TEMPO nanopaper", "56% porosity, 1.4 GPa, 17% strain to failure", ay("sehaqui2011"), "Ductility-clarity tension"],
    ["World sugarcane production, 2022", "1,921 Mt", ay("fao2024"), "Context"],
    ["Bagasse composition", "42% cellulose, 25% hemicellulose, 20% lignin", ay("kim2011"), "Context"],
    ["Refining energy to barrier plateau", "1,800–12,000 kWh t^{−1}", ay("kargupta2022"), "Section 9"],
    ["Aqueous counter-collision defibrillation, rice straw", "15 kWh kg^{−1}", ay("jiang2016"), "Section 9"],
], widths=[2.1, 1.7, 1.4, 1.5], size=8)
caption(doc, "**Table S7** Support classification for every reference. ‘Abstract’: the statements attached to it were checked against "
        "an abstract that was read. ‘Title’: no abstract could be retrieved and the attached statements are limited to what the title "
        "states. ‘Dataset’: a primary data record.", keep_next=True)
rows = [["Reference", "Support"]]
for key, text in rf.all_entries(None):
    sup = "Dataset" if key in DATASET else ("Abstract" if key in ABSTRACT_READ else "Title")
    rows.append([text.split("https://")[0].strip(), sup])
table(doc, rows, widths=[5.7, 0.9], size=7.5)
para(doc, "**Documented searches behind the statements of absence.** Searches were run on 2 October 2026 against the OpenAlex works "
     "index (journal articles, relevance-ranked), the first 12 titles of each were read, and a hit was counted only if it concerned "
     "the thing searched for. The full record is in references/search_log.md. Summary:", align="justify")
bullet(doc, "**Forming of dense nanocellulose sheets** (queries F1–F4: thermoforming, deep drawing, thermoformable three-dimensional "
       "shaping, hot-pressing moulds). Relevant results: %s (wet moulding of CNF mats: objects obtained, none transparent and "
       "dimensionally stable because of drying shrinkage), %s (thermal roll-to-roll imprinting of brittle, non-thermoplastic CNF "
       "films, micrometre-scale patterns only) and %s (moulded pulp review, opaque pulp products). **No report was found of a transparent "
       "dense nanocellulose sheet formed into a three-dimensional shape.**" % (ay("rol2020"), ay("makela2016"), ay("semple2022")))
bullet(doc, "**Transparent sheets from bagasse** (B1–B3). Relevant results: %s (super-clear nanopaper from bagasse nanocrystals, 91%% "
       "transmittance, 1.4%% haze). **No optical data for a transparent sheet made from bagasse nanofibrils were found**; the bagasse "
       "nanofibril studies found (%s; %s) characterise the nanofibrils and composite films." % (
           ay("tao2017"), ay("carneiro2023"), ay("otenda2022")))
bullet(doc, "**Wax-coated and chitosan-containing transparent cellulose films** (W1, C1). The CNF/chitosan wet-strength result of %s was "
       "the only directly relevant hit. A claim carried over from the first version, of transparent carbamylated CNF films with a "
       "water contact angle near 109°, could not be traced to any source and has been removed." % ay("toivonen2015"))
para(doc, "These are searches of one index by title and abstract, not systematic reviews; absence from them is evidence, not proof, "
     "of absence from the literature.", italic=True)

_alog = io.open(os.path.join(ROOT, "references", "audit_log.md"), encoding="utf-8").read()
_n_ok, _n_anch = _alog.count("| ok |"), _alog.count("| found |")
para(doc, "**Final audit.** Before submission every cited DOI was re-resolved against Crossref (references/audit_refs.py; "
     "references/audit_log.md): %d records matched the cached title, first author, journal and volume, none carried a retraction or "
     "withdrawal notice, and %d numerical or qualitative anchors used in the text and in Table 3 were located in the cited abstracts "
     "(for example 4.9–11.7%% haze and 1.29–1.55 g cm^{−3} in %s, 8.76 and 14.71 GPa in %s, 28%% and 4 GPa in %s). Numbers that sit "
     "only in a full text were not checked." % (_n_ok, _n_anch, ay("hsieh2017"), ay("szymanska2019"), ay("toivonen2015")), align="justify")

# ================================================================== S5
heading(doc, "S5 Uncertainty propagation and sensitivity", 1)
para(doc, "**Sampling.** N = 200,000 per test; seed 20261002 (NumPy default_rng, offsets +1, +10, +20, +30, +40, +50 for the calibration, "
     "optical, mechanical, forming, joint and sensitivity draws, and +60 to +100 for the extensions, so the streams are independent). Parameters are drawn independently "
     "from the registry (Table 3 of the main text), uniformly or log-uniformly; the void fraction is derived from the sampled film and "
     "wall densities and clipped to 0–0.5. A sample passes a test when its haze, wet stiffness or forming window meets the "
     "stated requirement; the joint share is the share of samples passing all three.", align="justify")
caption(doc, "**Table S8** Spearman rank correlation of each input with the output.", keep_next=True)
rows = [["Output", "Input", "ρ"]]
LAB = {"optical_bagasse_haze": "Haze, bagasse range, 100 µm", "optical_reference_haze": "Haze, wood-pulp scale, 100 µm",
       "mechanical_neutral_Ewet": "E_{wet}, 20 wt% chitosan, neutral", "mechanical_acid_Ewet": "E_{wet}, 20 wt% chitosan, acid",
       "forming_bowl_margin": "Forming margin, bowl, saturated"}
for k, d in S.items():
    for name, v in sorted(d.items(), key=lambda kv: -abs(kv[1])):
        rows.append([LAB[k], name, "%+.3f" % v])
table(doc, rows, widths=[2.6, 2.2, 0.8], size=8.5)
caption(doc, "**Table S9** Joint share of sampled designs passing all three tests (reference design: 100 µm, 20 wt% chitosan, haze ≤ 10%, "
        "E_{wet} ≥ 1 GPa, forming at saturation).", keep_next=True)
rows = [["Range", "Liquid", "Geometry", "Optical", "Mechanical", "Forming", "All three"]]
for k, d in C["joint_reference_design"].items():
    sc, liq, g = k.split("|")
    rows.append(["wood-pulp scale" if sc == "ref" else "bagasse range", liq, g, P(d["P_optical"]), P(d["P_mechanical"]), P(d["P_forming"]), P(d["P_all"], 1)])
table(doc, rows, widths=[1.3, 0.8, 0.8, 0.8, 0.9, 0.8, 0.8], size=8.5)

# ================================================================== S6
heading(doc, "S6 Experimental matrix", 1)
para(doc, "The matrix lists what each phase would measure, how, and what outcome would count against the framework. "
     "Thresholds marked ‘derived’ follow from the screens; those marked ‘proposed’ are design choices, not results.", align="justify")
table(doc, [
    ["Phase", "Measurement", "Method / standard", "Threshold", "Origin"],
    ["I Material", "Fibril width and length; crystallinity; density", "AFM or TEM; XRD; helium pycnometry and thickness", "Report; compare bagasse with wood pulp", "–"],
    ["I Material", "Void fraction and correlation length", "Small-angle X-ray scattering, Debye–Bueche plot", "φ(1−φ)a^{3} ≤ %.0f nm^{3} (100 µm, 5%% haze); a ≤ %.0f nm at 5%% voids (100 µm, 10%% haze)" % (B["t100_haze5"]["phi_1mphi_a3_budget_nm3"], G["a_max_nm"]["t100_haze10_phi05"]), "Derived"],
    ["I Material", "Haze and transmittance versus thickness", "ASTM D1003 at 40, 100, 200 µm; report thickness", "Haze ∝ t (bulk) or constant (surface)", "Derived"],
    ["I Material", "Surface roughness of both faces; coarse scatterers in the bulk", "AFM or optical profilometry; microscopy, wide-angle scattering", "Two-face haze from roughness ≤ 1%; coarse volume fraction below the haze budget (S7)", "Derived"],
    ["I Material", "Effect of delignification and bleaching", "Haze, colour, lignin content", "Haze within budget at target thickness", "Proposed"],
    ["II Composite", "Wet and dry tensile properties at 0, 5, 10, 20, 30 wt% chitosan", "Tensile test, saturated and 50% RH", "E_{wet} ≥ 1 GPa; gain over plain CNF > 0", "Proposed / derived"],
    ["II Composite", "Acid exposure", "Wet modulus after soaking in acidic liquids", "Gain near zero is the prediction", "Derived"],
    ["II Composite", "Optical effect of chitosan", "Haze, SAXS", "No rise in φ(1−φ)a^{3}", "Derived"],
    ["III Barrier", "Wax layer: thickness, haze, contact angle, liquid hold, abrasion", "Profilometry; ASTM D1003; goniometry; 24 h hold; abrasion test", "Added haze ≤ 1 point (S10); 24 h hold", "Proposed / derived"],
    ["IV Forming", "Biaxial strain to failure, ambient and wet; in situ haze versus strain", "Bulge test with optical haze", "Total tolerance ≥ %.2f (tray), %.2f (bowl)" % (E["strain_budgets"]["tray (lid-like)"], E["strain_budgets"]["bowl"]), "Derived"],
    ["IV Forming", "Wrinkling tolerance", "Draw test with blank holder; LDR at wrinkle onset", "LDR_{max} ≥ %.2f (tray)" % F_["tray (lid-like)"]["required_LDR_if_no_stretching"], "Derived"],
    ["IV Forming", "Shrinkage on drying of any wet-formed part", "Dimensional change; haze after drying", "Report (not modelled)", "%s" % ay("rol2020")],
    ["V Package", "Filled-container drop; lid attachment; thermal cycling; extended containment", "Drop from 1 m; seal test; cycling", "No failure", "Proposed"],
], widths=[0.8, 1.7, 1.7, 1.7, 0.7], size=8)

# ================================================================== S7 surface and coarse scattering
HV, PR, JT, KX, LC = (R["H_optical_validation"], R["I_prior_robustness"], R["J_thickness_coupling"], R["K_wax_bounded"],
                      R["L_cup_requirement"])
SN_ = HV["sigma_needed_nm"]
heading(doc, "S7 Surface and coarse scattering (main text Sections 5.6 and 6.5)", 1)
para(doc, "These bounded additions test how far the optical conclusions depend on what the core screen omits. All ranges are "
     "assumptions (Table S10); none enters the 19-parameter registry or the numbers of main-text Sections 6.1–6.4, which are "
     "unchanged by them (results.json sections A–G are identical in the v1.0.0 and later runs).", align="justify")
caption(doc, "**Table S10** Registry of the parameters of the bounded extensions. Every range is an assumption.", keep_next=True)
rows = [["Parameter", "Range", "Unit", "Dist.", "Meaning"]]
for k, (lo, hi, dist, unit, status, basis) in m.PARAMS_EXT.items():
    rows.append([k, "%g – %g" % (lo, hi), unit, dist, basis])
table(doc, rows, widths=[1.0, 0.9, 0.5, 0.45, 3.75], size=8)
heading(doc, "S7.1 Rough-surface term", 2)
para(doc, "A thin rough interface with zero-mean height h(x, y) of RMS value σ imposes on a transmitted plane wave the phase "
     "(2π/λ)(n_{f} − n_{out}) h. For Gaussian heights and small slopes the coherent amplitude is exp(−Φ²/2), with", align="justify")
equation(doc, V("Φ") + T(EQ) + FRAC(T("2") + V(PI) + DELIM(Vs("n", "f") + T(MINUS) + Vs("n", "out")) + V("σ"), V(LAM)), "S3")
para(doc, "so the specular transmitted fraction is exp(−Φ²) and the fraction scattered is 1 − exp(−Φ²). The fraction beyond the 2.5° "
     "cone is f_{s} times that, where f_{s} (0.3–1, assumed) stands in for the lateral correlation length of the roughness, which is "
     "not represented: long correlation lengths concentrate the scattered light at small angles. The small-roughness limit is "
     "f_{s}Φ². The relation holds for σ much smaller than λ/[2π(n − 1)], about 175 nm. For two identical faces the roughness "
     "that alone gives a haze H follows from 1 − (1 − s)² = H:", align="justify")
equation(doc, V("σ") + T(EQ) + FRAC(V(LAM), T("2") + V(PI) + DELIM(Vs("n", "f") + T(MINUS) + T("1")))
         + SQRT(DELIM(T("−") + T("ln") + DELIM(T("1") + T(MINUS) + FRAC(T("1") + T(MINUS) + SQRT(T("1") + T(MINUS) + V("H")), Vs("f", "s"))))), "S4")
para(doc, "Evaluated with n_{f} = 1.5: σ = %.1f nm for H = 4.9%%, %.1f nm for 8%% and %.1f nm for 11.7%% (f_{s} = 1); %.1f nm for 8%% if only "
     "30%% of the scattered light leaves the cone. The haze of two faces is %.2f%%, %.2f%%, %.2f%% and %.2f%% at σ = 5, 10, 20 and "
     "30 nm." % (SN_["band_low_4.9pct"], SN_["band_mid_8pct"], SN_["band_high_11.7pct"], SN_["band_mid_if_only_30pct_leaves_cone"],
                 HV["surface_haze_pct_for_sigma"]["5nm"], HV["surface_haze_pct_for_sigma"]["10nm"],
                 HV["surface_haze_pct_for_sigma"]["20nm"], HV["surface_haze_pct_for_sigma"]["30nm"]), align="justify")
heading(doc, "S7.2 Combining faces, network and coarse population", 2)
para(doc, "Light is followed through the entrance face, the nanofibril network, the coarse population and the exit face, with the "
     "state (D, F) of direct and diffuse fractions starting at (1, 0). A face of scattered fraction s moves s·D from D to F. A "
     "bulk layer of optical depth x and forward-haze fraction f_{h} moves f_{h}D(1 − e^{−x}) from D to F and multiplies D by e^{−x}. "
     "The haze is F/(D + F). With zero face terms and no coarse population this is exactly Eq. (3) of the main text (checked in "
     "the verification suite). The bookkeeping scatters each ray at most once per element and does not attenuate light that is already "
     "diffuse, so it is an estimate, optimistic at large optical depth, like Eq. (3).", align="justify")
caption(doc, "**Table S11** Haze of a wood-pulp-scale sheet (5th, 25th, 50th, 75th, 95th percentile, %) and the share of samples inside, below "
        "and above the observed 4.9–11.7% band, by thickness and scattering included.", keep_next=True)
rows = [["Thickness", "Scattering", "Percentiles 5/25/50/75/95", "Inside", "Below", "Above"]]
for t in (40, 100, 200):
    for v, lab in (("bulk_only", "bulk only"), ("plus_surface", "+ surfaces"), ("plus_coarse", "+ coarse"), ("plus_both", "+ both")):
        d = HV["calibration_variants_wood_pulp_scale"]["t%d" % t][v]
        rows.append(["%d µm" % t, lab, " / ".join("%.1f" % x for x in d["haze_q5_25_50_75_95_pct"]),
                     P(d["fraction_inside_observed_band"]), P(d["fraction_below_band"]), P(d["fraction_above_band"])])
table(doc, rows, widths=[0.8, 1.0, 2.5, 0.7, 0.7, 0.7], size=8.5)
caption(doc, "**Table S12** Inverse calculation: the coarse volume fraction that alone gives 8% haze at 40 µm, and the haze it implies "
        "thicker. Largest correlation length a (nm) for 100 µm, 10% haze and 5% voids once a baseline is present.", keep_next=True)
rows = [["Coarse size (nm)", "Volume fraction", "Haze at 100 µm", "Haze at 200 µm"]]
for k, d in HV["coarse_population_inverse"].items():
    rows.append([k[1:], "%.4f%%" % (100 * d["phi_coarse_for_8pct_at_40um"]), "%.1f%%" % d["haze_pct_at_100um"], "%.1f%%" % d["haze_pct_at_200um"]])
table(doc, rows, widths=[1.4, 1.6, 1.5, 1.5], size=8.5)
AM_ = HV["a_max_with_baseline_t100_haze10_phi05"]
para(doc, "Largest correlation length at 100 µm, 10%% haze and 5%% voids: %.1f nm with no baseline; %.1f, %.1f and %.1f nm with face "
     "roughness of 5, 10 and 20 nm RMS; %.1f and %.1f nm with a 100 nm coarse population of 0.001%% and 0.005%%." %
     (AM_["none"], AM_["surface_sigma_5nm"], AM_["surface_sigma_10nm"], AM_["surface_sigma_20nm"],
      AM_["coarse_0.001pct_a100nm"], AM_["coarse_0.005pct_a100nm"]), align="justify")

# ================================================================== S8 prior schemes
heading(doc, "S8 Prior schemes and the full robustness panel (main text Section 6.7)", 1)
para(doc, "Each scheme draws all 19 parameters independently (N = 200,000, streams seed + 100 + k). Literature-informed ranges are left "
     "unchanged by the last four schemes; the schemes act on the 11 assumed ranges.", align="justify")
table(doc, [
    ["Scheme", "Definition"],
    ["base", "Uniform, or log-uniform where the range spans an order of magnitude (the distributions of the main text)"],
    ["uniform", "Uniform in linear space for every parameter"],
    ["centred", "Triangular, mode at the middle of the range (geometric middle for log-uniform)"],
    ["widened", "Assumed ranges widened by 50%% of their width on each side, clipped to physical limits (e.g. wrinkle tolerance 0–%.3f, n_{c} %.2f–%.2f)" % (PR["widened_ranges"]["eps_wrinkle"][1], PR["widened_ranges"]["n_cell"][0], PR["widened_ranges"]["n_cell"][1])],
    ["narrowed", "Assumed ranges narrowed to their central 50%"],
    ["optimistic", "Assumed parameters triangular with the mode at the end of the range that helps the test"],
    ["pessimistic", "Assumed parameters triangular with the mode at the end of the range that hurts the test"],
], widths=[1.1, 5.5], size=8.5)
caption(doc, "**Table S13** Outputs of Sections 6.1–6.4 under the seven prior schemes (fractions of samples unless stated).", keep_next=True)
keys = list(PR["panels"]["base"])
rows = [["Output"] + list(PR["schemes"])]
for k in keys:
    row = [k]
    for s in PR["schemes"]:
        v = PR["panels"][s][k]
        row.append(("%.3f" % v) if isinstance(v, float) else ("yes" if v else "no"))
    rows.append(row)
table(doc, rows, widths=[2.0] + [0.68] * 7, size=6.8)
para(doc, "Statements that hold in all seven schemes: tray window > bowl window ≥ cup window (%s); wood-pulp-scale optical pass share > bagasse-range "
     "(%s); chitosan helps in more samples at neutral pH than in acid (%s); median gain in acid < median gain at neutral pH (%s). "
     "The cup has a non-zero window only in: %s." % (
         PR["claims"]["tray_gt_bowl_gt_cup_everywhere"], PR["claims"]["wood_pulp_beats_bagasse_optically_everywhere"],
         PR["claims"]["chitosan_helps_more_in_neutral_than_acid_everywhere"], PR["claims"]["acid_median_gain_below_neutral_everywhere"],
         ", ".join(PR["claims"]["cup_window_nonzero_in_schemes"]) or "none"), align="justify")
Lc = LC
para(doc, "**What the cup needs.** The strain budget of the cup is %.3f and of the bowl %.3f. With every tensile tolerance at its best case "
     "(ε_{crit} = %.2f, saturated), the flange must tolerate a wrinkling strain of %.3f (limiting draw ratio %.2f) for the cup and "
     "%.3f for the bowl; at the median tensile tolerance (%.2f) the cup needs %.3f (draw ratio %.2f). The assumed upper bound of the "
     "wrinkling tolerance is %.2f (draw ratio %.2f)." % (
         Lc["cup_budget"], Lc["bowl_budget"], Lc["best_case_tensile_saturated"], Lc["eps_wrinkle_needed_cup_at_best_tensile"],
         Lc["LDR_max_needed_cup_at_best_tensile"], Lc["eps_wrinkle_needed_bowl_at_best_tensile"], Lc["median_tensile_saturated"],
         Lc["eps_wrinkle_needed_cup_at_median_tensile"], Lc["LDR_max_needed_cup_at_median_tensile"],
         Lc["eps_wrinkle_assumed_upper"], Lc["LDR_max_assumed_upper"]), align="justify")

# ================================================================== S9 thickness coupling
heading(doc, "S9 Thickness coupling of the optical and stiffness screens (main text Section 6.6)", 1)
para(doc, "For a thin plate of modulus E, thickness t and Poisson ratio ν the flexural rigidity is E t³/[12(1 − ν²)]. Holding ν "
     "fixed, equal rigidity gives Eq. (12) of the main text,", align="justify")
equation(doc, Vs("t", "min") + T(EQ) + Vs("t", "ref") + SUP(DELIM(FRAC(Vs("E", "ref"), V("E"))), FRAC(T("1"), T("3"))), "S5")
para(doc, "which is physics only through its t⁻³ scaling. The anchor (E_{ref} = 1 GPa at t_{ref} = 100 µm) is the reference requirement "
     "of the main text, an assumption. A different anchor moves t_{min} by the cube root of the ratio: the table gives the effect on the "
     "median minimum thickness and on the allowed correlation length (5% voids, 10% haze).", align="justify")
caption(doc, "**Table S14** Thickness coupling at 20 wt% chitosan: minimum thickness from the median wet modulus for three anchors, and the "
        "shares of samples meeting the 10% haze target at each sample’s own minimum thickness.", keep_next=True)
rows = [["Liquid", "Median E (GPa)", "Anchor E_{ref} (GPa)", "t_{min} median (µm)", "t_{min} 5–95% (µm), anchor 1 GPa", "a_{max} at t_{min} (nm)",
         "Haze pass: wood-pulp / bagasse"]]
for liq in ("neutral", "acid"):
    d = JT["E_" + liq]
    for anchor in (0.5, 1.0, 2.0):
        tm = float(m.thickness_for_rigidity(d["E_median_GPa"], E_anchor=anchor))
        rows.append([liq, "%.2f" % d["E_median_GPa"], "%.1f" % anchor, "%.0f" % tm,
                     "%.0f–%.0f" % (d["t_min_um_q5_25_50_75_95"][0], d["t_min_um_q5_25_50_75_95"][4]) if anchor == 1.0 else "–",
                     "%.1f" % m.a_max_nm(tm, 0.10, 0.05),
                     "%s / %s" % (P(d["P_coupled_window_ref"]), P(d["P_coupled_window_bag"])) if anchor == 1.0 else "–"])
table(doc, rows, widths=[0.7, 0.8, 0.9, 0.9, 1.4, 0.9, 1.0], size=8)

# ================================================================== S10 wax layer
heading(doc, "S10 Wax layer: bounded optical and forming sensitivity (main text Section 6.8)", 1)
para(doc, "The wax layer enters the optical bookkeeping of S7.2 in two ways: the wax–air face is a rough interface with the index of the "
     "wax and its own RMS height, and crystallites in the layer are a coarse scattering term with the contrast of crystalline against "
     "amorphous wax, Δε_{w} = (n_{w} + Δn)² − n_{w}², in Eq. (2) with φ_{w} and a_{w} and with optical depth τ_{w}t_{w}. Haze added is the difference "
     "between the coated and the uncoated wall on the same film samples (wood-pulp scale, bulk only; one face coated). For forming, a "
     "coating applied before drawing cracks at the tensile strain ε_{wax}, so the tolerated tensile strain becomes min(ε_{crit}, ε_{wax}). All "
     "ranges are in Table S10. Liquid containment is not modelled, and so no result here bears on whether the layer holds liquid.", align="justify")
caption(doc, "**Table S15** Wax-layer sensitivity (assumed ranges).", keep_next=True)
rows = [["Quantity", "100 µm wall", "200 µm wall"]]
for lab, key, fmt in (("Added haze, 5/25/50/75/95th percentile (points)", "added_haze_points_q5_25_50_75_95", "list"),
                      ("Share adding more than 1 point", "P_added_gt_1pt", "p"), ("Share adding more than 2 points", "P_added_gt_2pt", "p"),
                      ("Share adding more than 5 points", "P_added_gt_5pt", "p"),
                      ("Median added, wax face only (points)", "median_added_points_surface_only", "f"),
                      ("Median added, crystallites only (points)", "median_added_points_crystallites_only", "f")):
    row = [lab]
    for t in (100, 200):
        v = KX["optical_t%d" % t][key]
        row.append(" / ".join("%.2f" % x for x in v) if fmt == "list" else (P(v) if fmt == "p" else "%.2f" % v))
    rows.append(row)
table(doc, rows, widths=[3.4, 1.6, 1.6], size=8.5)
rows = [["Geometry", "Forming window, uncoated", "Coated before forming"]]
for g in ("tray", "bowl", "cup"):
    rows.append([g, P(KX["forming_" + g]["P_window_uncoated"], 1), P(KX["forming_" + g]["P_window_coated_before_forming"], 1)])
table(doc, rows, widths=[1.6, 2.2, 2.2], size=8.5)
para(doc, "Spearman rank correlation of the added haze (100 µm) with the inputs: " + "; ".join(
    "%s %+.2f" % (k, v) for k, v in KX["optical_spearman_added_haze_t100"].items()) + ".", align="justify")

heading(doc, "Reproducing every number", 1)
para(doc, "From the repository root: python code/verify_model.py (%d checks); python code/run_analysis.py (writes code/results.json); "
     "python code/make_figures.py (writes the figures) and python code/export_figure_data.py (the numerical tables behind Figures 2–7); python manuscript/build_manuscript.py and "
     "python manuscript/build_si.py (rebuild the documents from results.json). References: python references/refs.py "
     "(formats the list from the cached Crossref records); python references/harvest.py doi <DOI> re-checks a record. Python 3 with NumPy and "
     "Matplotlib; no other numerical dependencies (pinned versions in requirements.txt). python references/audit_refs.py repeats the "
     "reference audit." % N_PASS, align="justify")
doc.save(OUT)
print("saved", OUT)
