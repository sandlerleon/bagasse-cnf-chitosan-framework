# Transparent rigid packaging from sugarcane bagasse: a consistency-testing framework

Code, figures and manuscript for *Toward transparent rigid packaging from sugarcane bagasse: a consistency-testing framework for nanocellulose–chitosan sheets* (Leon Sandler, 2026; submitted to *Cellulose*).

**Status: theoretical and computational. No experiments are reported, and nothing here claims that the proposed material works.** The question is whether three properties that the literature demonstrates separately, mostly on flat films, can coexist in one three-dimensional package wall: transparency, wet stiffness and a formable shape. Each requirement is checked against published evidence or a physical bound, and the answer is allowed to be no.

## What the framework returns

| Screen | Result |
|---|---|
| Optical (Debye–Bueche, derived prefactor, no fitted constant) | For a 100 µm wall, 10% haze and 5% voids, the correlation length must be about 10 nm or less. The cubic (Rayleigh-type) law overestimates scattering by about 7x at 80 nm. |
| Wet stiffness | Chitosan helps mainly through physical cross-linking. Median wet modulus is 2.36 GPa at 20% chitosan (neutral) against 0.85 GPa without it, and the benefit vanishes in acid. |
| Forming | Required total strain tolerance: tray 0.26, bowl 0.67, cup 1.10 (best case in the assumed ranges, fully hydrated: 0.96). The cup has no forming window anywhere in the assumed ranges. |
| Sensitivity | Spearman rank ranking of 19 parameters (11 are assumptions and are labelled as such). |

Pass-probabilities are conditional on the assumed priors. The robust results are the thresholds and the cup bound. The bulk-scattering screen does not by itself reproduce the haze of published clear nanopaper, and the manuscript reports that rather than hiding it. All numbers in the manuscript are read from `code/results.json` at build time.

## Repository layout

```
code/         model (tncc_model.py), 43 verification checks, analysis, figure scripts, results.json
figures/      Figures 1-5 as 600 dpi PNG and LZW TIFF
manuscript/   manuscript v2, Supplementary Information, cover letter (.docx) and their build scripts
references/   Crossref-resolved reference list (refs.py), harvest tooling, documented literature searches
tools/        Zenodo deposit script used for archiving
```

## Reproduce

Python 3.10+ with `numpy`, `matplotlib`, `pillow` and `python-docx`.

```bash
python code/verify_model.py      # 43 checks; all must pass
python code/run_analysis.py      # Monte Carlo (N = 200,000, seed 20261002) -> code/results.json
python code/make_figures.py      # figures/Figure1-5
python manuscript/build_manuscript.py
python manuscript/build_si.py
```

The manuscript build refuses to run if verification fails. The builders for the manuscript, SI and cover letter read the reserved Zenodo DOIs from a local deposit state file, so a fresh checkout needs that path edited or the DOIs passed in. The shipped `.docx` files already contain the final DOIs.

## Citation

- Code (all versions): https://doi.org/10.5281/zenodo.23111544
- Manuscript and Supplementary Information (preprint): https://doi.org/10.5281/zenodo.23111546
- Author: Leon Sandler, ORCID [0009-0007-4584-808X](https://orcid.org/0009-0007-4584-808X)

## Licences

Code: MIT (`LICENSE`). Manuscript, Supplementary Information, cover letter and figures: CC BY 4.0 (`manuscript/LICENSE`).

## AI use

Claude (Anthropic) was used as a drafting and analysis aid. The author directed the work, reviewed all content and takes responsibility for it. This is documented in Methods Section 5.5 of the manuscript.
