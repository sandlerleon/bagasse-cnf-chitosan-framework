# -*- coding: utf-8 -*-
"""Figures for the manuscript. Every plotted quantity comes from tncc_model.py or
results.json; nothing is drawn by hand except the process-chain schematic (Fig. 1).

    python make_figures.py      ->  ../figures/Figure1..5 (.png and .tif, 600 dpi)
"""
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Rectangle

import tncc_model as m

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "figures")
os.makedirs(OUT, exist_ok=True)
R = json.load(open(os.path.join(HERE, "results.json")))

BLUE, ORANGE, RED, GREEN, GREY = "#1f6fb2", "#e07b1a", "#c0392b", "#2e8b57", "#6b7280"
LIGHT = {"b": "#d6e6f4", "o": "#fbe3cc", "r": "#f6d5d1", "g": "#d9efe1"}
W = 6.85                                    # inches: Springer double-column width (174 mm)

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5, "axes.titlesize": 8.5,
                     "axes.labelsize": 8, "axes.spines.top": False, "axes.spines.right": False,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 6.8,
                     "axes.linewidth": 0.7, "lines.linewidth": 1.3})


def save(fig, stem):
    png = os.path.join(OUT, stem + ".png")
    fig.savefig(png, dpi=600, bbox_inches="tight", facecolor="white")
    try:
        fig.savefig(os.path.join(OUT, stem + ".tif"), dpi=600, bbox_inches="tight",
                    facecolor="white", pil_kwargs={"compression": "tiff_lzw", "dpi": (600, 600)})
    except Exception as e:
        print("   (tif skipped: %s)" % e)
    plt.close(fig)
    print("wrote", png)


def panel(ax, tag):
    ax.text(-0.13, 1.10, tag, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom", ha="left")


# ====================================================================== Fig 1: chain
fig, ax = plt.subplots(figsize=(W, 3.3))
ax.set_xlim(0, 100)
ax.set_ylim(0, 54)
ax.axis("off")
top = [("Sugarcane\nbagasse", GREY), ("Cellulose extraction\nand fibrillation", BLUE),
       ("Cellulose\nnanofibrils", BLUE), ("Densification", BLUE), ("Transparent\nCNF network", BLUE)]
bot = [("Transparent rigid\npackage", GREEN), ("Thermoforming", RED),
       ("Thin hydrophobic\nbarrier", ORANGE), ("Chitosan\nincorporation", ORANGE)]
bw, bh, gap, x0 = 17.4, 9.5, 2.9, 0.9
xs = [x0 + i * (bw + gap) for i in range(5)]
ytop, ybot = 41.0, 20.0
FS = 6.4


def box(x, y, txt, c):
    ax.add_patch(FancyBboxPatch((x, y), bw, bh, boxstyle="round,pad=0.2,rounding_size=0.8", fc="white", ec=c, lw=1.7))
    ax.text(x + bw / 2, y + bh / 2, txt, ha="center", va="center", fontsize=FS)


for (txt, c), x in zip(top, xs):
    box(x, ytop, txt, c)
for i in range(4):
    ax.annotate("", xy=(xs[i + 1] - 0.15, ytop + bh / 2), xytext=(xs[i] + bw + 0.15, ytop + bh / 2),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=0.9, shrinkA=0, shrinkB=0))
bx = [xs[1], xs[2], xs[3], xs[4]]
for (txt, c), x in zip(bot, bx):
    box(x, ybot, txt, c)
for i in range(3):
    ax.annotate("", xy=(bx[i] + bw + 0.15, ybot + bh / 2), xytext=(bx[i + 1] - 0.15, ybot + bh / 2),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=0.9, shrinkA=0, shrinkB=0))
ax.annotate("", xy=(xs[4] + bw / 2, ybot + bh + 0.3), xytext=(xs[4] + bw / 2, ytop - 0.3),
            arrowprops=dict(arrowstyle="-|>", color="black", lw=0.9, shrinkA=0, shrinkB=0))
