# -*- coding: utf-8 -*-
"""All numerical results in the manuscript, from one seeded run.

    python run_analysis.py     ->  results.json  (+ a readable summary on stdout)

Sections
  A  calibration of the optical screen against published nanopaper haze
  B  the haze budget: what structure a wall of given thickness may carry
  C  Monte Carlo propagation, three tests, three geometries
  D  Spearman rank sensitivity
  E  best/worst-case envelope over the stated ranges (corner enumeration)
  F  inverse design: what the unvalidated quantities would have to be
"""
import itertools
import json
import math
import os

import numpy as np

import tncc_model as m

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 20261002
N = 200_000
THICKNESS = (40.0, 100.0, 200.0)        # um: nanopaper reference, thin wall, rigid wall
HAZE_TARGETS = (0.05, 0.10)             # ASTM D1003 haze targets, assumed
E_REQ = (0.5, 1.0, 2.0)                 # GPa wet-stiffness thresholds, assumed
CHITOSAN = (0.0, 0.05, 0.10, 0.20, 0.30)
HYDRATION = (0.0, 0.5, 1.0)             # fraction of water-saturated
REF = dict(t=100.0, w=0.20, haze=0.10, e_req=1.0, hydration=1.0)   # headline design point

rng = np.random.default_rng(SEED)
R = {"seed": SEED, "n": N}
q = lambda a: [float(np.percentile(a, p)) for p in (5, 25, 50, 75, 95)]


# ======================================================================= A. calibration
def structure(scenario, n, rng):
    """Draw the optical structure. 'ref' = wood-pulp fibril scale; 'bag' = bagasse range."""
    rho_f = m.draw("rho_film", n, rng)
    rho_w = m.draw("rho_wall", n, rng)
    nc = m.draw("n_cell", n, rng)
    a = m.draw("a_ref" if scenario == "ref" else "a_bag", n, rng)
    fm = m.draw("f_morph", n, rng)
    return dict(phi=m.void_fraction(rho_f, rho_w), nc=nc, a=a, fm=fm, rho_f=rho_f, rho_w=rho_w)


def optical(s, t_um):
    tau, fh, fb = m.turbidity(s["phi"], s["a"], s["nc"], s["fm"])
    direct, haze = m.haze_from_tau(tau, t_um, fh)
    return tau, direct, haze


# Hsieh 2017: clear nanopaper, 40 um, haze 4.9-11.7 %, density 1.29-1.55 g/cm3, fibre width 3-15 nm
cal = {}
for sc in ("ref", "bag"):
    s = structure(sc, N, np.random.default_rng(SEED + 1))
    _, _, h40 = optical(s, 40.0)
    inside = (h40 >= 0.049) & (h40 <= 0.117)
    cal[sc] = {"haze40_quantiles_5_25_50_75_95": q(100 * h40),
               "fraction_inside_observed_band": float(inside.mean()),
               "fraction_below_band": float((h40 < 0.049).mean()),
               "fraction_above_band": float((h40 > 0.117).mean())}
R["A_calibration_hsieh2017"] = cal
# Xu 2016 radiative cross-check, using only the slab relation
xu = []
for d_obs, h_obs in ((0.751, 0.100), (0.311, 0.620)):
    x = -math.log(d_obs)
    _, hp = m.haze_from_tau(x / 1e-6, 1.0, 0.5)
    xu.append({"direct_observed": d_obs, "haze_observed": h_obs, "haze_model": float(hp)})
R["A_xu2016_cross_check"] = xu


# =========================================================================== B. haze budget
bud = {}
for t in THICKNESS:
    for h in HAZE_TARGETS:
        tm = m.haze_budget(t, h, 0.5)
        b = m.bulk_budget_nm3(tm, 1.55, 1.0)
        row = {"tau_max_per_m": tm, "phi_1mphi_a3_budget_nm3": b}
        for a_ in (5.0, 10.0, 15.0):
            g, _, _ = m.angular_split(a_, 1.5)
            # phi(1-phi) <= budget/(a^3 g)  ->  largest void fraction
            lim = b / (a_ ** 3 * float(g))
            row["max_void_fraction_a%d" % a_] = float((1 - math.sqrt(1 - 4 * lim)) / 2) if lim < 0.25 else None
        bud["t%d_haze%d" % (t, round(100 * h))] = row
R["B_haze_budget"] = bud


# ============================================================================ C. Monte Carlo
mc = {}

# --- C1 optical
for sc in ("ref", "bag"):
    s = structure(sc, N, np.random.default_rng(SEED + 10))
    for t in THICKNESS:
        tau, direct, haze = optical(s, t)
        x = tau * t * 1e-6
        d = {"haze_q5_25_50_75_95_pct": q(100 * haze),
             "direct_q5_50_95_pct": [float(np.percentile(100 * direct, p)) for p in (5, 50, 95)],
             "fraction_tau_t_gt_1": float((x > 1).mean())}
        for h in HAZE_TARGETS:
            d["P_haze_le_%d" % round(100 * h)] = float((haze <= h).mean())
        mc["optical_%s_t%d" % (sc, t)] = d

# --- C2 wet mechanics
rm = np.random.default_rng(SEED + 20)
mech = {k: m.draw(k, N, rm) for k in ("E_cnf", "E_chi", "psi", "kappa_cnf", "kappa_chi", "xi_max",
                                      "w_star", "kappa_chi_acid", "xi_acid")}
