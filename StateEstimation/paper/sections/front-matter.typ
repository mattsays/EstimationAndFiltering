#align(center)[
  #text(size: 17pt, weight: "bold")[Noise Sensitivity in Radar Ship Tracking]
  #v(3pt)
  #text(size: 13pt)[A Comparison of Linear and Nonlinear Kalman Filters]
  #v(7pt)
  Mattia Sicoli \
  #text(size: 9pt)[Estimation and Filtering | Project 2]
]
#v(7pt)

#block(inset: (x: 8pt, y: 6pt), stroke: (left: 1.5pt + rgb("657b91")))[
  *Abstract.* We compare a constant-velocity Kalman filter with converted radar measurements against extended, unscented, cubature, and square-root cubature Kalman filters for two-dimensional ship tracking. A paired Monte Carlo experiment varies bearing and range noise separately, keeping the process covariance fixed and the other measurement-noise parameter nominal. Each condition uses 30 trajectories and 800 radar scans, with the true noise parameters supplied to every filter. At nominal noise, position errors are similar, while velocity errors differ substantially. At large bearing and range noise the nonlinear trackers outperform the baseline, but their relative ranking depends on the measurement-noise component and on whether position or velocity error is considered. The study reports reproducible sensitivity results and documents the confounding effect of motion-model mismatch.
]
