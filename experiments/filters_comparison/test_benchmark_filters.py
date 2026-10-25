"""Numerical sanity checks: python3 -m unittest discover -s 'Slides/Student Slides'."""
import unittest

import numpy as np

from benchmark_filters import F, INITIAL, P0, Q, R, cycle, observe, wrap


class BenchmarkTests(unittest.TestCase):
    def test_wrapped_innovation(self):
        self.assertAlmostEqual(wrap(np.deg2rad(-358)), np.deg2rad(2))

    def test_converted_measurement_update(self):
        """Compare the converted KF to an independent linear-Gaussian update."""
        z = np.array([1100., .4])
        H = np.eye(4)[:2]
        prior = F @ INITIAL
        P = F @ P0 @ F.T + Q
        J = np.array([[np.cos(z[1]), -z[0]*np.sin(z[1])],
                      [np.sin(z[1]), z[0]*np.cos(z[1])]])
        noise = J @ R @ J.T
        converted = z[0]*np.array([np.cos(z[1]), np.sin(z[1])])
        K = np.linalg.solve(H @ P @ H.T + noise, H @ P).T
        mean, covariance = cycle(INITIAL.copy(), P0.copy(), z, 'KF')
        np.testing.assert_allclose(mean, prior + K @ (converted - H @ prior))
        np.testing.assert_allclose(covariance, P - K @ H @ P, atol=1e-10)

    def test_finite_positive_covariances(self):
        """All four filters remain well-defined on a shared near-branch-cut track."""
        for method in ('KF', 'EKF', 'UKF', 'CKF'):
            mean = np.array([-1000., 2., 0., -.1])
            covariance = P0.copy()
            truth = mean.copy()
            for _ in range(30):
                truth = F @ truth
                mean, covariance = cycle(mean, covariance, observe(truth[None])[0], method)
                self.assertTrue(np.isfinite(mean).all(), method)
                np.testing.assert_allclose(covariance, covariance.T, atol=1e-10)
                self.assertGreater(np.linalg.eigvalsh(covariance).min(), 0, method)

    def test_rule_reproduces_input_moments(self):
        root = np.linalg.cholesky(P0)
        points = np.concatenate((INITIAL + 2*root.T, INITIAL - 2*root.T))
        np.testing.assert_allclose(points.mean(axis=0), INITIAL)
        deviations = points - INITIAL
        np.testing.assert_allclose(deviations.T @ deviations / 8, P0)

    def test_unknown_method_is_rejected(self):
        with self.assertRaises(ValueError):
            cycle(INITIAL, P0, np.array([1000., 0.]), 'typo')


if __name__ == '__main__':
    unittest.main()