base_args = {k: mech[k] for k in ("E_cnf", "E_chi", "psi", "kappa_cnf", "kappa_chi", "xi_max", "w_star")}
for liquid in ("neutral", "acid"):
    acid = liquid == "acid"
    e0 = m.E_wet(0.0, **base_args, acid=acid, kappa_chi_acid=mech["kappa_chi_acid"], xi_acid=mech["xi_acid"])
    for w in CHITOSAN:
        e = m.E_wet(w, **base_args, acid=acid, kappa_chi_acid=mech["kappa_chi_acid"], xi_acid=mech["xi_acid"])
        d = {"E_wet_q5_25_50_75_95_GPa": q(e), "P_chitosan_helps": float((e > e0 + 1e-12).mean()) if w > 0 else None,
             "median_gain_over_plain_GPa": float(np.median(e - e0))}
        for th in E_REQ:
            d["P_E_ge_%.1f" % th] = float((e >= th).mean())
        mc["mech_%s_w%03d" % (liquid, round(100 * w))] = d

# --- C3 forming
rf = np.random.default_rng(SEED + 30)
fm_ = {k: m.draw(k, N, rf) for k in ("eps_f_dry", "d_eps_wet", "r_void", "eps_wrinkle")}
for gname, (d_b, d_t, h) in m.GEOMETRY.items():
    budget = m.strain_budget(d_b, d_t, h)
    for hyd in HYDRATION:
        ec = m.eps_crit(fm_["eps_f_dry"], fm_["d_eps_wet"], fm_["r_void"], hyd)
        tot = ec + fm_["eps_wrinkle"]
        ok = tot >= budget
        mc["forming_%s_h%02d" % (gname.split()[0], round(10 * hyd))] = {
            "strain_budget": budget,
            "P_window": float(ok.mean()),
            "tolerance_total_q5_50_95": [float(np.percentile(tot, p)) for p in (5, 50, 95)],
            "P_transparency_limited": float((fm_["r_void"] < 1.0).mean()),
            "area_ratio_A_cup_over_footprint": float(math.exp(2 * budget)),
        }

# --- C4 joint: every test passes at the reference design, shared draws are independent across tests
joint = {}
for sc in ("ref", "bag"):
    s = structure(sc, N, np.random.default_rng(SEED + 40))
    _, _, haze = optical(s, REF["t"])
    p_opt = haze <= REF["haze"]
    for liquid in ("neutral", "acid"):
        acid = liquid == "acid"
        e = m.E_wet(REF["w"], **base_args, acid=acid, kappa_chi_acid=mech["kappa_chi_acid"], xi_acid=mech["xi_acid"])
        p_mech = e >= REF["e_req"]
        for gname, (d_b, d_t, h) in m.GEOMETRY.items():
            ec = m.eps_crit(fm_["eps_f_dry"], fm_["d_eps_wet"], fm_["r_void"], REF["hydration"])
            p_form = (ec + fm_["eps_wrinkle"]) >= m.strain_budget(d_b, d_t, h)
            joint["%s|%s|%s" % (sc, liquid, gname.split()[0])] = {
                "P_optical": float(p_opt.mean()), "P_mechanical": float(p_mech.mean()),
                "P_forming": float(p_form.mean()), "P_all": float((p_opt & p_mech & p_form).mean())}
mc["joint_reference_design"] = joint
mc["reference_design"] = REF
R["C_monte_carlo"] = mc


# ===================================================================== D. Spearman sensitivity
sens = {}
s = structure("bag", N, np.random.default_rng(SEED + 50))
tau, direct, haze = optical(s, REF["t"])
inputs = {"film density": s["rho_f"], "wall density": s["rho_w"], "refractive index": s["nc"],
          "correlation length a": s["a"], "morphology factor": s["fm"]}
sens["optical_bagasse_haze"] = {k: m.spearman(v, haze) for k, v in inputs.items()}
s = structure("ref", N, np.random.default_rng(SEED + 51))
tau, direct, haze = optical(s, REF["t"])
inputs = {"film density": s["rho_f"], "wall density": s["rho_w"], "refractive index": s["nc"],
          "correlation length a": s["a"], "morphology factor": s["fm"]}
sens["optical_reference_haze"] = {k: m.spearman(v, haze) for k, v in inputs.items()}
for liquid in ("neutral", "acid"):
    e = m.E_wet(REF["w"], **base_args, acid=(liquid == "acid"), kappa_chi_acid=mech["kappa_chi_acid"], xi_acid=mech["xi_acid"])
    names = ["E_cnf", "E_chi", "psi", "kappa_cnf", "kappa_chi", "xi_max", "w_star"] + (
        ["kappa_chi_acid", "xi_acid"] if liquid == "acid" else [])
    sens["mechanical_%s_Ewet" % liquid] = {k: m.spearman(mech[k], e) for k in names}
d_b, d_t, h = m.GEOMETRY["bowl"]
ec = m.eps_crit(fm_["eps_f_dry"], fm_["d_eps_wet"], fm_["r_void"], REF["hydration"])
margin = ec + fm_["eps_wrinkle"] - m.strain_budget(d_b, d_t, h)
sens["forming_bowl_margin"] = {k: m.spearman(fm_[k], margin) for k in fm_}
R["D_spearman"] = sens


