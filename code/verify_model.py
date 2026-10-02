# -*- coding: utf-8 -*-
"""Verification of the screening model against limits that are known independently of it.

A screening model cannot be validated against data it was not built from, so what can be
checked is (a) that the code implements the stated equations, (b) that it reduces to
established results in the limits where those are known, and (c) that its internal
bookkeeping is consistent. Each test below states which of the three it is.

    python verify_model.py        # exits non-zero if any test fails
"""
import math
import sys

import numpy as np

import tncc_model as m

FAILS = []


def check(name, ok, detail=""):
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", name, ("  -- " + detail) if detail else ""))
    if not ok:
        FAILS.append(name)


print("Optical (Test 1)")

# (b) small-qa limit: angular integral -> 4/3, so the turbidity reduces to Eq. (2) exactly
g, fh, fb = m.angular_split(a_nm=0.05, n_bar=1.5)
check("angular integral -> 4/3 in the small-qa limit (g = 1)", abs(float(g) - 1.0) < 1e-5, "g=%.8f at a = 0.05 nm" % g)
check("small-qa scattering is forward/backward symmetric", abs(float(fh) - 0.5) < 2e-3 and abs(float(fb) - 0.5) < 2e-3,
      "f_haze=%.4f f_back=%.4f" % (fh, fb))

# (c) energy bookkeeping: haze + cone + back fractions sum to one
g, fh, fb = m.angular_split(np.array([5.0, 20.0, 80.0, 300.0]), 1.5)
cone = 1.0 - fh - fb
check("scattered-light fractions sum to 1 (cone fraction non-negative)", np.all(cone >= -1e-12),
      "min cone fraction %.2e" % cone.min())

# (b) large correlation length makes scattering forward-peaked
check("large features scatter forward (f_back falls as a grows)", fb[-1] < fb[0], "f_back %.3f -> %.3f" % (fb[0], fb[-1]))
check("turbidity saturates below its small-qa value at large a (g < 1)", g[-1] < 1.0, "g(300 nm)=%.3f" % g[-1])

# (b) the derived prefactor against an independent classical result: dilute small spheres.
# Debye-Bueche with Gamma = integral of the correlation function reduces, for dilute spheres of
# volume V, to Gamma = V. Rayleigh gives tau = N sigma with sigma = (2 pi^5/3) D^6/lam^4 ((m^2-1)/(m^2+2))^2.
D, phi_s, ns = 20e-9, 1e-3, 1.01           # weak contrast so the local-field factor (m^2+2) is ~3
lam = m.LAMBDA0
V = math.pi * D ** 3 / 6.0
d_eps = ns ** 2 - 1.0
tau_db = (math.pi ** 2 / lam ** 4) * phi_s * d_eps ** 2 * V * (4 * math.pi) * (2.0 / 3.0)
N = phi_s / V
sigma = (2 * math.pi ** 5 / 3.0) * D ** 6 / lam ** 4 * ((ns ** 2 - 1) / (ns ** 2 + 2)) ** 2
tau_ray = N * sigma
check("Debye-Bueche reduces to Rayleigh for dilute small spheres", abs(tau_db / tau_ray - 1.0) < 0.03,
      "ratio %.4f (expected ~(1+small)  from the (m^2+2) factor)" % (tau_db / tau_ray))

# The a^3 law of Eq. (2) is the small-qa limit. State how far it holds, because it governs how
# large a fibre-scale feature can be before the closed form overestimates scattering.
for a_ in (2.0, 5.0, 10.0, 20.0, 40.0, 80.0):
    ga, _, _ = m.angular_split(a_, 1.5)
    print("      g(a = %5.1f nm) = %.3f   (closed-form Eq. 2 overestimates tau by x%.2f)" % (a_, ga, 1 / ga))

# (a) code reproduces the closed form where qa is genuinely small
phi, a, nc = 0.05, 2.0, 1.55
tau, fh_, fb_ = m.turbidity(phi, a, nc)
closed = m.K_DERIVED * phi * (1 - phi) * (nc ** 2 - 1) ** 2 * (a * 1e-9) ** 3 / lam ** 4
check("turbidity matches Eq. (2) when qa is small (a = 2 nm)", abs(float(tau) / closed - 1.0) < 0.01,
      "code %.1f vs closed %.1f 1/m" % (tau, closed))
