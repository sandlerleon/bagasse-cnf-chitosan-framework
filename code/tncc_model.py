# -*- coding: utf-8 -*-
"""Consistency-testing framework for a transparent, rigid, bagasse-derived
nanocellulose-chitosan package.

Three screens, each a physical bound or a stated relation rather than a prediction:

  Test 1  OPTICAL     Can a dense nanofibril wall keep bulk scattering low enough at
                      packaging thickness?   Debye-Bueche scattering from refractive-index
                      fluctuations (random two-phase medium, exponential correlation).
  Test 2  WET MECH.   Does chitosan raise wet stiffness, and does the answer survive an
                      acidic liquid?          Rule of mixtures with phase-wise moisture
                      knockdown and a cross-linking term.
  Test 3  FORMING     Does the strain budget of the target geometry fit inside the strain
                      the sheet can tolerate?  Area-conservation geometry + failure/void/
                      wrinkling limits.

Every parameter lives in PARAMS with its range and its basis. A range is tagged either
'lit' (taken from a verified reference, key given) or 'assumed' (author's bracket,
explored rather than asserted). Nothing here has been fitted to the paper's own data.

No experiments were performed. All outputs are screening estimates.
"""
import math

import numpy as np

# ------------------------------------------------------------------ constants
LAMBDA0 = 550e-9              # m, reference wavelength (mid-visible)
HAZE_CONE = math.radians(2.5)  # ASTM D1003: haze is light deviating more than 2.5 deg
K_DERIVED = 64.0 * math.pi ** 4 / 3.0   # small-q limit of the Debye-Bueche turbidity, derived below

# Gauss-Legendre nodes for the angular integrals (smooth integrands, 48 nodes is ample)
_GL_X, _GL_W = np.polynomial.legendre.leggauss(48)


# ------------------------------------------------------------ parameter registry
# name: (low, high, distribution, unit, status, basis)
#   distribution: 'u' uniform, 'lu' log-uniform
#   status      : 'lit' (verified reference key in basis) or 'assumed'
PARAMS = {
    # ---- optical
    "rho_film":  (1.29, 1.55, "u", "g cm-3", "lit",
                  "Measured density of clear transparent nanopaper, hsieh2017"),
    "rho_wall":  (1.50, 1.60, "u", "g cm-3", "assumed",
                  "Cell-wall density, amorphous (~1.5) to crystalline (~1.6) cellulose"),
    "n_cell":    (1.50, 1.62, "u", "-", "assumed",
                  "Refractive index of the cellulose phase; anisotropic, "
                  "complex index measured for TEMPO-CNF films in niskanen2022"),
    "a_ref":     (3.0, 15.0, "lu", "nm", "lit",
                  "Correlation length scale of void structure ~ wood-pulp fibril width: "
                  "3-4 nm in fukuzumi2009, 3-15 nm in hsieh2017"),
    "a_bag":     (5.0, 80.0, "lu", "nm", "lit",
                  "Bagasse CNF diameters 5-80 nm after microfluidization, carneiro2023"),
    "f_morph":   (0.3, 3.0, "lu", "-", "assumed",
                  "Multiplier on the derived prefactor for departures from exponential "
                  "correlation and the Born approximation"),
    # ---- wet mechanics
    "E_cnf":     (4.0, 14.0, "u", "GPa", "lit",
                  "Dry CNF film modulus: 4.79 GPa qing2012; ~4 GPa jiang2016; "
                  "14.7 GPa szymanska2019"),
    "E_chi":     (2.0, 4.0, "u", "GPa", "lit",
                  "Neat chitosan film modulus 2.3 and 3.4 GPa, fernandez2024"),
    "psi":       (0.5, 1.1, "u", "-", "lit",
                  "Dry network efficiency with chitosan present; 8.76/14.71 = 0.60 at "
                  "5 wt% in szymanska2019, up to ~1 or slightly above if no disruption"),
    "kappa_cnf": (0.02, 0.50, "lu", "-", "assumed",
                  "Retained fraction of plain-CNF stiffness when water-saturated"),
    "kappa_chi": (0.05, 0.60, "u", "-", "assumed",
                  "Retained fraction of chitosan stiffness when water-saturated (neutral)"),
    "xi_max":    (0.0, 0.8, "u", "-", "assumed",
                  "Maximum wet-retention gain from physical cross-linking by chitosan; "
                  "toivonen2015 shows the effect exists (wet films keep 4 GPa)"),
    "w_star":    (0.05, 0.20, "u", "-", "assumed",
                  "Chitosan fraction at which the cross-linking gain saturates"),
    "kappa_chi_acid": (0.0, 0.10, "u", "-", "assumed",
                  "Chitosan retention in an acidic liquid: chitosan is water-insoluble "
                  "and dissolves in acidic solutions, melro2021"),
    "xi_acid":   (0.0, 0.5, "u", "-", "assumed",
                  "Fraction of the cross-linking gain surviving an acidic liquid"),
    # ---- forming
    "eps_f_dry": (0.03, 0.16, "u", "-", "lit",
                  "Failure strain at ambient humidity: 8% at 50% RH toivonen2015; "
                  "16% jiang2016; lower bound assumed for a brittle dense sheet"),
    "d_eps_wet": (0.05, 0.30, "u", "-", "lit",
                  "Failure-strain gain when wet; toivonen2015 reports 28% wet vs 8% at 50% RH"),
    "r_void":    (0.2, 1.0, "u", "-", "assumed",
                  "Ratio of microvoid-onset strain to failure strain; <1 means "
                  "transparency is lost before the sheet fractures"),
    "eps_wrinkle": (0.05, 0.50, "u", "-", "assumed",
                  "Compressive log-strain the flange tolerates before wrinkling "
                  "(maximum draw ratio is exp of this value); no value exists for nanocellulose sheets"),
}