# the three consistency tests, each in clear space beside the stage it gates
xa = xs[4] + bw / 2 - 1.6
ax.text(xa, 37.2, "TEST 1  optical", ha="right", va="center", fontsize=6.9, fontweight="bold", color=BLUE)
ax.text(xa, 33.4, "bulk scattering over the wall\nthickness: haze budget", ha="right", va="center", fontsize=6.0, color=BLUE)
xm = (bx[2] + bx[3] + bw) / 2
ax.text(xm, 14.6, "TEST 2  wet mechanical", ha="center", va="center", fontsize=6.9, fontweight="bold", color=ORANGE)
ax.text(xm, 10.2, "does chitosan raise wet stiffness,\nand in an acidic liquid?", ha="center", va="center", fontsize=6.0, color=ORANGE)
xf = bx[1] + bw / 2
ax.text(xf, 14.6, "TEST 3  forming", ha="center", va="center", fontsize=6.9, fontweight="bold", color=RED)
ax.text(xf, 10.2, "strain budget vs\ntolerated strain", ha="center", va="center", fontsize=6.0, color=RED)
ax.text(50, 1.2, "Conceptual integration of separately published elements, not an existing material.\n"
        "Each coloured test is a consistency screen, not a performance prediction (Sections 5–7).",
        ha="center", va="bottom", fontsize=6.0, color="#444", style="italic")
save(fig, "Figure1")


# ====================================================================== Fig 2: optical
fig = plt.figure(figsize=(W, 3.05))
gs = fig.add_gridspec(1, 2, width_ratios=[1.05, 1], wspace=0.30)
ax = fig.add_subplot(gs[0])
phi = np.linspace(0.002, 0.20, 160)
a = np.exp(np.linspace(math.log(2), math.log(100), 160))
PHI, A = np.meshgrid(phi, a)
tau, fh, _ = m.turbidity(PHI, A, 1.55)
_, H100 = m.haze_from_tau(tau, 100.0, fh)
_, H200 = m.haze_from_tau(tau, 200.0, fh)
ax.contourf(100 * PHI, A, 100 * H100, levels=[0, 5, 10, 25, 50, 100.1],
            colors=["#d9efe1", "#eaf4d3", "#fdf1c9", "#fbd9b4", "#f4b9a8"], alpha=0.95)
cs = ax.contour(100 * PHI, A, 100 * H100, levels=[5, 10, 25, 50], colors="#333", linewidths=0.8)
ax.clabel(cs, fmt="%d%%", fontsize=6.5, inline=True)
cs2 = ax.contour(100 * PHI, A, 100 * H200, levels=[5], colors=RED, linewidths=1.1, linestyles="--")
ax.clabel(cs2, fmt="200 µm, 5%%", fontsize=6.2, inline=True, manual=[(8.0, 5.6)])
ax.set_yscale("log")
ax.set_ylim(2, 100)
ax.set_xlim(0, 20)
# literature boxes
ax.add_patch(Rectangle((0.15, 3), 18.85, 12, fill=False, ec=BLUE, lw=1.6))
ax.text(18.8, 2.25, "wood-pulp fibril scale (Hsieh 2017; Fukuzumi 2009)", color=BLUE, fontsize=6.0, ha="right", va="bottom")
ax.add_patch(Rectangle((0.15, 15.5), 18.85, 64.5, fill=False, ec=ORANGE, lw=1.6, ls=(0, (4, 2))))
ax.text(18.8, 58, "bagasse range extends\nupward (Carneiro Pessan 2023)", color=ORANGE, fontsize=6.0, ha="right", va="center")
ax.set_xlabel("Void volume fraction  φ  (%)")
ax.set_ylabel("Correlation length  a  (nm)")
ax.set_title("Haze of a 100 µm wall (bulk scattering)", loc="left", pad=9)
panel(ax, "a")

ax = fig.add_subplot(gs[1])
tt = np.linspace(20, 300, 140)
for (phi_, a_, c, lab) in ((0.02, 8.0, GREEN, "φ = 2%, a = 8 nm"), (0.05, 10.0, BLUE, "φ = 5%, a = 10 nm"),
                           (0.05, 15.0, RED, "φ = 5%, a = 15 nm")):
    tau_, fh_, _ = m.turbidity(phi_, a_, 1.55)
    _, hh = m.haze_from_tau(tau_, tt, fh_)
    ax.plot(tt, 100 * hh, color=c, label=lab)
ax.axhspan(4.9, 11.7, xmin=0, xmax=1, color=GREY, alpha=0.18, lw=0)
ax.text(298, 12.0, "grey band: observed 40 µm haze held fixed", fontsize=6.0, color="#444", ha="right", va="bottom")
ax.errorbar([40], [8.3], yerr=[[3.4], [3.4]], fmt="o", color="black", ms=4, capsize=3, zorder=5)
ax.annotate("Hsieh 2017, clear\nnanopaper (40 µm)", xy=(40, 11.9), xytext=(24, 31), fontsize=6.2, ha="left",
            arrowprops=dict(arrowstyle="-", color="black", lw=0.6, shrinkA=2, shrinkB=2))