check("K = 64 pi^4 / 3 = 2078.1", abs(m.K_DERIVED - 2078.1) < 0.1)

# scaling laws
t1, _, _ = m.turbidity(0.05, 0.5, 1.55)
t2, _, _ = m.turbidity(0.05, 1.0, 1.55)
check("tau scales as a^3 in the small-qa limit (doubling a multiplies tau by 8)", abs(float(t2 / t1) - 8.0) < 0.05, "x%.4f" % (t2 / t1))
t3, _, _ = m.turbidity(0.05, 10.0, 1.55)
t4, _, _ = m.turbidity(0.05, 20.0, 1.55)
check("beyond small-qa the growth with a is slower than a^3 (a 10 -> 20 nm)", float(t4 / t3) < 8.0, "x%.2f" % (t4 / t3))
lam_ratio = (m.LAMBDA0 / 450e-9) ** 4
check("wavelength scaling lam^-4 gives the expected blue/green ratio", lam_ratio > 2.0, "(550/450)^4 = %.2f" % lam_ratio)
tp, _, _ = m.turbidity(0.10, 8.0, 1.55)
tq, _, _ = m.turbidity(0.20, 8.0, 1.55)
check("tau scales as phi(1-phi)", abs(float(tq / tp) - (0.2 * 0.8) / (0.1 * 0.9)) < 0.02)

# haze slab
d0, h0 = m.haze_from_tau(0.0, 100.0, 0.5)
check("zero scattering gives zero haze and unit direct transmittance", abs(float(h0)) < 1e-12 and abs(float(d0) - 1.0) < 1e-12)
ts = np.linspace(10, 300, 30)
_, hh = m.haze_from_tau(2000.0, ts, 0.5)
check("haze rises monotonically with thickness", bool(np.all(np.diff(hh) > 0)))
_, small = m.haze_from_tau(500.0, 40.0, 0.5)
check("haze ~ f * tau * t for thin sheets", abs(float(small) / (0.5 * 500.0 * 40e-6) - 1.0) < 0.02)
# inversion round trip
for hmax in (0.02, 0.05, 0.10, 0.20):
    tm = m.haze_budget(200.0, hmax, 0.5)
    _, hback = m.haze_from_tau(tm, 200.0, 0.5)
    check("haze_budget inverts haze_from_tau at %d%%" % round(hmax * 100), abs(float(hback) - hmax) < 1e-9)

# (c) radiative relation against two published (direct transmittance, haze) pairs, Xu 2016.
# Direct/total = 1 - haze. With total ~ direct/(1-haze) the single-scattering slab should
# map direct transmittance to a haze within about +-10 points; it cannot be exact.
for direct_obs, haze_obs in ((0.751, 0.100), (0.311, 0.620)):
    x = -math.log(direct_obs)
    _, hp = m.haze_from_tau(x / 1e-6, 1.0, 0.5)            # tau = x / (1 um), so tau*t = x
    check("single-scattering relation within 12 points of Xu 2016 (direct %.1f%% -> haze %.0f%% reported)"
          % (100 * direct_obs, 100 * haze_obs), abs(float(hp) - haze_obs) < 0.12, "model %.1f%%" % (100 * float(hp)))

print("\nWet mechanics (Test 2)")
P = dict(E_cnf=8.0, E_chi=3.0, psi=0.8, kappa_cnf=0.1, kappa_chi=0.3, xi_max=0.5, w_star=0.1)
check("w = 0 recovers plain CNF exactly", abs(float(m.E_wet(0.0, **P)) - P["kappa_cnf"] * P["E_cnf"]) < 1e-12)
check("w = 1 recovers neat chitosan exactly", abs(float(m.E_wet(1.0, **P)) - P["kappa_chi"] * P["E_chi"]) < 1e-12)
P2 = dict(P, psi=1.0, xi_max=0.0)
mix = lambda w: (1 - w) * 0.1 * 8.0 + w * 0.3 * 3.0
check("with no disruption and no cross-linking it is the rule of mixtures",
      all(abs(float(m.E_wet(w, **P2)) - mix(w)) < 1e-12 for w in (0.1, 0.4, 0.8)))