# reference package geometries: (bottom diameter, top diameter, depth), mm
GEOMETRY = {
    "tray (lid-like)": (100.0, 120.0, 12.0),
    "bowl":            (100.0, 150.0, 50.0),
    "cup":             (55.0, 80.0, 90.0),
}


def draw(name, n, rng):
    lo, hi, dist = PARAMS[name][:3]
    if dist == "lu":
        return np.exp(rng.uniform(math.log(lo), math.log(hi), n))
    return rng.uniform(lo, hi, n)


# =============================================================== TEST 1: OPTICAL
def void_fraction(rho_film, rho_wall):
    """Void volume fraction from film density; clipped at zero (a film cannot be denser
    than the wall material)."""
    return np.clip(1.0 - np.asarray(rho_film) / np.asarray(rho_wall), 0.0, 0.5)


def angular_split(a_nm, n_bar, lam=LAMBDA0):
    """Angular structure of Debye-Bueche scattering with unpolarised light.

    dSigma/dOmega  ~  (1+cos^2 th)/2  /  (1 + q^2 a^2)^2 ,   q = 2 k sin(th/2),  k = 2 pi n_bar/lam.
    Returns (g, f_haze, f_back):
      g       total turbidity relative to its small-qa limit (1 when qa << 1)
      f_haze  fraction of scattered light that goes forward and deviates by more than 2.5 deg
      f_back  fraction scattered into the backward hemisphere
    """
    a = np.asarray(a_nm, float) * 1e-9
    k = 2.0 * math.pi * np.asarray(n_bar, float) / lam
    a, k = np.broadcast_arrays(a, k)
    shape = a.shape
    a, k = a.ravel()[:, None], k.ravel()[:, None]

    def integral(lo, hi):
        x = 0.5 * (hi - lo) * _GL_X + 0.5 * (hi + lo)          # u = cos(theta)
        w = 0.5 * (hi - lo) * _GL_W
        q2a2 = 2.0 * (k * a) ** 2 * (1.0 - x[None, :])
        f = 0.5 * (1.0 + x[None, :] ** 2) / (1.0 + q2a2) ** 2
        return (f * w[None, :]).sum(axis=1)

    c = math.cos(HAZE_CONE)
    back = integral(-1.0, 0.0)
    fwd_wide = integral(0.0, c)
    fwd_cone = integral(c, 1.0)
    total = back + fwd_wide + fwd_cone
    g = total / (4.0 / 3.0)               # small-qa limit of the angular integral
    return (g.reshape(shape), (fwd_wide / total).reshape(shape), (back / total).reshape(shape))