# ============================================================ E. best/worst-case envelope (corners)
def corners(names, fn):
    """Evaluate fn over every corner of the named parameters. fn is monotone in each
    parameter, so the extrema over the box are attained at corners."""
    vals = [(m.PARAMS[k][0], m.PARAMS[k][1]) for k in names]
    out = []
    for combo in itertools.product(*vals):
        out.append(fn(dict(zip(names, combo))))
    return min(out), max(out)


env = {}
# optical haze at each thickness, bagasse and reference ranges
for sc, aname in (("ref", "a_ref"), ("bag", "a_bag")):
    names = ["rho_film", "rho_wall", "n_cell", aname, "f_morph"]

    def hz(p, t=REF["t"], aname=aname):
        phi = float(m.void_fraction(p["rho_film"], p["rho_wall"]))
        tau, fh, _ = m.turbidity(phi, p[aname], p["n_cell"], p["f_morph"])
        return float(m.haze_from_tau(tau, t, fh)[1])
    for t in THICKNESS:
        lo, hi = corners(names, lambda p, t=t: hz(p, t))
        env["optical_%s_t%d" % (sc, t)] = {"best_case_haze_pct": 100 * lo, "worst_case_haze_pct": 100 * hi}
# forming: total tolerance extremes against each budget
names = ["eps_f_dry", "d_eps_wet", "r_void", "eps_wrinkle"]
for hyd in HYDRATION:
    lo, hi = corners(names, lambda p, hyd=hyd: float(m.eps_crit(p["eps_f_dry"], p["d_eps_wet"], p["r_void"], hyd) + p["eps_wrinkle"]))
    env["forming_tolerance_h%02d" % round(10 * hyd)] = {"min": lo, "max": hi}
env["strain_budgets"] = {g: m.strain_budget(*v) for g, v in m.GEOMETRY.items()}
env["geometries_mm"] = {g: {"base": v[0], "top": v[1], "depth": v[2]} for g, v in m.GEOMETRY.items()}
# mechanics extremes: best-case and worst-case wet stiffness at w = 0.2
names = ["E_cnf", "E_chi", "psi", "kappa_cnf", "kappa_chi", "xi_max", "w_star"]
lo, hi = corners(names, lambda p: float(m.E_wet(REF["w"], **p)))
env["mechanical_neutral_w20_GPa"] = {"min": lo, "max": hi}
names2 = names + ["kappa_chi_acid", "xi_acid"]
lo, hi = corners(names2, lambda p: float(m.E_wet(REF["w"], **{k: p[k] for k in names}, acid=True,
                                                 kappa_chi_acid=p["kappa_chi_acid"], xi_acid=p["xi_acid"])))
env["mechanical_acid_w20_GPa"] = {"min": lo, "max": hi}
# a random sample can never leave the corner envelope (checks monotonicity of the screens)
chk = optical(structure("bag", 50_000, np.random.default_rng(7)), REF["t"])[2]
env["optical_bag_monotone_check"] = bool(100 * chk.max() <= env["optical_bag_t100"]["worst_case_haze_pct"] + 1e-6
                                         and 100 * chk.min() >= env["optical_bag_t100"]["best_case_haze_pct"] - 1e-6)
R["E_envelope"] = env


# ================================================================================ F. inverse design
inv = {}
for gname, (d_b, d_t, h) in m.GEOMETRY.items():
    b = m.strain_budget(d_b, d_t, h)
    inv[gname] = {"strain_budget": b, "area_ratio": math.exp(2 * b),
                  "required_total_tolerance": b,
                  "required_eps_wrinkle_if_eps_crit_is_wet_median":
                  max(0.0, b - float(np.median(m.eps_crit(fm_["eps_f_dry"], fm_["d_eps_wet"], fm_["r_void"], 1.0)))),
                  "required_LDR_if_no_stretching": math.sqrt(math.exp(2 * b)),
                  "max_straight_cup_aspect_at_median_dry": float(m.s_max(np.median(m.eps_crit(fm_["eps_f_dry"], fm_["d_eps_wet"], fm_["r_void"], 0.0)) + np.median(fm_["eps_wrinkle"]))),
                  "max_straight_cup_aspect_at_median_wet": float(m.s_max(np.median(m.eps_crit(fm_["eps_f_dry"], fm_["d_eps_wet"], fm_["r_void"], 1.0)) + np.median(fm_["eps_wrinkle"])))}
# chitosan fraction needed to hold E_req at median parameters, neutral liquid
med = {k: float(np.median(v)) for k, v in mech.items()}
ws = np.linspace(0, 1, 2001)
for th in E_REQ:
    e = m.E_wet(ws, **{k: med[k] for k in base_args})
    ok = ws[e >= th]
    inv["w_needed_for_%.1fGPa_neutral_median" % th] = float(ok.min()) if ok.size else None
R["F_inverse"] = inv

# ======================================================== G. additions: anchors and thresholds
G = {}
# maximum correlation length that keeps a wall at its haze target (full angular integral)
amax = {}
for tt in THICKNESS:
    for h in HAZE_TARGETS:
        for phi in (0.01, 0.02, 0.05, 0.10):
            amax["t%d_haze%d_phi%02d" % (tt, round(100 * h), round(100 * phi))] = m.a_max_nm(tt, h, phi)
G["a_max_nm"] = amax