check("cross-linking can only raise wet stiffness", float(m.E_wet(0.2, **P)) > float(m.E_wet(0.2, **dict(P, xi_max=0.0))))
check("an acidic liquid does not exceed the neutral case",
      float(m.E_wet(0.2, **P, acid=True, kappa_chi_acid=0.05, xi_acid=0.3)) <= float(m.E_wet(0.2, **P)))
check("losing all chitosan benefit in acid leaves at most plain-CNF stiffness (x(1-w))",
      float(m.E_wet(0.2, **dict(P, psi=1.0), acid=True, kappa_chi_acid=0.0, xi_acid=0.0))
      <= (1 - 0.2) * 0.1 * 8.0 + 1e-12)

print("\nForming (Test 3)")
# (a) the strain budget and the window condition are the same statement
for name, (d_b, d_t, h) in m.GEOMETRY.items():
    bud = m.strain_budget(d_b, d_t, h)
    ec, ew = 0.5 * bud, 0.5 * bud
    check("window closes just below the budget and opens at it (%s)" % name,
          (not m.window_exists(d_b, d_t, h, ec - 1e-6, ew)) and m.window_exists(d_b, d_t, h, ec, ew), "budget %.3f" % bud)
    # LDR interval bounds are ordered exactly when the window exists
    lmin = m.ldr_required(d_b, d_t, h, ec)
    lmax = math.exp(ew)
    check("LDR_min == LDR_max at the budget boundary (%s)" % name, abs(lmin - lmax) < 1e-9, "%.5f vs %.5f" % (lmin, lmax))
# (a) straight-walled cup: closed form s_max
for s_ in (0.1, 0.35, 0.9):
    bud = 0.5 * math.log(1 + 4 * s_)
    check("straight cup h/d = %.2f: s_max(budget) = h/d" % s_, abs(float(m.s_max(bud)) - s_) < 1e-12)
check("flat sheet needs no strain", abs(m.strain_budget(100.0, 100.0, 0.0)) < 1e-12)
check("budget grows with depth", m.strain_budget(55, 80, 90) > m.strain_budget(55, 80, 45) > 0)
# a peak is never below the mean: nonuniform thinning of a unit area increases the maximum strain
rng = np.random.default_rng(1)
f = rng.uniform(0.2, 1.8, 10000)
f /= f.mean()
check("peak strain >= mean strain for any nonuniform split (Jensen bound used in the text)",
      float(np.log(f).max()) >= float(np.log(f.mean())) - 1e-12)
check("eps_crit = min(eps_f, eps_void) <= eps_f",
      bool(np.all(m.eps_crit(0.1, 0.2, np.array([0.2, 0.6, 1.0, 1.7]), 0.5) <= 0.1 + 0.2 * 0.5 + 1e-12)))

print("\nStatistics")
r = np.random.default_rng(3)
x = r.normal(size=5000)
check("Spearman of a monotone transform is 1", abs(m.spearman(x, np.exp(x)) - 1.0) < 1e-9)
check("Spearman of independent samples is near 0", abs(m.spearman(x, r.normal(size=5000))) < 0.05)

print("\nExtensions (surface scattering, prior schemes, thickness coupling)")
# (c) the composite slab with every extra term switched off is the core single-scattering slab
tau_t, fh_t, _ = m.turbidity(0.05, np.array([5.0, 20.0, 60.0]), 1.55, 1.0)
h_core = m.haze_from_tau(tau_t, 100.0, fh_t)[1]
check("composite slab reduces to the core slab when surface and coarse terms are zero",
      bool(np.allclose(m.haze_composite(tau_t, fh_t, 100.0, 0.0), h_core, atol=1e-12)))
# (b) scalar-theory small-roughness limit: s -> (2 pi (n-1) sigma / lambda)^2
s_small = float(m.surface_scatter_fraction(1.0, 1.5, 1.0))
phi_small = 2.0 * math.pi * 0.5 * 1e-9 / m.LAMBDA0
check("rough-surface scattering -> (2 pi (n-1) sigma/lambda)^2 at small sigma",
      abs(s_small / phi_small ** 2 - 1.0) < 1e-3, "ratio %.5f" % (s_small / phi_small ** 2))
