"""Paired Monte Carlo radar benchmark. Run with Python 3 and NumPy."""
import json
import platform
import time
from pathlib import Path

import numpy as np


def wrap(angle):
    """Return an angular difference in [-pi, pi)."""
    return (angle + np.pi) % (2 * np.pi) - np.pi


def observe(states):
    """Map rows [x, y, vx, vy] to radar range and bearing."""
    return np.column_stack((np.hypot(states[:, 0], states[:, 1]),
                            np.arctan2(states[:, 1], states[:, 0])))


F = np.array([[1., 0, 1, 0], [0, 1, 0, 1],
              [0, 0, 1, 0], [0, 0, 0, 1]])
G = np.array([[.5, 0], [0, .5], [1, 0], [0, 1]])
Q = G @ G.T * .5 ** 2
R = np.diag([20. ** 2, np.deg2rad(3.) ** 2])
INITIAL = np.array([1000., 400., -12., 8.])
P0 = np.diag([200. ** 2, 200. ** 2, 3. ** 2, 3. ** 2])
UKF_KAPPA = 1.


def cycle(mean, covariance, measurement, method):
    """Predict linearly; KF converts radar data using first-order covariance."""
    if method not in ('KF', 'EKF', 'UKF', 'CKF'):
        raise ValueError(f'Unknown filter: {method}')
    mean = F @ mean
    covariance = F @ covariance @ F.T + Q
    if method == 'KF':
        # Practical converted-measurement baseline, NOT an exact Gaussian KF:
        # Cartesian noise is biased/non-Gaussian, and this covariance uses z.
        radius, angle = measurement
        cosine, sine = np.cos(angle), np.sin(angle)
        converted = radius * np.array([cosine, sine])
        J = np.array([[cosine, -radius*sine], [sine, radius*cosine]])
        converted_R = J @ R @ J.T
        cross = covariance[:, :2]
        innovation_cov = covariance[:2, :2] + converted_R
        gain = np.linalg.solve(innovation_cov, cross.T).T
        mean = mean + gain @ (converted - mean[:2])
        residual = np.eye(4)
        residual[:, :2] -= gain
        covariance = residual @ covariance @ residual.T + gain @ converted_R @ gain.T
        return mean, (covariance + covariance.T)/2
    if method == 'EKF':
        x, y = mean[:2]
        radius2 = x*x + y*y
        radius = np.sqrt(radius2)
        H = np.array([[x/radius, y/radius, 0, 0],
                      [-y/radius2, x/radius2, 0, 0]])
        expected = observe(mean[None, :])[0]
        cross = covariance @ H.T
        innovation_cov = H @ cross + R
    else:
        root = np.linalg.cholesky(covariance)
        # UKF: alpha=1, beta=2, kappa=1. CKF: 2n equal weights.
        n = mean.size
        scale = n + UKF_KAPPA if method == 'UKF' else n
        offsets = np.sqrt(scale) * root.T
        points = np.concatenate((mean + offsets, mean - offsets))
        weights = np.full(2*n, 1/(2*scale))
        covariance_weights = weights.copy()
        if method == 'UKF':
            points = np.vstack((mean, points))
            weights = np.r_[UKF_KAPPA/scale, weights]
            covariance_weights = np.r_[UKF_KAPPA/scale + 2., covariance_weights]
        images = observe(points)
        expected = weights @ images
        expected[1] = np.arctan2(weights @ np.sin(images[:, 1]),
                                 weights @ np.cos(images[:, 1]))
        deviations = images - expected
        deviations[:, 1] = wrap(deviations[:, 1])
        cross = ((points - mean).T * covariance_weights) @ deviations
        innovation_cov = (deviations.T * covariance_weights) @ deviations + R
    gain = np.linalg.solve(innovation_cov, cross.T).T
    innovation = measurement - expected
    innovation[1] = wrap(innovation[1])
    mean = mean + gain @ innovation
    covariance = covariance - gain @ innovation_cov @ gain.T
    return mean, (covariance + covariance.T)/2


def main():
    """Use common observations and truths; report pooled position RMSE and timing."""
    rng = np.random.default_rng(20261023)
    runs, steps = 100, 120
    errors = {name: [] for name in ('KF', 'EKF', 'UKF', 'CKF')}
    timings = {name: [] for name in errors}
    for run in range(runs):
        truth = rng.multivariate_normal(INITIAL, P0)
        truths, observations = [], []
        for _ in range(steps):
            truth = F @ truth + G @ rng.normal(0, .5, 2)
            z = observe(truth[None, :])[0] + rng.multivariate_normal(np.zeros(2), R)
            z[1] = wrap(z[1])
            truths.append(truth.copy())
            observations.append(z)
        # Rotate ordering to reduce systematic timing bias.
        names = list(errors)
        names = names[run % len(names):] + names[:run % len(names)]
        for name in names:
            mean, covariance = INITIAL.copy(), P0.copy()
            squared_errors = []
            elapsed = 0.
            for truth, z in zip(truths, observations):
                start = time.perf_counter()
                mean, covariance = cycle(mean, covariance, z, name)
                elapsed += time.perf_counter() - start
                squared_errors.append(float(np.sum((mean[:2] - truth[:2])**2)))
            errors[name].extend(squared_errors)
            timings[name].append(elapsed/steps * 1e6)
    result = {
        'seed': 20261023, 'runs': runs, 'steps': steps,
        'position_rmse_definition': 'sqrt(mean(dx**2 + dy**2)) over all runs and steps',
        'timing_definition': 'median across runs of mean predict+update microseconds; includes point generation',
        'environment': f'{platform.system()} {platform.machine()}, Python {platform.python_version()}, NumPy {np.__version__}',
        'model': 'dt=1 s; CV; acceleration sd=0.5 m/s^2; radar range sd=20 m; bearing sd=3 deg',
        'UKF': f'alpha=1, beta=2, kappa={UKF_KAPPA:g}; 9 measurement evaluations',
        'CKF': '8 measurement evaluations; equal positive weights',
        'KF': 'Converted measurements [r cos(b), r sin(b)]; R_cart=J(z) R J(z)^T. First-order approximation, not an exact Gaussian KF. Conversion included in timing.',
        'results': {name: {'rmse_m': float(np.sqrt(np.mean(errors[name]))),
                            'time_us': float(np.median(timings[name])),
                            'time_p25_us': float(np.percentile(timings[name], 25)),
                            'time_p75_us': float(np.percentile(timings[name], 75))}
                    for name in errors},
    }
    path = Path(__file__).with_name('benchmark-results.json')
    path.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
