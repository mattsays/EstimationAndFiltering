#import "../data.typ": nominal, nominal-table, digits, endpoint

= Results

== Nominal noise

#figure(
  nominal-table(),
  kind: table,
  caption: [Nominal-noise results: mean per-scan RMSE after initialization and mean filtering time per 800-scan trajectory. Values are read directly from the current experiment JSON.],
) <tab-nominal>

At nominal noise, position RMSE is nearly identical across methods (@tab-nominal). Velocity is more discriminating: KF-CV has error #digits(nominal.KF.vel_rmse) m/s, compared with #digits(nominal.EKF.vel_rmse) m/s for EKF, #digits(nominal.UKF.vel_rmse) m/s for UKF, and #digits(nominal.CKF.vel_rmse) m/s for CKF. KF-CV is fastest in this implementation, while SCKF costs more than CKF. Aggregated linear prediction, the number of point transformations, and implementation details all affect these timings.

== Measurement-noise sensitivity

#figure(
  image("../figures/sigma_b_deg.svg", width: 100%),
  caption: [Bearing-noise sweep. Range and both process noises remain nominal. Curves show mean per-scan RMSE after initialization; the dotted vertical line marks nominal noise. SCKF overlaps CKF at the plotted precision.],
) <fig-bearing>

At 30-degree bearing noise, KF-CV position RMSE is #digits(endpoint("sigma_b_deg", "KF", "pos_rmse")) m, versus #digits(endpoint("sigma_b_deg", "CKF", "pos_rmse")) m for CKF (@fig-bearing). This is a #digits(100 * (1 - endpoint("sigma_b_deg", "CKF", "pos_rmse") / endpoint("sigma_b_deg", "KF", "pos_rmse")), places: 1)% reduction in this ensemble. UKF has slightly lower position error than CKF at that endpoint, whereas CKF has lower velocity error. The experiment therefore does not establish a single winner even among the nonlinear methods.

#figure(
  image("../figures/sigma_r.svg", width: 100%),
  caption: [Range-noise sweep with bearing standard deviation fixed at 0.5 degrees and both process noises nominal. The Gaussian range model is not truncated near zero.],
) <fig-range>

At range SD 0.5 m, KF-CV position RMSE is #digits(endpoint("sigma_r", "KF", "pos_rmse")) m and CKF reaches #digits(endpoint("sigma_r", "CKF", "pos_rmse")) m. However, EKF has the smallest endpoint velocity RMSE among these nonlinear methods: #digits(endpoint("sigma_r", "EKF", "vel_rmse")) m/s, versus #digits(endpoint("sigma_r", "CKF", "vel_rmse")) m/s for CKF (@fig-range). Increasing range noise does not simply reproduce the bearing-noise ranking.

== Process-noise sensitivity

#figure(
  image("../figures/q_position.svg", width: 100%),
  caption: [Position process-noise sweep. The velocity process-noise SD stays at 0.01 m/s per substep, and both radar noises remain nominal. Changing process noise changes the true trajectories as well as the filter covariance.],
) <fig-process-position>

At $q_p=0.08$, KF-CV has lower position error (#digits(endpoint("q_position", "KF", "pos_rmse")) m) than CKF (#digits(endpoint("q_position", "CKF", "pos_rmse")) m), while its velocity error is substantially larger: #digits(endpoint("q_position", "KF", "vel_rmse")) versus #digits(endpoint("q_position", "CKF", "vel_rmse")) m/s. Thus a position-only evaluation would miss a material trade-off (@fig-process-position). The present data alone do not isolate the cause of that reversal.

#figure(
  image("../figures/q_velocity.svg", width: 100%),
  caption: [Velocity process-noise sweep. Position process noise and both measurement noises stay nominal. The baseline's velocity-error curve is nonmonotonic over the tested grid.],
) <fig-process-velocity>

At $q_v=0.08$, KF-CV and CKF position errors are #digits(endpoint("q_velocity", "KF", "pos_rmse")) and #digits(endpoint("q_velocity", "CKF", "pos_rmse")) m, whereas velocity errors are #digits(endpoint("q_velocity", "KF", "vel_rmse")) and #digits(endpoint("q_velocity", "CKF", "vel_rmse")) m/s. KF-CV's nonmonotonic velocity sensitivity reinforces that changing $Q$ affects both simulated motion and how the tracker balances prediction and observations (@fig-process-velocity).