# consistency of the wet-stiffness screen with the one published wet data point:
# Toivonen 2015, CNF/chitosan 80/20 wet, modulus 4 GPa at 0.5 % strain (neutral, pH-switched).
e20 = m.E_wet(0.20, **base_args)
G["toivonen_consistency"] = {
    "reported_wet_modulus_GPa": 4.0, "chitosan_fraction": 0.20,
    "model_E_wet_w20_q5_25_50_75_95": q(e20),
    "fraction_of_model_at_or_above_reported": float((e20 >= 4.0).mean()),
    "fraction_of_model_below_reported": float((e20 < 4.0).mean())}
# Szymanska 2019: chitosan lowered a CNF film modulus, 14.71 -> 8.76 GPa at 5 wt %: psi ~ 0.60
psi5 = 1.0 + (mech["psi"] - 1.0) * (1.0 - np.exp(-0.05 / 0.05))
G["szymanska_consistency"] = {"reported_ratio": 8.76 / 14.71, "psi_range": [m.PARAMS["psi"][0], m.PARAMS["psi"][1]],
                              "reported_ratio_inside_range": bool(m.PARAMS["psi"][0] <= 8.76 / 14.71 <= m.PARAMS["psi"][1])}

# hydration map at median parameters (chitosan fraction x hydration), neutral and acid
medp = {k: float(np.median(v)) for k, v in mech.items()}
wg = np.linspace(0, 0.5, 51)
hg = np.linspace(0, 1, 41)
W, H = np.meshgrid(wg, hg)
for liquid in ("neutral", "acid"):
    Z = m.E_hyd(W, H, **{k: medp[k] for k in base_args}, acid=(liquid == "acid"),
                kappa_chi_acid=medp["kappa_chi_acid"], xi_acid=medp["xi_acid"])
    G["hydration_map_%s" % liquid] = {"E_at_w0.2_h1": float(m.E_hyd(0.2, 1.0, **{k: medp[k] for k in base_args}, acid=(liquid == "acid"), kappa_chi_acid=medp["kappa_chi_acid"], xi_acid=medp["xi_acid"])),
                                      "E_at_w0.2_h0": float(m.E_hyd(0.2, 0.0, **{k: medp[k] for k in base_args}, acid=(liquid == "acid"), kappa_chi_acid=medp["kappa_chi_acid"], xi_acid=medp["xi_acid"]))}
G["median_parameters"] = medp

# How much of the chitosan benefit is carried by the cross-linking term? Remove it and re-measure
# on the same draws (20 wt% chitosan, neutral liquid).
_e0 = m.E_wet(0.0, **base_args)
_full = m.E_wet(REF["w"], **base_args)
_nox = m.E_wet(REF["w"], **dict(base_args, xi_max=np.zeros(N)))
G["crosslinking_attribution"] = {
    "median_gain_with_crosslinking_GPa": float(np.median(_full - _e0)),
    "median_gain_without_crosslinking_GPa": float(np.median(_nox - _e0)),
    "P_helps_with_crosslinking": float((_full > _e0).mean()),
    "P_helps_without_crosslinking": float((_nox > _e0).mean())}
R["G_additions"] = G

# ============================================================ H. optical-model validation (review v1.1)
# What closes the gap between the bulk-scattering haze and published clear nanopaper? Two bounded
# additions, both with assumed ranges (PARAMS_EXT): rough surfaces, and a coarse residual population.
H = {}
NB = 1.5                                         # effective film index used for the surface term
H["sigma_needed_nm"] = {
    "band_low_4.9pct": m.sigma_for_haze(0.049, NB), "band_mid_8pct": m.sigma_for_haze(0.08, NB),
    "band_high_11.7pct": m.sigma_for_haze(0.117, NB),
    "band_mid_if_only_30pct_leaves_cone": m.sigma_for_haze(0.08, NB, f_surf=0.3),
    "note": "RMS height of each of two surfaces that, alone, gives the haze (scalar theory)"}
sv = structure("ref", N, np.random.default_rng(SEED + 60))
re_ = np.random.default_rng(SEED + 61)
sig = m.draw_ext("sigma_surf", N, re_)
fsf = m.draw_ext("f_surf", N, re_)
phc = m.draw_ext("phi_coarse", N, re_)
acs = m.draw_ext("a_coarse", N, re_)
nbar = np.sqrt((1 - sv["phi"]) * sv["nc"] ** 2 + sv["phi"])
tau_b, fh_b, _ = m.turbidity(sv["phi"], sv["a"], sv["nc"], sv["fm"])
tau_c, fh_c, _ = m.turbidity(phc, acs, sv["nc"], 1.0)
s1 = m.surface_scatter_fraction(sig, nbar, fsf)


def band(h):
    return {"haze_q5_25_50_75_95_pct": q(100 * h), "fraction_inside_observed_band": float(((h >= 0.049) & (h <= 0.117)).mean()),
            "fraction_below_band": float((h < 0.049).mean()), "fraction_above_band": float((h > 0.117).mean())}


var = {}
for t in (40.0, 100.0, 200.0):
    var["t%d" % t] = {
        "bulk_only": band(m.haze_composite(tau_b, fh_b, t, 0.0)),
        "plus_surface": band(m.haze_composite(tau_b, fh_b, t, s1)),
        "plus_coarse": band(m.haze_composite(tau_b, fh_b, t, 0.0, tau_c=tau_c, f_haze_c=fh_c)),
        "plus_both": band(m.haze_composite(tau_b, fh_b, t, s1, tau_c=tau_c, f_haze_c=fh_c))}
