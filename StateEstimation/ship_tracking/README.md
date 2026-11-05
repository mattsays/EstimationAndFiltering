# State estimation project: ship tracking

This project compares a linear constant-velocity KF with EKF, UKF, CKF and square-root CKF (SCKF) on a radar-observed ship. It follows the nonlinear measurement direction of [Project 2](../Project%202.md).

Start with [KF comparison.md](KF%20comparison.md) for the model, experimental protocol, noise sensitivity tables and figures. The manuscript is in [../paper/main.typ](../paper/main.typ), with a [compiled draft](../paper/draft.pdf), [bibliography](../paper/references.bib) and [build/research notes](../paper/README.md). The exported `../presentation.html` is the original source presentation and predates the new experiments.

## Noise study

The simulation includes both process noise and radar measurement noise. Four independent sweeps vary one standard deviation at a time:

| Sweep | Varied component | Other noise components |
| --- | --- | --- |
| Bearing | Radar bearing SD, 0.5 to 30 degrees | Fixed at nominal levels |
| Range | Radar range SD, 0.01 to 0.5 m | Fixed at nominal levels |
| Process position | Position increment SD, 0.0025 to 0.08 m per substep | Fixed at nominal levels |
| Process velocity | Velocity increment SD, 0.0025 to 0.08 m/s per substep | Fixed at nominal levels |

Nominal levels are 0.5 degrees, 0.01 m range SD, 0.01 m position increment SD, and 0.01 m/s velocity increment SD. All noises are independent white Gaussian sequences. Actual simulation covariances and filter covariances are matched for every condition. The optional coloured-noise improvement in the assignment is not implemented by these intensity sweeps.

## Necessary files

| File | Purpose |
| --- | --- |
| `ship_benchmark.py` | Ship dynamics, radar observations and five filter implementations. Also offers an optional single-condition benchmark CLI. |
| `noise_sensitivity.py` | Reproducible paired sweeps of the four noise components; updates one results file. |
| `noise-sensitivity.json` | Current complete experiment: configuration, source hashes, metrics and per-scan RMSE curves. |
| `make_kf_report.py` | Generate the report and the two figure families from current results. |
| `test_kf_baseline.py` | Numerical checks for the KF baseline and the nonlinear filter prediction order. |
| `test_noise_sensitivity.py` | Check isolation of noise parameters, paired draws, matched covariances and failure handling. |
| `KF comparison.md` | English project report with methodology and results. |
| `figures/` | Measurement-noise and process-noise comparisons, each in PNG and SVG. |

The earlier bearing-only runner, slide generation scripts and superseded result JSON files have been removed from this project copy. The original source folder in the Obsidian vault is unchanged.

## Reproduce

Requires Python 3, NumPy and Matplotlib. Run from this folder:

```bash
python3 -m unittest -v test_kf_baseline.py test_noise_sensitivity.py
python3 noise_sensitivity.py --runs 30 --scans 800 --out noise-sensitivity.json
python3 make_kf_report.py
```

The defaults use seed 20261026, 30 tracks per condition, 800 radar scans per track, integration step 0.01 s, five integration substeps per radar scan, and 300 initialization scans excluded from summary averages. The nominal configuration is reused across sweeps, resulting in 21 unique conditions. No individual failed tracks are dropped: a failure invalidates the complete method/condition. Results are checkpointed with `complete: false` until all conditions finish; the report generator rejects incomplete results and checks the simulation source hashes.

Measurement sweeps preserve the same truth. Process sweeps change true trajectories while reusing the same initial states and standardized process/measurement draws. All five filters receive identical observations within each condition.

KF-CV uses constant velocity and unbiased Cartesian-converted radar observations, with approximate converted covariance. The other filters also know the ship's nonlinear turning force. Results therefore include motion-model mismatch and cannot isolate the effect of measurement nonlinearity alone. The state order is `[px, py, vx, vy]`.

A short paper with the required literature citations remains to be prepared.