def turbidity(phi, a_nm, n_cell, f_morph=1.0, lam=LAMBDA0):
    """Scattering coefficient tau (m^-1) of a dense nanofibril network.

    Derivation (Born / Rayleigh-Gans-Debye, random two-phase medium). For refractive-index
    fluctuations the scattering per unit volume per solid angle is
        dSigma/dOmega = (pi^2/lam^4) <d_eps^2> * Gamma(q) * (1+cos^2 th)/2,
    with Gamma(q) = 8 pi a^3 / (1+q^2 a^2)^2 for an exponential correlation function
    (Debye-Bueche 1949; Debye-Anderson-Brumberger 1957 for random porous solids) and
    <d_eps^2> = phi (1-phi) (n_c^2 - 1)^2 for a solid phase of index n_c and air voids.
    Integrating over 4 pi, in the small-qa limit,
        tau = (64 pi^4 / 3) phi (1-phi) (n_c^2-1)^2 a^3 / lam^4          (Eq. 2)
    so the prefactor K = 64 pi^4/3 is derived, not fitted. f_morph carries the uncertainty
    from departures of the real structure from the exponential-correlation model.
    """
    phi = np.asarray(phi, float)
    a = np.asarray(a_nm, float)
    n_c = np.asarray(n_cell, float)
    n_bar = np.sqrt((1.0 - phi) * n_c ** 2 + phi)
    g, f_haze, f_back = angular_split(a, n_bar, lam)
    d_eps = n_c ** 2 - 1.0
    tau0 = K_DERIVED * phi * (1.0 - phi) * d_eps ** 2 * (a * 1e-9) ** 3 / lam ** 4
    return f_morph * tau0 * g, f_haze, f_back


def haze_from_tau(tau, t_um, f_haze):
    """Single-scattering slab: direct transmittance exp(-tau t); a fraction f_haze of the
    scattered light is transmitted beyond 2.5 deg. Surface reflection multiplies direct and
    diffuse light alike, so it cancels in the haze ratio.

    Returns (direct_fraction, haze). Valid for tau*t up to about 1; beyond that, repeated
    scattering makes the real haze higher than this estimate, so values there are optimistic.
    """
    x = np.asarray(tau, float) * np.asarray(t_um, float) * 1e-6
    direct = np.exp(-x)
    diffuse = f_haze * (1.0 - direct)
    return direct, diffuse / (direct + diffuse)


def haze_budget(t_um, haze_max, f_haze=0.5):
    """Largest scattering coefficient tau_max (m^-1) compatible with a haze target at
    thickness t. Inverts haze = f(1-d) / (d + f(1-d)) with d = exp(-tau t):
        d = f (1-h) / (h (1-f) + f).
    """
    h = haze_max
    d = f_haze * (1.0 - h) / (h * (1.0 - f_haze) + f_haze)
    return -math.log(d) / (t_um * 1e-6)


def bulk_budget_nm3(tau_max, n_cell=1.55, f_morph=1.0, lam=LAMBDA0):
    """phi(1-phi) a^3 (nm^3) that a sheet may carry before bulk scattering alone exceeds
    tau_max. This is the quantity SAXS measures, so it is the Phase I target."""
    d_eps = n_cell ** 2 - 1.0
    return tau_max * lam ** 4 / (f_morph * K_DERIVED * d_eps ** 2) * 1e27


# =============================================================== TEST 2: WET MECH.
def E_wet(w, E_cnf, E_chi, psi, kappa_cnf, kappa_chi, xi_max, w_star, acid=False,
          kappa_chi_acid=0.0, xi_acid=0.0):
    """Water-saturated stiffness (GPa) of a CNF/chitosan sheet with chitosan mass fraction w.

        E_wet = (1-w) psi(w) kappa_c(w) E_cnf  +  w kappa_h E_chi

    psi: dry network-efficiency factor, applied as 1 at w=0 and relaxing to psi at large w,
         so w=0 recovers plain CNF exactly.
    kappa_c(w) = kappa_cnf + xi(w) (1 - kappa_cnf),  xi(w) = xi_max (1 - exp(-w/w_star)):
         physical cross-linking by chitosan raises the wet retention of the CNF phase
         (toivonen2015). In an acidic liquid chitosan hydrates and the gain is largely lost.
    This is a Voigt-type bound: it assumes perfect load sharing, so it is optimistic.
    """
    w = np.asarray(w, float)
    psi_w = 1.0 + (psi - 1.0) * (1.0 - np.exp(-w / 0.05))
    xi = xi_max * (1.0 - np.exp(-w / w_star))
    kh = kappa_chi_acid if acid else kappa_chi
    if acid:
        xi = xi * xi_acid
    kc = kappa_cnf + xi * (1.0 - kappa_cnf)
    return (1.0 - w) * psi_w * kc * E_cnf + w * kh * E_chi