H["calibration_variants_wood_pulp_scale"] = var
H["cdf_t40_percentiles_1_to_99"] = {
    "bulk_only": [float(x) for x in np.percentile(100 * m.haze_composite(tau_b, fh_b, 40.0, 0.0), np.arange(1, 100))],
    "plus_surface": [float(x) for x in np.percentile(100 * m.haze_composite(tau_b, fh_b, 40.0, s1), np.arange(1, 100))],
    "plus_coarse": [float(x) for x in np.percentile(100 * m.haze_composite(tau_b, fh_b, 40.0, 0.0, tau_c=tau_c, f_haze_c=fh_c), np.arange(1, 100))],
    "plus_both": [float(x) for x in np.percentile(100 * m.haze_composite(tau_b, fh_b, 40.0, s1, tau_c=tau_c, f_haze_c=fh_c), np.arange(1, 100))]}
H["check_bulk_only_equals_core"] = bool(np.allclose(m.haze_composite(tau_b, fh_b, 40.0, 0.0), m.haze_from_tau(tau_b, 40.0, fh_b)[1]))
# which mechanism, if any, can explain the observed band? share of samples in band, 40 um
H["thickness_bracket_median_haze_pct"] = {
    mech_name: {("t%d" % t): 100 * float(np.median(m.haze_composite(
        tau_b, fh_b, t, s1 if "surface" in mech_name or "both" in mech_name else 0.0,
        tau_c=tau_c if ("coarse" in mech_name or "both" in mech_name) else 0.0, f_haze_c=fh_c)))
        for t in (40.0, 100.0, 200.0)}
    for mech_name in ("bulk_only", "plus_surface", "plus_coarse", "plus_both")}

# robustness of the haze budget itself: largest a that keeps 100 um at 10 % haze, 5 % voids,
# once a baseline from a rough surface or a coarse population is present
def a_max_composite(t_um, haze_max, phi, sigma_nm=0.0, phi_c=0.0, a_c=100.0, n_cell=1.55):
    nb = math.sqrt((1 - phi) * n_cell ** 2 + phi)
    s = float(m.surface_scatter_fraction(sigma_nm, nb, 1.0)) if sigma_nm > 0 else 0.0
    tc, fc = 0.0, 0.5
    if phi_c > 0:
        tc_, fc_, _ = m.turbidity(phi_c, a_c, n_cell, 1.0)
        tc, fc = float(tc_), float(fc_)

    def h(a):
        tau, fh, _ = m.turbidity(phi, a, n_cell, 1.0)
        return float(m.haze_composite(tau, fh, t_um, s, tau_c=tc, f_haze_c=fc))
    lo, hi = 1.0, 200.0
    if h(lo) > haze_max:
        return None
    if h(hi) <= haze_max:
        return hi
    for _ in range(60):
        mid = math.sqrt(lo * hi)
        lo, hi = (mid, hi) if h(mid) <= haze_max else (lo, mid)
    return lo


H["a_max_with_baseline_t100_haze10_phi05"] = {
    "none": a_max_composite(100.0, 0.10, 0.05),
    "surface_sigma_5nm": a_max_composite(100.0, 0.10, 0.05, sigma_nm=5.0),
    "surface_sigma_10nm": a_max_composite(100.0, 0.10, 0.05, sigma_nm=10.0),
    "surface_sigma_20nm": a_max_composite(100.0, 0.10, 0.05, sigma_nm=20.0),
    "coarse_0.001pct_a100nm": a_max_composite(100.0, 0.10, 0.05, phi_c=1e-5, a_c=100.0),
    "coarse_0.005pct_a100nm": a_max_composite(100.0, 0.10, 0.05, phi_c=5e-5, a_c=100.0)}
# inverse: the coarse volume fraction that alone gives 8 % haze at 40 um, and what it implies thicker
inv_c = {}
for a_c in (50.0, 100.0, 200.0, 300.0):
    def hz40(pc, a_c=a_c):
        tc_, fc_, _ = m.turbidity(pc, a_c, 1.55, 1.0)
        return float(m.haze_composite(np.array(0.0), 0.5, 40.0, 0.0, tau_c=tc_, f_haze_c=fc_))
    lo_, hi_ = 1e-9, 1e-1
    for _ in range(80):
        mid_ = math.sqrt(lo_ * hi_)
        lo_, hi_ = (mid_, hi_) if hz40(mid_) < 0.08 else (lo_, mid_)
    pc = lo_
    tc_, fc_, _ = m.turbidity(pc, a_c, 1.55, 1.0)
    inv_c["a%d" % a_c] = {"phi_coarse_for_8pct_at_40um": pc,
                          "haze_pct_at_100um": 100 * float(m.haze_composite(np.array(0.0), 0.5, 100.0, 0.0, tau_c=tc_, f_haze_c=fc_)),
                          "haze_pct_at_200um": 100 * float(m.haze_composite(np.array(0.0), 0.5, 200.0, 0.0, tau_c=tc_, f_haze_c=fc_))}
H["coarse_population_inverse"] = inv_c
H["surface_haze_pct_for_sigma"] = {("%dnm" % s_): 100 * float(1 - (1 - m.surface_scatter_fraction(s_, NB, 1.0)) ** 2)
                                   for s_ in (2, 5, 10, 20, 30)}
