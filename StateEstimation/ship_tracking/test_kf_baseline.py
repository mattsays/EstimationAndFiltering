"""Numerical checks for conversion statistics and the linear KF baseline."""

import unittest
from unittest.mock import patch

import numpy as np

import ship_benchmark as sb


class BaselineTests(unittest.TestCase):
    def test_scan_process_covariance_matches_closed_form(self):
        A, covariance = sb.linear_cv_model()
        n, dt = sb.SUBSTEPS, sb.DT
        expected = np.zeros((4, 4))
        for pos, vel in ((0, 2), (1, 3)):
            expected[pos, pos] = n * sb.Q1 ** 2 + sb.Q2 ** 2 * dt ** 2 * n * (n - 1) * (2 * n - 1) / 6
            expected[pos, vel] = expected[vel, pos] = sb.Q2 ** 2 * dt * n * (n - 1) / 2
            expected[vel, vel] = n * sb.Q2 ** 2
        np.testing.assert_allclose(covariance, expected, atol=1e-15)
        np.testing.assert_allclose(A @ [1., 2., 3., 4.],
                                   [1. + n * dt * 3., 2. + n * dt * 4., 3., 4.])

    def test_unbiased_conversion_and_covariance_against_monte_carlo(self):
        rng = np.random.default_rng(20261105)
        radius, angle, samples = 5., 1.1, 300_000
        truth = radius * np.array([np.cos(angle), np.sin(angle)])
        for degrees in (0.5, 30.):
            with self.subTest(degrees=degrees), patch.object(sb, 'SIGMA_B', np.deg2rad(degrees)):
                polar = np.vstack((radius + sb.SIGMA_R * rng.standard_normal(samples),
                                   angle + sb.SIGMA_B * rng.standard_normal(samples)))
                cart = sb.converted_radar_measurement(polar).T
                theoretical = sb.converted_radar_covariance(truth)
                # Sampling tolerance is scaled by the theoretical standard error.
                np.testing.assert_array_less(np.abs(cart.mean(axis=0) - truth),
                                             6 * np.sqrt(np.diag(theoretical) / samples))
                np.testing.assert_allclose(np.cov(cart.T), theoretical, rtol=.02, atol=1e-6)

    def test_covariance_zero_bearing_noise_limit(self):
        position = np.array([3., 4.])
        with patch.object(sb, 'SIGMA_B', 0.):
            expected = sb.SIGMA_R ** 2 * np.outer(position / 5., position / 5.)
            np.testing.assert_allclose(sb.converted_radar_covariance(position), expected)

    def test_constant_velocity_recovery(self):
        steps = np.arange(1, 201) * sb.DT * sb.SUBSTEPS
        truth = np.column_stack((2. + .2 * steps, -1. - .1 * steps,
                                 np.full(200, .2), np.full(200, -.1)))
        polar = sb.h_batch(truth.T).T
        with patch.object(sb, 'SIGMA_B', 1e-5), patch.object(sb, 'SIGMA_R', 1e-5):
            estimate = sb.run_kf(polar)
        np.testing.assert_allclose(estimate[-20:], truth[-20:], atol=1e-6)

    def test_ekf_jacobian_uses_state_before_propagation(self):
        with patch.object(sb, 'jacobian_f', wraps=sb.jacobian_f) as jacobian:
            sb.run_ekf(np.array([[1., .5]]))
        np.testing.assert_array_equal(jacobian.call_args_list[0].args[0], sb.X0_HAT)


if __name__ == '__main__':
    unittest.main()
