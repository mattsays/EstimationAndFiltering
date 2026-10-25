# Estimation and Filtering

A short graduate course held at **Xi'an Jiaotong University (XJTU)** on state estimation
in dynamic systems: how to recover the state of a system from noisy measurements, starting
from the Kalman filter and moving to nonlinear extensions such as the extended, unscented
and cubature Kalman filters.

## Presentation

The presentation in `presentation/` follows the course from the probabilistic idea of
estimation to the practical behaviour of the filters. It introduces the Kalman filter and
its limits, builds the unscented transform and the weights that make the unscented filter
work, shows the square-root cubature filter and its numerical details, and closes by
putting four filters side by side on a nonlinear problem, to see when linearization
matters and how to choose among them.

`presentation_editor.html` is the entry point that reads the deck and plays it.

## Experiments

`experiments/filters_comparison/` contains the Python scripts and JSON results that
compare KF, EKF, UKF and CKF on the same nonlinear test case; the charts in the deck come
from these runs.