R["H_optical_validation"] = H

# ====================================================================== I. robustness to the priors
def panel(scheme, k):
    """The headline outputs of Sections 6.1-6.4 recomputed under a prior scheme."""
    r_ = np.random.default_rng(SEED + 100 + k)
    d = lambda nm: m.draw_scheme(nm, N, r_, scheme)
    out = {}
    # optical, both feedstock ranges
    base_opt = {nm: d(nm) for nm in ("rho_film", "rho_wall", "n_cell", "f_morph")}
    phi = m.void_fraction(base_opt["rho_film"], base_opt["rho_wall"])
    hz = {}
    for sc, an in (("ref", "a_ref"), ("bag", "a_bag")):
        a = d(an)
        tau, fh, _ = m.turbidity(phi, a, base_opt["n_cell"], base_opt["f_morph"])
        for t in (40.0, 100.0, 200.0):
            hz[(sc, t)] = m.haze_from_tau(tau, t, fh)[1]
    out["P_haze10_ref_t100"] = float((hz[("ref", 100.0)] <= 0.10).mean())
    out["P_haze10_bag_t100"] = float((hz[("bag", 100.0)] <= 0.10).mean())
    out["P_haze10_bag_t200"] = float((hz[("bag", 200.0)] <= 0.10).mean())
    out["median_haze40_ref_pct"] = 100 * float(np.median(hz[("ref", 40.0)]))
    out["calibration_in_band_ref40"] = float(((hz[("ref", 40.0)] >= 0.049) & (hz[("ref", 40.0)] <= 0.117)).mean())
    # wet mechanics
    mm = {nm: d(nm) for nm in ("E_cnf", "E_chi", "psi", "kappa_cnf", "kappa_chi", "xi_max", "w_star", "kappa_chi_acid", "xi_acid")}
    ba = {nm: mm[nm] for nm in ("E_cnf", "E_chi", "psi", "kappa_cnf", "kappa_chi", "xi_max", "w_star")}
    e0 = m.E_wet(0.0, **ba)
    en = m.E_wet(0.2, **ba)
    ea = m.E_wet(0.2, **ba, acid=True, kappa_chi_acid=mm["kappa_chi_acid"], xi_acid=mm["xi_acid"])
    e0a = m.E_wet(0.0, **ba, acid=True, kappa_chi_acid=mm["kappa_chi_acid"], xi_acid=mm["xi_acid"])
    out["P_helps_neutral"] = float((en > e0).mean())
    out["P_helps_acid"] = float((ea > e0a).mean())
    out["median_E_neutral_w20_GPa"] = float(np.median(en))
    out["median_E_acid_w20_GPa"] = float(np.median(ea))
    out["median_gain_neutral_GPa"] = float(np.median(en - e0))
    out["median_gain_acid_GPa"] = float(np.median(ea - e0a))
    out["P_E_ge_1_neutral"] = float((en >= 1.0).mean())
    out["P_E_ge_1_acid"] = float((ea >= 1.0).mean())
    # forming
    ff = {nm: d(nm) for nm in ("eps_f_dry", "d_eps_wet", "r_void", "eps_wrinkle")}
    ec = m.eps_crit(ff["eps_f_dry"], ff["d_eps_wet"], ff["r_void"], 1.0)
    for gname, (d_b, d_t, h) in m.GEOMETRY.items():
        out["P_window_%s" % gname.split()[0]] = float(((ec + ff["eps_wrinkle"]) >= m.strain_budget(d_b, d_t, h)).mean())
    lo_, hi_ = {nm: m.scheme_range(nm, scheme) for nm in ff}, None
    best = min(1.0, lo_["r_void"][1]) * (lo_["eps_f_dry"][1] + lo_["d_eps_wet"][1]) + lo_["eps_wrinkle"][1]
    out["best_case_total_tolerance_saturated"] = best
    out["cup_possible_in_range"] = bool(best >= m.strain_budget(*m.GEOMETRY["cup"]))
    # joint pass, reference design, neutral liquid
    for sc in ("ref", "bag"):
        pass_opt = hz[(sc, 100.0)] <= 0.10
        for gname in ("tray (lid-like)", "bowl", "cup"):
            d_b, d_t, h = m.GEOMETRY[gname]
            pf = (ec + ff["eps_wrinkle"]) >= m.strain_budget(d_b, d_t, h)
            out["P_all_%s_%s" % (sc, gname.split()[0])] = float((pass_opt & (en >= 1.0) & pf).mean())
    return out


PRI = {}
for k, sch in enumerate(m.PRIOR_SCHEMES):
    PRI[sch] = panel(sch, k)