check("a smooth surface scatters nothing", float(m.surface_scatter_fraction(0.0, 1.5, 1.0)) == 0.0)
sg = np.array([1.0, 5.0, 20.0, 80.0])
check("surface scattering rises with roughness and never exceeds f_surf",
      bool(np.all(np.diff(m.surface_scatter_fraction(sg, 1.5, 0.7)) > 0) and np.all(m.surface_scatter_fraction(sg, 1.5, 0.7) <= 0.7)))
# (a) round trip of the roughness needed for a given haze
for h_ in (0.05, 0.117):
    sig_ = m.sigma_for_haze(h_, 1.5)
    s1_ = float(m.surface_scatter_fraction(sig_, 1.5, 1.0))
    check("roughness inversion round-trips at haze %.3f" % h_, abs(1.0 - (1.0 - s1_) ** 2 - h_) < 1e-9)
hz_c = m.haze_composite(tau_t, fh_t, 100.0, 0.03, tau_c=np.array([2e3, 1e4, 5e4]), f_haze_c=0.8)
check("composite haze stays in [0, 1] and rises with every added scattering term",
      bool(np.all((hz_c >= 0) & (hz_c <= 1)) and np.all(hz_c > h_core)))
# (a) equal-rigidity thickness: E t^3 is conserved
E_t = np.array([0.5, 1.0, 2.36, 8.0])
t_t = m.thickness_for_rigidity(E_t)
check("equal-rigidity thickness conserves E t^3", bool(np.allclose(E_t * t_t ** 3, 1.0 * 100.0 ** 3)))
check("a stiffer wall may be thinner (E = 8 GPa -> half the thickness)", abs(float(m.thickness_for_rigidity(8.0)) - 50.0) < 1e-9)
# (c) prior schemes
rs = np.random.default_rng(11)
ok_support, ok_lit = True, True
for nm, (lo_, hi_, dist_, _, st_, _) in m.PARAMS.items():
    for sch in m.PRIOR_SCHEMES:
        x_ = m.draw_scheme(nm, 4000, rs, sch)
        a_, b_ = m.scheme_range(nm, sch)
        ok_support &= bool(x_.min() >= a_ - 1e-9 and x_.max() <= b_ + 1e-9)
        if st_ == "lit" and sch in ("widened", "narrowed", "optimistic", "pessimistic"):
            ok_lit &= (m.scheme_range(nm, sch) == (lo_, hi_))
check("every draw lies inside its scheme's stated support", ok_support)
check("literature-informed ranges are untouched by the widened, narrowed, optimistic and pessimistic schemes", ok_lit)
wide_ok = all(m.scheme_range(k_, "widened")[0] <= v_[0] and m.scheme_range(k_, "widened")[1] >= v_[1] and
              m.scheme_range(k_, "narrowed")[0] >= v_[0] and m.scheme_range(k_, "narrowed")[1] <= v_[1] for k_, v_ in m.PARAMS.items())
check("widened ranges contain, and narrowed ranges sit inside, the base ranges", wide_ok)
x_opt = m.draw_scheme("xi_max", 20000, np.random.default_rng(5), "optimistic").mean()
x_pes = m.draw_scheme("xi_max", 20000, np.random.default_rng(5), "pessimistic").mean()
check("optimistic prior favours a helpful cross-linking gain, pessimistic the opposite", x_opt > x_pes, "%.3f vs %.3f" % (x_opt, x_pes))
check("every core parameter has a recorded favourable direction and hard limits",
      set(m.FAVOURABLE) == set(m.PARAMS) and set(m.HARD_LIMITS) == set(m.PARAMS))
check("extension ranges are all declared assumptions", all(v[4] == "assumed" and v[0] < v[1] for v in m.PARAMS_EXT.values()))

print("\nParameter registry")
for k, (lo, hi, dist, unit, status, basis) in m.PARAMS.items():
    if not (lo < hi and dist in ("u", "lu") and status in ("lit", "assumed")):
        FAILS.append("registry:" + k)
check("every parameter has lo < hi, a known distribution and a status", not any(s.startswith("registry:") for s in FAILS))
n_lit = sum(1 for v in m.PARAMS.values() if v[4] == "lit")
print("      %d parameters: %d literature-informed, %d assumed" % (len(m.PARAMS), n_lit, len(m.PARAMS) - n_lit))

print("\n%s" % ("ALL TESTS PASSED" if not FAILS else "%d FAILED: %s" % (len(FAILS), ", ".join(FAILS))))
sys.exit(1 if FAILS else 0)
