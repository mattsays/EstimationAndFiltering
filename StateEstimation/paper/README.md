# Typst paper draft

The current English working draft is [main.typ](main.typ), compiled as [draft.pdf](draft.pdf). It contains the problem statement, related work, implemented estimators, experimental protocol, two measurement-noise sweeps at fixed process covariance, results, limitations and references. Citations use IEEE numbering; this is a readable single-column course-paper layout, not an official IEEE submission template.

The author is currently Mattia Sicoli, following the project owner. Confirm the final author list before submission if this is a joint paper.

## Source structure

`main.typ` is the entry point and lists the sections in reading order. Edit the body text in `sections/`:

```text
paper/
├── main.typ
├── style.typ                 # Layout, typography and document metadata
├── data.typ                  # JSON loading, validation and table helpers
├── sections/
│   ├── front-matter.typ       # Title, author and abstract
│   ├── introduction.typ
│   ├── models.typ
│   ├── methods.typ
│   ├── experiments.typ
│   ├── results.typ
│   ├── discussion.typ
│   └── conclusion.typ
├── references.bib
├── figures/
└── draft.pdf
```

The experimental design and results sections import the shared values they need from `data.typ`. Document styling is applied through the `paper-style` function in `style.typ`. Compile `main.typ` to build the complete paper, including citations and cross-references.

## Build and data

With Typst installed, run from this `paper` directory:

```bash
typst compile --root .. main.typ draft.pdf
```

The draft was checked with Typst 0.15.0. It uses built-in Typst features and a local BibLaTeX bibliography, without remote template packages.

Tables and numerical statements read the project's existing `../ship_tracking/noise-sensitivity.json`; no result JSON is duplicated. Assertions reject a different run count, seed, time grid, nominal noise or measurement sweep grid until the corresponding prose is revised.

To regenerate the paper's two vector plots, run from `../ship_tracking` in a Python environment with NumPy and Matplotlib:

```bash
python3 make_kf_report.py --paper-dir ../paper/figures
```

Then recompile the paper. Regenerate the figures whenever the experiment data change; Typst loads the numerical tables dynamically but embeds the last exported SVGs. The plotting command also refreshes the existing Markdown report. The simulation kernels and result file are unchanged by paper authoring.

The process covariance remains `Q = diag(0.0001, 0.0001, 0.0001, 0.0001)` per substep. Only bearing SD and range SD vary, independently; the other radar SD stays nominal.

## Selected literature and where it belongs

The seven entries are stored in [references.bib](references.bib). Bibliographic details and relevant source material were checked on 5 November 2026.

| Key | Source and verified link | Purpose in this draft |
| --- | --- | --- |
| `kalman1960` | R. E. Kalman, *A New Approach to Linear Filtering and Prediction Problems*, Journal of Basic Engineering 82(1), 35-45, 1960. [DOI](https://doi.org/10.1115/1.3662552); [original article reprint](https://eceweb1.rutgers.edu/~gajic/pdffiles/519KalmanFiltering/kalman1960.pdf). | Foundational linear filtering reference. |
| `julier2004` | S. J. Julier and J. K. Uhlmann, *Unscented Filtering and Nonlinear Estimation*, Proceedings of the IEEE 92(3), 401-422, 2004. [IEEE Xplore](https://ieeexplore.ieee.org/document/1271397/); [DOI](https://doi.org/10.1109/JPROC.2003.823141). | UKF motivation and distinction from local linearization. |
| `arasaratnam2009` | I. Arasaratnam and S. Haykin, *Cubature Kalman Filters*, IEEE Transactions on Automatic Control 54(6), 1254-1269, 2009. [IEEE Xplore](https://ieeexplore.ieee.org/document/4982682/); [DOI](https://doi.org/10.1109/TAC.2009.2019800). | Primary CKF and square-root CKF reference. |
| `arasaratnam-thesis2009` | I. Arasaratnam, *Cubature Kalman Filtering: Theory & Applications*, PhD thesis, McMaster University, April 2009. [Institutional full text](https://macsphere.mcmaster.ca/bitstream/11375/17242/1/Arasaratnam%20Ienkaran.pdf). | Original ship scenario, Section 6.1, printed pp. 75-80; derivation context for CKF/SCKF. |
| `lerro1993` | D. Lerro and Y. Bar-Shalom, *Tracking with Debiased Consistent Converted Measurements versus EKF*, IEEE Transactions on Aerospace and Electronic Systems 29(3), 1015-1022, 1993. [DOI](https://doi.org/10.1109/7.220948). | Foundational converted-measurement tracking reference. |
| `spitzmiller2010` | J. N. Spitzmiller and R. R. Adhami, *Tracking with Estimate-Conditioned Debiased 2-D Converted Measurements*, Intelligent Information Management 2, 286-294, 2010. [Publisher full text](https://file.scirp.org/pdf/iim20100400006_66126447.pdf); [DOI](https://doi.org/10.4236/iim.2010.23033). | Explains why bias removal alone does not solve covariance conditioning. |
| `pei2025` | A. J. Pei, *Tracking Methods for Converted Radar Measurements*, Johns Hopkins APL Technical Digest 38(1), article 2503437, 2025. [Institutional full text](https://www.jhuapl.edu/sites/default/files/2025-09/38-01-Pei.pdf). | Recent context for Cartesian conversion and geometry-dependent performance. |

IEEE Xplore's indexed records/abstracts verified the Julier and Arasaratnam journal metadata, but direct full-text access was limited during this session. Lerro's original full text was not inspected; its citation details are also confirmed in the primary reference list of Spitzmiller and Adhami (2010). The draft cites it as prior work and does not claim to implement its full consistent converted-measurement algorithm. Accessible original-paper reprints, institutional thesis text, and publisher PDFs were used for the other relevant checks.

## Findings from the source check

The original thesis explicitly uses normalized space and time. The draft therefore labels metres and seconds as the project's plotting convention, not a physical vessel calibration. It also calls the scenario an adaptation: the present 30-track, 0.01-substep experiment and implementation choices should not be represented as an exact reproduction of the thesis's reported curves or divergence behaviour.

The converted covariance in our baseline is evaluated at the predicted position. This approximation is stated explicitly; the draft does not equate the baseline with a full consistent CMKF or claim exact Gaussian optimality for polar radar data.

## Next substantive revisions

- Confirm the author list and any instructor-specific page or formatting requirements.
- Add a matched constant-velocity truth experiment to separate measurement nonlinearity from the KF baseline's motion-model mismatch.
- Add confidence intervals from paired trajectories and, if covariance outputs are retained, a consistency analysis such as NEES/NIS. These have not been computed and no significance claims appear in the draft.
- Consider a numerical stress experiment before claiming a practical SCKF stability advantage. Current CKF/SCKF accuracy overlaps in double precision.
- Keep coloured noise, covariance misspecification, and CRLB analysis as explicitly separate extensions unless actually implemented and evaluated.