R["I_prior_robustness"] = {
    "schemes": list(m.PRIOR_SCHEMES), "panels": PRI,
    "widened_ranges": {nm: list(m.scheme_range(nm, "widened")) for nm in ("kappa_cnf", "xi_max", "r_void", "eps_wrinkle", "n_cell", "f_morph")},
    "narrowed_ranges": {nm: list(m.scheme_range(nm, "narrowed")) for nm in ("kappa_cnf", "xi_max", "r_void", "eps_wrinkle", "n_cell", "f_morph")},
    "claims": {
        "tray_gt_bowl_gt_cup_everywhere": all(PRI[s_]["P_window_tray"] > PRI[s_]["P_window_bowl"] >= PRI[s_]["P_window_cup"] for s_ in PRI),
        "cup_window_zero_in_schemes": [s_ for s_ in PRI if PRI[s_]["P_window_cup"] == 0.0],
        "cup_window_nonzero_in_schemes": [s_ for s_ in PRI if PRI[s_]["P_window_cup"] > 0.0],
        "wood_pulp_beats_bagasse_optically_everywhere": all(PRI[s_]["P_haze10_ref_t100"] > PRI[s_]["P_haze10_bag_t100"] for s_ in PRI),
        "chitosan_helps_more_in_neutral_than_acid_everywhere": all(PRI[s_]["P_helps_neutral"] > PRI[s_]["P_helps_acid"] for s_ in PRI),
        "acid_median_gain_below_neutral_everywhere": all(PRI[s_]["median_gain_acid_GPa"] < PRI[s_]["median_gain_neutral_GPa"] for s_ in PRI)}}

# ===================================================================== J. thickness couples optics and stiffness
# A rigid wall is judged by flexural rigidity, proportional to E t^3. Anchoring the reference
# requirement (1 GPa at 100 um) gives the thinnest wall for a sample's wet modulus,
# t_min = 100 (1 GPa / E)^(1/3), and that thickness sets the haze the optics must meet.
J = {}
sj = {sc: structure(sc, N, np.random.default_rng(SEED + 70 + i)) for i, sc in enumerate(("ref", "bag"))}
rj = np.random.default_rng(SEED + 72)
mj = {k_: m.draw(k_, N, rj) for k_ in ("E_cnf", "E_chi", "psi", "kappa_cnf", "kappa_chi", "xi_max", "w_star", "kappa_chi_acid", "xi_acid")}
bj = {k_: mj[k_] for k_ in ("E_cnf", "E_chi", "psi", "kappa_cnf", "kappa_chi", "xi_max", "w_star")}
for liquid in ("neutral", "acid"):
    ew = m.E_wet(REF["w"], **bj, acid=(liquid == "acid"), kappa_chi_acid=mj["kappa_chi_acid"], xi_acid=mj["xi_acid"])
    tmin = m.thickness_for_rigidity(np.maximum(ew, 1e-6))
    row = {"t_min_um_q5_25_50_75_95": q(np.minimum(tmin, 1e4)), "E_median_GPa": float(np.median(ew))}
    for sc in ("ref", "bag"):
        _, _, hz_t = optical(sj[sc], tmin)
        fixed100 = (optical(sj[sc], REF["t"])[2] <= REF["haze"]) & (ew >= REF["e_req"])
        row["P_coupled_window_%s" % sc] = float((hz_t <= REF["haze"]).mean())
        row["P_fixed100_joint_%s" % sc] = float(fixed100.mean())
        row["P_t_min_le_200um_%s" % sc] = float((tmin <= 200.0).mean())
    J["E_" + liquid] = row
# deterministic boundary for the figure: largest a at each thickness (5 % voids, 10 % haze)
tg = np.linspace(20, 300, 29)
J["a_max_curve_phi05_haze10"] = {"t_um": [float(x) for x in tg],
                                 "a_max_nm": [float(m.a_max_nm(float(x), 0.10, 0.05)) for x in tg]}
J["a_max_curve_phi05_haze5"] = {"t_um": [float(x) for x in tg],
                                "a_max_nm": [float(m.a_max_nm(float(x), 0.05, 0.05)) for x in tg]}
medE = {"neutral": float(np.median(m.E_wet(REF["w"], **bj))),
        "acid": float(np.median(m.E_wet(REF["w"], **bj, acid=True, kappa_chi_acid=mj["kappa_chi_acid"], xi_acid=mj["xi_acid"])))}
J["t_min_at_median_E_um"] = {k_: float(m.thickness_for_rigidity(v)) for k_, v in medE.items()}
J["a_max_at_t_min_phi05_haze10_nm"] = {k_: float(m.a_max_nm(float(m.thickness_for_rigidity(v)), 0.10, 0.05)) for k_, v in medE.items()}
J["anchor"] = {"E_GPa": 1.0, "t_um": 100.0, "note": "assumed equal-rigidity anchor; only the t^-3 scaling is physics"}
R["J_thickness_coupling"] = J

