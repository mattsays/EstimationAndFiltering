#pagebreak()
= Discussion and limitations

The baseline has linear motion while the other filters know the nonlinear turn. Observed differences therefore combine motion-model mismatch, Cartesian conversion statistics, and nonlinear moment approximations. A further experiment using constant-velocity truth for every method would be needed to isolate measurement nonlinearity. Likewise, no parameter search was performed to build an optimally tuned linear maneuvering tracker.

The switch in @eq-turn is nonsmooth, the initial state prior is deliberately imperfect, and the ensemble contains only 30 paired trajectories. No confidence intervals, hypothesis tests, normalized estimation error squared (NEES), or innovation-consistency analysis have been computed. Small numerical differences should not be described as statistically significant. The results are synthetic and are not validated against measured vessel tracks.

SCKF and CKF agree at displayed precision, as expected from their common cubature rule. This double-precision experiment does not establish a practical stability advantage for SCKF; that would require a controlled numerical stress or reduced-precision study. Finally, all noises remain white Gaussian, with known covariances. Coloured noise and covariance misspecification are separate extensions rather than outcomes demonstrated here.
