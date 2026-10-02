# Transparent rigid packaging from sugarcane bagasse: a consistency-testing framework

Code, figures and manuscript for *Toward transparent rigid packaging from sugarcane bagasse: a consistency-testing framework for nanocellulose–chitosan sheets* (Leon Sandler, 2026; submitted to *Cellulose*).

**Status: theoretical and computational. No experiments are reported, and nothing here claims that the proposed material works.** The question is whether three properties that the literature demonstrates separately, mostly on flat films, can coexist in one three-dimensional package wall: transparency, wet stiffness and a formable shape. Each requirement is checked against published evidence or a physical bound, and the answer is allowed to be no. Liquid containment is untested, so every feasibility result is provisional.

## What the framework returns

| Screen | Result |
|---|---|
| Optical (Debye–Bueche, derived prefactor, no fitted constant) | Under the stated assumptions a 100 µm wall at 10% haze and 5% voids needs a correlation length of about 10 nm or less. The bulk screen does not by itself reproduce the haze of published clear nanopaper; rough surfaces and a coarse residual population narrow the gap and do not close it (Section 6.5). |
| Wet stiffness | Chitosan helps mainly through physical cross-linking (median gain +1.1 GPa with it, −0.1 GPa without). Its gain in an acidic liquid is small and of uncertain sign. |
| Forming | Required total strain tolerance: tray 0.26, bowl 0.67, cup 1.10 (best case in the assumed ranges, fully hydrated: 0.96). The cup needs a flange wrinkling strain above 0.64. |
| Coupling | Stiffness fixes a minimum wall thickness and thickness fixes the haze, so the liquid changes the optical budget (median minimum thickness 75 µm neutral, 99 µm acidic). A wax layer applied before forming narrows the forming window. |
| Robustness | Pass shares move by tens of percentage points across seven prior schemes. Thresholds, orderings and the cup bound do not (Section 6.7, Fig. 7). |

All numbers in the manuscript are read from `code/results.json` at build time.

## Repository layout

```
code/         model (tncc_model.py), 58 verification checks, analysis, figure scripts, results.json
code/figure_data/   CSV tables behind Figures 2-7
figures/      Figures 1-7 as 600 dpi PNG and LZW TIFF
manuscript/   manuscript v3, Supplementary Information, cover letter (.docx) and their build scripts
references/   Crossref-resolved reference list (refs.py), harvest and audit tooling, documented literature searches
tools/        Zenodo deposit scripts used for archiving
requirements.txt   pinned software versions
```

## Reproduce

Python 3.11 with the versions in `requirements.txt` (NumPy 2.4.6, Matplotlib 3.11.1, Pillow 12.3.0, python-docx 1.2.0).

```bash
python code/verify_model.py        # 58 checks; all must pass
python code/run_analysis.py        # Monte Carlo (N = 200,000, seed 20261002) -> code/results.json
python code/make_figures.py        # figures/Figure1-7
python code/export_figure_data.py  # code/figure_data/*.csv
python manuscript/build_manuscript.py
python manuscript/build_si.py
python manuscript/build_cover_letter.py
```

The manuscript build refuses to run if verification fails. `results.json` is deterministic given the seed: a clean clone reproduces the committed file. The reference audit (`python references/audit_refs.py`) queries Crossref, PubMed, OpenAlex and Semantic Scholar and so needs network access. PDF rendering of the `.docx` files used LibreOffice and is not part of the build.

## Citation

- Code (all versions): https://doi.org/10.5281/zenodo.23111544
- Manuscript and Supplementary Information (preprint, all versions): https://doi.org/10.5281/zenodo.23111546
- Author: Leon Sandler, ORCID [0009-0007-4584-808X](https://orcid.org/0009-0007-4584-808X)

## Licences

Code: MIT (`LICENSE`). Manuscript, Supplementary Information, cover letter and figures: CC BY 4.0 (`manuscript/LICENSE`).

## AI use

Claude (Anthropic) was used as an assistive tool for code drafting, code review, figure-script drafting, literature-record retrieval scripts, and drafting and language editing of the manuscript text. The author defined the research question, requirements and assumptions, directed the workflow and verification, reviewed the literature interpretation and approved all conclusions. This is documented in Methods Section 5.5 of the manuscript.

## Changelog

- **v1.1.0** (2 October 2026): response to review. Surface-scattering and coarse-population sensitivity of the optical screen; seven prior schemes; thickness coupling of the optical and stiffness screens; bounded wax-layer sensitivity; requirement for the cup; Figures 6 and 7; figure-data tables; final reference audit; Data availability and AI statements revised; 58 verification checks (was 43). Results of v1.0.0 (sections A–G of `results.json`) are unchanged.
- **v1.0.0** (2 October 2026): first release.