# ===================================================================== K. wax layer, bounded (H3 provisional)
Kx = {}
rk = np.random.default_rng(SEED + 80)
tw = m.draw_ext("t_wax", N, rk)
nw = m.draw_ext("n_wax", N, rk)
sw = m.draw_ext("sigma_wax", N, rk)
dnw = m.draw_ext("dn_wax", N, rk)
pw = m.draw_ext("phi_wax", N, rk)
aw = m.draw_ext("a_wax", N, rk)
ew_ = m.draw_ext("eps_wax", N, rk)
fsw = m.draw_ext("f_surf", N, rk)
# paired film samples at the reference design, wood-pulp scale, bulk only
sk = structure("ref", N, np.random.default_rng(SEED + 81))
tau_f, fh_f, _ = m.turbidity(sk["phi"], sk["a"], sk["nc"], sk["fm"])
# wax crystallite scattering: Delta eps = (n+dn)^2 - n^2
de = (nw + dnw) ** 2 - nw ** 2
gw, fhw, _ = m.angular_split(aw, nw)
tau_w = m.K_DERIVED * pw * (1 - pw) * de ** 2 * (aw * 1e-9) ** 3 / m.LAMBDA0 ** 4 * gw
s_w = m.surface_scatter_fraction(sw, nw, fsw)
for t in (100.0, 200.0):
    h0 = m.haze_composite(tau_f, fh_f, t, 0.0)
    h1 = m.haze_composite(tau_f, fh_f, t, 0.0, s_out=s_w, tau_c=tau_w * tw / t, f_haze_c=fhw)
    h1s = m.haze_composite(tau_f, fh_f, t, 0.0, s_out=s_w)                     # surface of the wax only
    h1b = m.haze_composite(tau_f, fh_f, t, 0.0, tau_c=tau_w * tw / t, f_haze_c=fhw)   # crystallites only
    dlt = h1 - h0
    Kx["optical_t%d" % t] = {
        "added_haze_points_q5_25_50_75_95": q(100 * dlt),
        "P_added_gt_1pt": float((dlt > 0.01).mean()), "P_added_gt_2pt": float((dlt > 0.02).mean()),
        "P_added_gt_5pt": float((dlt > 0.05).mean()),
        "median_added_points_surface_only": 100 * float(np.median(h1s - h0)),
        "median_added_points_crystallites_only": 100 * float(np.median(h1b - h0)),
        "tau_w_t_median": float(np.median(tau_w * tw * 1e-6))}
Kx["optical_spearman_added_haze_t100"] = {
    "crystallite size a_wax": m.spearman(aw, m.haze_composite(tau_f, fh_f, 100.0, 0.0, s_out=s_w, tau_c=tau_w * tw / 100.0, f_haze_c=fhw) - m.haze_composite(tau_f, fh_f, 100.0, 0.0)),
    "crystallite fraction phi_wax": m.spearman(pw, m.haze_composite(tau_f, fh_f, 100.0, 0.0, s_out=s_w, tau_c=tau_w * tw / 100.0, f_haze_c=fhw) - m.haze_composite(tau_f, fh_f, 100.0, 0.0)),
    "index contrast dn_wax": m.spearman(dnw, m.haze_composite(tau_f, fh_f, 100.0, 0.0, s_out=s_w, tau_c=tau_w * tw / 100.0, f_haze_c=fhw) - m.haze_composite(tau_f, fh_f, 100.0, 0.0)),
    "layer thickness t_wax": m.spearman(tw, m.haze_composite(tau_f, fh_f, 100.0, 0.0, s_out=s_w, tau_c=tau_w * tw / 100.0, f_haze_c=fhw) - m.haze_composite(tau_f, fh_f, 100.0, 0.0)),
    "wax roughness sigma_wax": m.spearman(sw, m.haze_composite(tau_f, fh_f, 100.0, 0.0, s_out=s_w, tau_c=tau_w * tw / 100.0, f_haze_c=fhw) - m.haze_composite(tau_f, fh_f, 100.0, 0.0))}
# forming with a coating applied before forming: containment is lost where the wax cracks
ecw = m.eps_crit(fm_["eps_f_dry"], fm_["d_eps_wet"], fm_["r_void"], 1.0)
for gname, (d_b, d_t, h) in m.GEOMETRY.items():
    b = m.strain_budget(d_b, d_t, h)
    Kx["forming_%s" % gname.split()[0]] = {
        "P_window_uncoated": float(((ecw + fm_["eps_wrinkle"]) >= b).mean()),
        "P_window_coated_before_forming": float(((np.minimum(ecw, ew_) + fm_["eps_wrinkle"]) >= b).mean())}
Kx["note"] = "liquid containment and the moisture barrier are not modelled; H3 stays untested"
R["K_wax_bounded"] = Kx

# ====================================================================== L. what the cup would need
cup_b = m.strain_budget(*m.GEOMETRY["cup"])
bowl_b = m.strain_budget(*m.GEOMETRY["bowl"])
lo_ef, hi_ef = m.PARAMS["eps_f_dry"][:2]
lo_dw, hi_dw = m.PARAMS["d_eps_wet"][:2]
hi_rv = min(1.0, m.PARAMS["r_void"][1])
hi_wr = m.PARAMS["eps_wrinkle"][1]
best_tens = hi_rv * (hi_ef + hi_dw)
med_tens = float(np.median(m.eps_crit(fm_["eps_f_dry"], fm_["d_eps_wet"], fm_["r_void"], 1.0)))
Lc = {"cup_budget": cup_b, "bowl_budget": bowl_b, "best_case_tensile_saturated": best_tens,
      "median_tensile_saturated": med_tens,
      "eps_wrinkle_needed_cup_at_best_tensile": cup_b - best_tens,
      "LDR_max_needed_cup_at_best_tensile": math.exp(cup_b - best_tens),
      "eps_wrinkle_needed_cup_at_median_tensile": cup_b - med_tens,
      "LDR_max_needed_cup_at_median_tensile": math.exp(cup_b - med_tens),
      "eps_wrinkle_needed_bowl_at_best_tensile": bowl_b - best_tens,
      "eps_wrinkle_assumed_upper": hi_wr, "LDR_max_assumed_upper": math.exp(hi_wr),
      "LDR_min_for_cup_if_tolerances_at_best_case": math.exp(cup_b - best_tens)}
R["L_cup_requirement"] = Lc


io_path = os.path.join(HERE, "results.json")
with open(io_path, "w", encoding="utf-8") as f:
    json.dump(R, f, indent=1)
print("wrote", io_path)
