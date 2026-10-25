# Radar benchmark: cost and accuracy

## Reproduce

From the course folder:

```bash
python3 "Slides/Student Slides/benchmark_filters.py"
python3 -m unittest discover -s "Slides/Student Slides"
```

The benchmark writes `benchmark-results.json`. The deck embeds the reported numbers as a static snapshot, not a live data feed. Rerunning changes timing, so update the deck values and bar widths together if using a new run.

## Shared experiment

100 paired Monte Carlo trajectories, each 120 steps, seed 20261023. State order: position x, position y, velocity x, velocity y. Time interval: 1 second. Dynamics: constant velocity with independent Gaussian acceleration perturbations (standard deviation 0.5 m/s² per axis).

The initial truth is sampled from the same prior supplied to all four filters. Prior mean: [1000 m, 400 m, -12 m/s, 8 m/s]; standard deviations: [200 m, 200 m, 3 m/s, 3 m/s]. Every filter receives the same noisy radar observations for each trajectory. Radar noise standard deviations are 20 m in range and 3° in bearing. All filters use the same process and radar noise covariances.

The dynamics are linear, so each implementation uses the exact linear prediction. Only the radar measurement update needs a nonlinear treatment. This does not measure the cost of a fully nonlinear dynamics model.

## Filter definitions

- **KF***: practical converted-measurement baseline. Convert each radar observation to Cartesian coordinates and propagate its noise covariance with the conversion Jacobian evaluated at the observation. The resulting noise is not exactly Gaussian or unbiased, and the covariance is approximate. This is not an exact KF applied directly to nonlinear radar observations, nor a debiased converted-measurement filter.
- **EKF**: analytic radar Jacobian at the predicted mean.
- **UKF**: standard scaled rule, α = 1, β = 2, κ = 0; nine points for the four-dimensional predicted state. A circular mean and wrapped bearing differences handle angular observations.
- **CKF**: eight cubature points with equal positive weights. The same angular conventions are used as in the UKF.

For these UKF parameters the off-centre points match CKF, but the UKF central covariance weight is 2. The mean weight at the centre is zero. Thus this particular comparison concerns closely related integration rules, not two unrelated algorithms.

## Metrics and limitations

Position RMSE is the square root of the average squared Euclidean position error over all runs and all time steps, including initialization. It is not the average distance or a per-coordinate RMSE.

Runtime is the median, over trajectories, of mean predict-and-update time per cycle. It includes converted-measurement preprocessing or sigma-point generation, but not simulation or error scoring. Method order rotates across trajectories. Times depend on hardware, Python/NumPy and the chosen implementations; they are not a theoretical complexity ranking.

The slightly lower RMSE of the converted KF in this experiment is retained rather than choosing data to force a preferred ranking. Small differences have not been assessed for statistical significance. No consistency or robustness claim follows from these two metrics. Use further scenarios, covariance checks and multiple seeds for a broader evaluation.

## UKF versus CKF: interpretation

Application labels do not separate these filters: both can handle nonlinear dynamics and nonlinear measurements. The UKF application slide emphasizes configurable sampling; the CKF radar slide emphasizes a fixed rule. These are design motivations, not exclusive capabilities.

With α = 1, κ = 0 and β = 0 the standard unscented integration rule reduces to the third-degree spherical-radial cubature rule, assuming the same square-root and implementation conventions in exact arithmetic. Positive cubature weights help construct a covariance from weighted outer products but do not eliminate finite-precision problems or guarantee better estimation accuracy.

References: Arasaratnam and Haykin, “Cubature Kalman Filters,” IEEE Transactions on Automatic Control, 2009, DOI: 10.1109/TAC.2009.2019800; Julier and Uhlmann, “Unscented Filtering and Nonlinear Estimation,” Proceedings of the IEEE, 2004, DOI: 10.1109/JPROC.2003.823141.

## Initial uncertainty sweep (slide 5)

Reproduce with `python3 "Slides/Student Slides/uncertainty_sweep.py"`. Results: `uncertainty-results.json`. Seed 20261023; 300 paired trajectories, 30 updates; initial per-axis position standard deviations 25, 50, 100, 200, 400, 600 m. Velocity SD stays 3 m/s. Truth is sampled from the corresponding filter prior. Common standardized initial draws, process noise and measurement noise are reused across levels and filters. All other model settings match the radar benchmark. No failed or nonfinite runs occurred.

Position RMSE pools the first 30 post-update position errors. Shading uses 2,000 percentile bootstrap resamples of whole trajectories, preserving temporal dependence. These are individual pointwise intervals, not confidence intervals for paired filter differences or simultaneous bands. Initial uncertainty changes the sampled trajectory geometry as well as the prior width. The sweep is scenario evidence, not an isolated universal measure of nonlinearity or a general ranking. Runtime is deliberately omitted.
