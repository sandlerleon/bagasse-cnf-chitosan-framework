# -*- coding: utf-8 -*-
"""Numerical tables underlying Figures 2-7, written as CSV to code/figure_data/.

Each table holds the plotted quantity exactly as the figure script computes it (same model
functions, same seeds where sampling is involved), so a reader can re-plot or check a figure
without running the plotting code.

    python export_figure_data.py
"""
import csv
import json
import math
import os

import numpy as np

import tncc_model as m

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figure_data")
os.makedirs(OUT, exist_ok=True)
R = json.load(open(os.path.join(HERE, "results.json")))
SEED = R["seed"]


def write(name, header, rows):
    path = os.path.join(OUT, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow([("%.6g" % v) if isinstance(v, float) else v for v in r])
    print("wrote", path, "(%d rows)" % len(rows))


# ---- Figure 2a: haze of a 100 um and 200 um wall on the (void fraction, correlation length) grid
phi = np.linspace(0.002, 0.20, 160)
a = np.exp(np.linspace(math.log(2), math.log(100), 160))
PHI, A = np.meshgrid(phi, a)
tau, fh, _ = m.turbidity(PHI, A, 1.55)
H100 = m.haze_from_tau(tau, 100.0, fh)[1]
H200 = m.haze_from_tau(tau, 200.0, fh)[1]
write("fig2a_haze_grid.csv", ["void_fraction", "correlation_length_nm", "haze_100um", "haze_200um"],
      [[float(PHI[i, j]), float(A[i, j]), float(H100[i, j]), float(H200[i, j])] for i in range(0, 160, 2) for j in range(0, 160, 2)])

# ---- Figure 2b: haze against thickness for three structures (bulk scattering)
tt = np.linspace(20, 300, 140)
rows = []
for phi_, a_ in ((0.02, 8.0), (0.05, 10.0), (0.05, 15.0)):
    tau_, fh_, _ = m.turbidity(phi_, a_, 1.55)
    hh = m.haze_from_tau(tau_, tt, fh_)[1]
    rows += [[phi_, a_, float(t), float(h)] for t, h in zip(tt, hh)]
write("fig2b_haze_vs_thickness.csv", ["void_fraction", "correlation_length_nm", "thickness_um", "haze"], rows)

# ---- Figure 3a: wet stiffness bands (40,000 samples, seed + 99)
rng = np.random.default_rng(SEED + 99)
N = 40_000
mech = {k: m.draw(k, N, rng) for k in ("E_cnf", "E_chi", "psi", "kappa_cnf", "kappa_chi", "xi_max", "w_star",
                                       "kappa_chi_acid", "xi_acid")}
ba = {k: mech[k] for k in ("E_cnf", "E_chi", "psi", "kappa_cnf", "kappa_chi", "xi_max", "w_star")}
rows = []
for liquid in ("neutral", "acid"):
    for w in np.linspace(0, 0.4, 41):
        E = m.E_wet(w, **ba, acid=(liquid == "acid"), kappa_chi_acid=mech["kappa_chi_acid"], xi_acid=mech["xi_acid"])
        lo, md, hi = np.percentile(E, [5, 50, 95])
        rows.append([liquid, float(w), float(lo), float(md), float(hi)])
write("fig3a_wet_stiffness_bands.csv", ["liquid", "chitosan_fraction", "E_q05_GPa", "E_median_GPa", "E_q95_GPa"], rows)

# ---- Figure 3b,c: chitosan x hydration maps at median parameters
medp = R["G_additions"]["median_parameters"]
base = {k: medp[k] for k in ("E_cnf", "E_chi", "psi", "kappa_cnf", "kappa_chi", "xi_max", "w_star")}
rows = []
for liquid in ("neutral", "acid"):
    for w in np.linspace(0, 0.5, 51):
        for h in np.linspace(0, 1, 41):
            z = m.E_hyd(w, h, **base, acid=(liquid == "acid"), kappa_chi_acid=medp["kappa_chi_acid"], xi_acid=medp["xi_acid"])
            rows.append([liquid, float(w), float(h), float(z)])
write("fig3bc_hydration_maps.csv", ["liquid", "chitosan_fraction", "hydration", "E_GPa"], rows)

# ---- Figure 4a: mean tensile strain at the wall against limiting draw ratio
ldr = np.linspace(1.0, 2.2, 121)
rows = []
for g, (d_b, d_t, h) in m.GEOMETRY.items():
    b = m.strain_budget(d_b, d_t, h)
    rows += [[g, float(b), float(x), float(max(0.0, b - math.log(x)))] for x in ldr]
write("fig4a_strain_vs_ldr.csv", ["geometry", "strain_budget", "LDR", "mean_tensile_strain"], rows)

# ---- Figure 4b: deepest formable straight cup against total tolerance
tol = np.linspace(0, 1.25, 126)
write("fig4b_cup_depth_vs_tolerance.csv", ["total_tolerance", "max_depth_over_base_diameter"],
      [[float(t), float(m.s_max(t))] for t in tol])

# ---- Figure 5a, 5b: joint pass shares and Spearman coefficients
J = R["C_monte_carlo"]["joint_reference_design"]
write("fig5a_joint_pass.csv", ["feedstock_range|liquid|geometry", "P_optical", "P_mechanical", "P_forming", "P_all"],
      [[k, v["P_optical"], v["P_mechanical"], v["P_forming"], v["P_all"]] for k, v in J.items()])
rows = []
for block, d in R["D_spearman"].items():
    rows += [[block, k, float(v)] for k, v in d.items()]
write("fig5b_spearman.csv", ["output", "input", "spearman_rho"], rows)

# ---- Figure 6a: haze CDF with added scattering; 6b: haze budget curves and minimum thickness
HV = R["H_optical_validation"]["cdf_t40_percentiles_1_to_99"]
write("fig6a_haze_cdf_40um.csv", ["percentile"] + list(HV), [[p] + [HV[k][i] for k in HV] for i, p in enumerate(range(1, 100))])
JT = R["J_thickness_coupling"]
write("fig6b_haze_budget_curves.csv", ["thickness_um", "a_max_nm_haze10_phi5", "a_max_nm_haze5_phi5"],
      [[t, x, y] for t, x, y in zip(JT["a_max_curve_phi05_haze10"]["t_um"], JT["a_max_curve_phi05_haze10"]["a_max_nm"],
                                     JT["a_max_curve_phi05_haze5"]["a_max_nm"])])
write("fig6b_minimum_thickness.csv", ["liquid", "t_min_q05", "t_min_q25", "t_min_q50", "t_min_q75", "t_min_q95"],
      [[liq] + JT["E_" + liq]["t_min_um_q5_25_50_75_95"] for liq in ("neutral", "acid")])

# ---- Figure 7: pass shares under each prior scheme
PR = R["I_prior_robustness"]
keys = list(PR["panels"]["base"])
write("fig7_prior_robustness.csv", ["scheme"] + keys, [[s] + [PR["panels"][s][k] for k in keys] for s in PR["schemes"]])