for hz, ls in ((5, ":"), (10, ":")):
    ax.axhline(hz, color="black", lw=0.6, ls=ls)
ax.set_xlim(20, 300)
ax.set_ylim(0, 60)
ax.set_xlabel("Wall thickness  t  (µm)")
ax.set_ylabel("Haze  (%)")
ax.set_title("Thickness scaling: the unmeasured bracket", loc="left", pad=9)
ax.legend(frameon=False, loc="upper left")
panel(ax, "b")
save(fig, "Figure2")


# ================================================================ Fig 3: wet mechanics
medp = R["G_additions"]["median_parameters"]
base = {k: medp[k] for k in ("E_cnf", "E_chi", "psi", "kappa_cnf", "kappa_chi", "xi_max", "w_star")}
fig = plt.figure(figsize=(W, 2.85))
gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 1, 1], wspace=0.40)

# (a) Monte Carlo bands
rng = np.random.default_rng(20261002 + 99)
N = 40_000
mech = {k: m.draw(k, N, rng) for k in ("E_cnf", "E_chi", "psi", "kappa_cnf", "kappa_chi", "xi_max", "w_star",
                                       "kappa_chi_acid", "xi_acid")}
ba = {k: mech[k] for k in ("E_cnf", "E_chi", "psi", "kappa_cnf", "kappa_chi", "xi_max", "w_star")}
wg = np.linspace(0, 0.4, 41)
ax = fig.add_subplot(gs[0])
for liquid, c in (("neutral", BLUE), ("acid", ORANGE)):
    acid = liquid == "acid"
    E = np.array([m.E_wet(w, **ba, acid=acid, kappa_chi_acid=mech["kappa_chi_acid"], xi_acid=mech["xi_acid"]) for w in wg])
    lo, md, hi = np.percentile(E, [5, 50, 95], axis=1)
    ax.fill_between(100 * wg, lo, hi, color=c, alpha=0.18, lw=0)
    ax.plot(100 * wg, md, color=c, label="%s liquid" % liquid)
ax.axhline(1.0, color="black", lw=0.7, ls=":")
ax.text(39, 1.07, "1 GPa requirement (assumed)", fontsize=6.2, ha="right")
ax.plot([20], [4.0], marker="*", ms=9, color="black", zorder=6, ls="none")
ax.annotate("Toivonen 2015: 4 GPa,\nwet, 20% chitosan", xy=(20, 4.0), xytext=(2.0, 6.0), fontsize=6.2,
            arrowprops=dict(arrowstyle="-", color="black", lw=0.6, shrinkA=2, shrinkB=3))
ax.set_xlim(0, 40)
ax.set_ylim(0, 8)
ax.set_xlabel("Chitosan mass fraction  w  (%)")
ax.set_ylabel("Water-saturated stiffness  (GPa)")
ax.set_title("Screen output", loc="left")
ax.legend(frameon=False, loc="upper right", fontsize=6.3)
panel(ax, "a")

# (b, c) chitosan x hydration maps at median parameters
wgrid = np.linspace(0, 0.5, 101)
hgrid = np.linspace(0, 1, 81)
WW, HH = np.meshgrid(wgrid, hgrid)
vmin, vmax = 0.3, 9.0
for i, (liquid, tag) in enumerate((("neutral", "b"), ("acid", "c"))):
    ax = fig.add_subplot(gs[1 + i])
    acid = liquid == "acid"
    Z = m.E_hyd(WW, HH, **base, acid=acid, kappa_chi_acid=medp["kappa_chi_acid"], xi_acid=medp["xi_acid"])
    cf = ax.contourf(100 * WW, HH, np.clip(Z, vmin, vmax), levels=np.geomspace(vmin, vmax, 19), cmap="YlGnBu", norm=matplotlib.colors.LogNorm(vmin, vmax))
    cc = ax.contour(100 * WW, HH, Z, levels=[0.5, 1.0, 2.0, 4.0], colors=["#555", "black", "#555", "#555"], linewidths=[0.8, 1.6, 0.8, 0.8])
    ax.clabel(cc, fmt={0.5: "0.5", 1.0: "1 GPa", 2.0: "2", 4.0: "4"}, fontsize=6.3, inline=True)
    ax.axvline(20, color=ORANGE, lw=0.9, ls="--")
    ax.plot([20], [1.0], marker="*", ms=8, color="black", mfc="white" if acid else "black", zorder=6)
    ax.set_xlabel("Chitosan fraction  w  (%)")
    if i == 0:
        ax.set_ylabel("Hydration (0 ambient, 1 saturated)")
    else:
        ax.set_yticklabels([])
    ax.set_title("Neutral liquid" if not acid else "Acidic liquid", loc="left")
    panel(ax, tag)
