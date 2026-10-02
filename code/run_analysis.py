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

io_path = os.path.join(HERE, "results.json")
with open(io_path, "w", encoding="utf-8") as f:
    json.dump(R, f, indent=1)
print("wrote", io_path)