def E_hyd(w, h, E_cnf, E_chi, psi, kappa_cnf, kappa_chi, xi_max, w_star, acid=False,
          kappa_chi_acid=0.0, xi_acid=0.0):
    """Stiffness (GPa) at hydration h in [0, 1], where h = 0 is the dry/ambient state and
    h = 1 the water-saturated state: linear interpolation between the two end states, so
    E_hyd(w, 1) == E_wet(w) and E_hyd(w, 0) is the dry rule of mixtures with the same
    network-efficiency factor. Used for the chitosan-content x moisture map."""
    w = np.asarray(w, float)
    psi_w = 1.0 + (psi - 1.0) * (1.0 - np.exp(-w / 0.05))
    e_dry = (1.0 - w) * psi_w * E_cnf + w * E_chi
    e_wet = E_wet(w, E_cnf, E_chi, psi, kappa_cnf, kappa_chi, xi_max, w_star, acid, kappa_chi_acid, xi_acid)
    return e_dry - np.asarray(h, float) * (e_dry - e_wet)


def a_max_nm(t_um, haze_max, phi, n_cell=1.55, f_morph=1.0, lo=1.0, hi=200.0):
    """Largest correlation length (nm) that keeps haze at or below haze_max for a sheet of
    thickness t and void fraction phi, using the full angular integral (bisection; haze is
    monotone in a)."""
    def h(a):
        tau, fh, _ = turbidity(phi, a, n_cell, f_morph)
        return float(haze_from_tau(tau, t_um, fh)[1])
    if h(lo) > haze_max:
        return None
    if h(hi) <= haze_max:
        return hi
    for _ in range(60):
        mid = math.sqrt(lo * hi)
        if h(mid) <= haze_max:
            lo = mid
        else:
            hi = mid
    return lo


# ================================================================ TEST 3: FORMING
def cup_area(d_b, d_t, h):
    """Surface area (mm^2) of a frustum cup: flat base plus conical wall."""
    slant = math.sqrt(h ** 2 + ((d_t - d_b) / 2.0) ** 2)
    return math.pi * d_b ** 2 / 4.0 + math.pi * (d_b + d_t) / 2.0 * slant


def strain_budget(d_b, d_t, h):
    """Mean equibiaxial log-strain a sheet would need if it received no material from the
    flange: 0.5 ln(A_cup / A_footprint), with the footprint being the base disc of the
    punch. Peak strain is never below the mean, so this is a lower bound on what the
    sheet must tolerate if all of the area comes from stretching."""
    return 0.5 * math.log(cup_area(d_b, d_t, h) / (math.pi * d_b ** 2 / 4.0))


def ldr_required(d_b, d_t, h, eps_crit):
    """Smallest limiting draw ratio LDR = D0/d_b at which mean tensile strain does not
    exceed eps_crit: A_cup/A_blank = exp(2 eps_crit)."""
    return math.sqrt(cup_area(d_b, d_t, h) / (math.pi * d_b ** 2 / 4.0) * math.exp(-2.0 * eps_crit))


def window_exists(d_b, d_t, h, eps_crit, eps_wrinkle):
    """The forming window is the interval LDR_min <= LDR <= LDR_max with
    LDR_min = ldr_required(...) and LDR_max = exp(eps_wrinkle). It exists iff the sum of the
    tolerated tensile and compressive strains covers the strain budget:
        eps_crit + eps_wrinkle >= strain_budget."""
    return np.asarray(eps_crit) + np.asarray(eps_wrinkle) >= strain_budget(d_b, d_t, h)


def eps_crit(eps_f_dry, d_eps_wet, r_void, hydration):
    """Strain the sheet may carry before it loses either integrity or transparency:
    min(eps_f, eps_void) = r * eps_f with r = min(1, r_void). Failure strain interpolates
    between its ambient and water-saturated values with hydration in [0, 1]."""
    eps_f = np.asarray(eps_f_dry) + np.asarray(d_eps_wet) * hydration
    return np.minimum(1.0, r_void) * eps_f


def s_max(eps_total):
    """Largest depth-to-base-diameter ratio of a straight-walled cup that a total strain
    tolerance eps_total can form: (exp(2 eps_total) - 1)/4. Used for the feasibility map."""
    return (np.exp(2.0 * np.asarray(eps_total)) - 1.0) / 4.0


# ===================================================================== statistics
def spearman(x, y):
    """Spearman rank correlation. Ties are rare in continuous samples, so plain ranks."""
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx -= rx.mean()
    ry -= ry.mean()
    return float((rx * ry).sum() / math.sqrt((rx ** 2).sum() * (ry ** 2).sum()))