cax = fig.add_axes([0.915, 0.18, 0.012, 0.62])
cb = fig.colorbar(cf, cax=cax)
cb.set_label("Stiffness (GPa), median parameters, log scale", fontsize=6.4)
cb.set_ticks([0.3, 0.5, 1, 2, 4, 9])
cb.set_ticklabels(["0.3", "0.5", "1", "2", "4", "9"])
cb.ax.tick_params(labelsize=6.5)
save(fig, "Figure3")


# ================================================================== Fig 4: forming
rf = np.random.default_rng(20261002 + 30)
fm = {k: m.draw(k, 200_000, rf) for k in ("eps_f_dry", "d_eps_wet", "r_void", "eps_wrinkle")}
fig = plt.figure(figsize=(W, 3.05))
gs = fig.add_gridspec(1, 2, width_ratios=[1.1, 1], wspace=0.28)
ax = fig.add_subplot(gs[0])
ldr = np.linspace(1.0, 2.2, 300)
cols = {"tray (lid-like)": GREEN, "bowl": ORANGE, "cup": RED}
for g, (d_b, d_t, h) in m.GEOMETRY.items():
    b = m.strain_budget(d_b, d_t, h)
    eps = np.maximum(0.0, b - np.log(ldr))
    ax.plot(ldr, 100 * eps, color=cols[g], lw=1.9, label="%s, budget %.2f" % (g.split(" (")[0], b), zorder=4)
ec_med = {hy: float(np.percentile(m.eps_crit(fm["eps_f_dry"], fm["d_eps_wet"], fm["r_void"], hy), 50)) for hy in (0.0, 1.0)}
ew_med = float(np.percentile(fm["eps_wrinkle"], 50))
env = R["E_envelope"]
best_tot = env["forming_tolerance_h10"]["max"]
ec_best = best_tot - 0.50                       # eps_wrinkle upper bound of the registry
boxes = [(ec_med[0], ew_med, "#9aa5b1", "ambient, median", "-"), (ec_med[1], ew_med, BLUE, "wet, median", "-"),
         (ec_best, 0.50, GREEN, "best case, all ranges", "--")]
for ec, ew, c, lab, ls in boxes:
    ax.add_patch(Rectangle((1.0, 0), math.exp(ew) - 1.0, 100 * ec,
                           fc=matplotlib.colors.to_rgba(c, 0.20) if ls == "-" else "none",
                           ec=c, lw=1.5, ls=ls, zorder=2))
    ytxt = 30 if ls == "--" else 100 * ec - 0.5
    ax.text(math.exp(ew) + 0.012, ytxt, lab, fontsize=6.2, color=c if c != "#9aa5b1" else "#666",
            va="center" if ls == "--" else "top", ha="left")
ax.set_xlim(1.0, 2.2)
ax.set_ylim(0, 80)
ax.set_xlabel("Limiting draw ratio  LDR = D\u2080 / d_b")
ax.set_ylabel("Mean tensile strain at the wall  (%)")
ax.set_title("Strain budget versus tolerated strain", loc="left", pad=9)
ax.legend(frameon=False, loc="upper right", fontsize=6.4)
panel(ax, "a")

ax = fig.add_subplot(gs[1])
tol = np.linspace(0, 1.25, 200)
ax.plot(tol, m.s_max(tol), color="black", lw=1.5)
for g, (d_b, d_t, h) in m.GEOMETRY.items():
    s_eq = (math.exp(2 * m.strain_budget(d_b, d_t, h)) - 1) / 4
    ax.axhline(s_eq, color=cols[g], lw=1.0, ls="--")
    right = g.startswith("tray")
    ax.text(1.24 if right else 0.015, s_eq + 0.05, "%s: h/d \u2248 %.2f" % (g.split(" (")[0], s_eq), color=cols[g],
            fontsize=6.4, ha="right" if right else "left", va="bottom")
tol_pts = [("ambient, median", float(np.median(m.eps_crit(fm["eps_f_dry"], fm["d_eps_wet"], fm["r_void"], 0.0) + fm["eps_wrinkle"])), "#9aa5b1"),
           ("wet, median", float(np.median(m.eps_crit(fm["eps_f_dry"], fm["d_eps_wet"], fm["r_void"], 1.0) + fm["eps_wrinkle"])), BLUE),
           ("best case, all ranges", best_tot, GREEN)]
