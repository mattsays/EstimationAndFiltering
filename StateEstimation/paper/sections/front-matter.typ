#align(center)[
  #text(size: 17pt, weight: "bold")[Noise Sensitivity in Radar Ship Tracking]
  #v(3pt)
  #text(size: 13pt)[A Comparison of Linear and Nonlinear Kalman Filters]
  #v(7pt)
  Mattia Sicoli \
  #text(size: 9pt)[Estimation and Filtering | Project 2 | Draft, 5 November 2026]
]
#v(7pt)

#block(inset: (x: 8pt, y: 6pt), stroke: (left: 1.5pt + rgb("657b91")))[
  *Abstract.* We compare a constant-velocity Kalman filter with converted radar measurements against extended, unscented, cubature, and square-root cubature Kalman filters for two-dimensional ship tracking. A paired Monte Carlo experiment varies bearing noise, range noise, position process noise, and velocity process noise separately, keeping the other noise parameters nominal. Each condition uses 30 trajectories and 800 radar scans, with the true noise parameters supplied to every filter. At nominal noise, position errors are similar, while velocity errors differ substantially. Larger bearing and range noise favour the nonlinear trackers over the baseline, but the ranking is not universal: at the largest position process noise, the baseline has lower position error and higher velocity error than the cubature filter. The study reports reproducible sensitivity results and documents the confounding effect of motion-model mismatch.
]