for lab, x, c in tol_pts:
    ax.plot([x], [float(m.s_max(x))], marker="o", color=c, ms=6, zorder=5, ls="none", label="%s (%.2f)" % (lab, x))
ax.legend(frameon=False, loc="upper left", fontsize=6.3, title="tolerance", title_fontsize=6.4)
ax.set_xlim(0, 1.25)
ax.set_ylim(0, 3.0)
ax.set_xlabel("Total strain tolerance  \u03b5_crit + \u03b5_wrinkle")
ax.set_ylabel("Deepest formable cup, depth / base diameter")
ax.set_title("What a given tolerance can form", loc="left", pad=9)
panel(ax, "b")
save(fig, "Figure4")


# ============================================================= Fig 5: integration
fig = plt.figure(figsize=(W, 3.1))
gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 1], wspace=0.34)
ax = fig.add_subplot(gs[0])
J = R["C_monte_carlo"]["joint_reference_design"]
geoms = ["tray", "bowl", "cup"]
combos = [("ref|neutral", "wood-pulp scale, neutral", BLUE), ("ref|acid", "wood-pulp scale, acidic", "#7fb0da"),
          ("bag|neutral", "bagasse range, neutral", ORANGE), ("bag|acid", "bagasse range, acidic", "#f0b878")]
x0 = np.arange(len(geoms))
bw = 0.19
for i, (key, lab, c) in enumerate(combos):
    vals = [100 * J["%s|%s" % (key, g)]["P_all"] for g in geoms]
    ax.bar(x0 + (i - 1.5) * bw, vals, bw, color=c, label=lab, edgecolor="white", lw=0.5)
    for xx, v in zip(x0 + (i - 1.5) * bw, vals):
        ax.text(xx, v + 1.0, "%.0f" % v if v >= 0.5 else "0", ha="center", fontsize=6.0)
ax.set_xticks(x0)
ax.set_xticklabels(["tray (lid-like)\nbudget 0.26", "bowl\nbudget 0.67", "cup\nbudget 1.11"])
ax.set_ylabel("Share of sampled designs passing all three tests  (%)")
ax.set_ylim(0, 62)
ax.set_title("Joint outcome, reference design", loc="left")
ax.legend(frameon=False, loc="upper right")
panel(ax, "a")

ax = fig.add_subplot(gs[1])
S = R["D_spearman"]
rows = [("Optical", BLUE, "optical_reference_haze", {"correlation length a": "correlation length a", "film density": "film density",
                                                       "morphology factor": "morphology factor"}),
        ("Wet mechanical", ORANGE, "mechanical_neutral_Ewet", {"xi_max": "cross-linking gain", "E_cnf": "CNF modulus",
                                                                 "kappa_cnf": "plain-CNF wet retention"}),
        ("Forming (bowl)", RED, "forming_bowl_margin", {"eps_wrinkle": "wrinkle tolerance", "r_void": "void-onset ratio",
                                                         "d_eps_wet": "wet strain gain"})]
y, ylab, ycol = 0, [], []
for title, c, key, names in reversed(rows):
    d = S[key]
    items = sorted(((names[k], d[k]) for k in names), key=lambda kv: abs(kv[1]))
    for lab, v in items:
        ax.barh(y, v, color=c, height=0.7)
        ax.text(v + (0.03 if v >= 0 else -0.03), y, "%+.2f" % v, va="center", ha="left" if v >= 0 else "right", fontsize=6.2)
        ylab.append(lab)
        y += 1
    ax.text(-0.98, y - 0.5 - 1.0, title, color=c, fontsize=7.2, fontweight="bold", va="center")
    y += 0.7
ax.set_yticks([i for i in range(len(ylab) + 3) if False])
yy, k = 0, 0
ticks, labs = [], []
for title, c, key, names in reversed(rows):
    d = S[key]
    items = sorted(((names[kk], d[kk]) for kk in names), key=lambda kv: abs(kv[1]))
    for lab, v in items:
        ticks.append(yy); labs.append(lab); yy += 1
    yy += 0.7
ax.set_yticks(ticks)
ax.set_yticklabels(labs, fontsize=6.6)
ax.set_xlim(-1.0, 1.05)
ax.axvline(0, color="black", lw=0.7)
ax.set_xlabel("Spearman rank correlation with the output")
ax.set_title("Which unknown to measure first", loc="left", pad=9)
panel(ax, "b")
save(fig, "Figure5")
print("done")
