"""Checks for one-at-a-time noise variation and paired simulation."""

import unittest
from unittest.mock import patch
import numpy as np

import ship_benchmark as sb
import noise_sensitivity as ns


class NoiseSensitivityTests(unittest.TestCase):
    def test_one_parameter_changes(self):
        for parameter, values in ns.SWEEPS.items():
            for value in values:
                config = ns.configuration(parameter, value)
                changed = {key for key in ns.BASE if config[key] != ns.BASE[key]}
                self.assertEqual(changed, set() if value == ns.BASE[parameter] else {parameter})

    def test_filter_noise_matches_truth_and_restores_after_error(self):
        saved = {name: getattr(sb, name) for name in ('Q1', 'Q2', 'SIGMA_R', 'SIGMA_B', 'Q', 'R')}
        for parameter in ns.SWEEPS:
            config = ns.configuration(parameter, ns.BASE[parameter] * 2)
            with self.assertRaisesRegex(RuntimeError, 'restore'):
                with ns.filter_noise(config):
                    expected_q = np.diag([config['q_position'] ** 2] * 2
                                         + [config['q_velocity'] ** 2] * 2)
                    expected_r = np.diag([config['sigma_r'] ** 2,
                                          np.deg2rad(config['sigma_b_deg']) ** 2])
                    np.testing.assert_array_equal(sb.Q, expected_q)
                    np.testing.assert_array_equal(sb.R, expected_r)
                    raise RuntimeError('restore')
            for name, value in saved.items():
                np.testing.assert_array_equal(getattr(sb, name), value)

    def test_replay_matches_original_draw_order(self):
        seed, scans = 741, 10
        rng = np.random.default_rng(seed)
        x = rng.uniform(-.5, .5, 4)
        truth, observations = [], []
        for _ in range(scans):
            for _ in range(sb.SUBSTEPS):
                x = sb.f_batch(x[:, None])[:, 0] + .01 * rng.standard_normal(4)
            truth.append(x.copy())
            noise = rng.standard_normal(2)
            observations.append([np.hypot(x[0], x[1]) + .01 * noise[0],
                                 sb.wrap(np.arctan2(x[1], x[0]) + np.deg2rad(.5) * noise[1])])
        actual = ns.simulate(ns.draw_randomness(np.random.default_rng(seed), scans), ns.BASE)
        np.testing.assert_array_equal(actual[0], truth)
        np.testing.assert_allclose(actual[1], observations, atol=1e-15)

    def test_measurement_sweeps_keep_truth_and_other_channel_fixed(self):
        draws = ns.draw_randomness(np.random.default_rng(7), 20)
        truth, base_obs = ns.simulate(draws, ns.BASE)
        for parameter, fixed_channel in (('sigma_r', 1), ('sigma_b_deg', 0)):
            other_truth, other_obs = ns.simulate(draws, ns.configuration(parameter, ns.BASE[parameter] * 2))
            np.testing.assert_array_equal(other_truth, truth)
            np.testing.assert_array_equal(other_obs[:, fixed_channel], base_obs[:, fixed_channel])

    def test_process_noise_cannot_vary(self):
        self.assertEqual(set(ns.SWEEPS), {'sigma_r', 'sigma_b_deg'})
        draws = ns.draw_randomness(np.random.default_rng(17), 20)
        for parameter in ('q_position', 'q_velocity'):
            with self.assertRaises(ValueError):
                ns.configuration(parameter, ns.BASE[parameter] * 2)
            invalid = {**ns.BASE, parameter: ns.BASE[parameter] * 2}
            with self.assertRaisesRegex(ValueError, 'process noise is fixed'):
                ns.simulate(draws, invalid)
            with self.assertRaisesRegex(ValueError, 'process noise is fixed'):
                with ns.filter_noise(invalid):
                    self.fail('A changed Q must not enter the experiment')

    def test_failed_track_invalidates_whole_condition_without_stopping_other_methods(self):
        rng = np.random.default_rng(8)
        draws = [ns.draw_randomness(rng, 4) for _ in range(2)]
        good = np.zeros((4, 4))
        with patch.object(sb, 'FILTERS', (
            ('broken', unittest.mock.Mock(side_effect=[good, ValueError('bad track')])),
            ('working', lambda observations: good.copy()),
        )), patch('builtins.print'):
            result = ns.evaluate(ns.BASE, draws, burn_in=1)
        self.assertEqual(result['broken']['status'], 'failed')
        self.assertEqual(result['broken']['failed_track_index'], 1)
        self.assertNotIn('pos_rmse', result['broken'])
        self.assertEqual(result['working']['status'], 'ok')
        self.assertEqual(result['working']['tracks'], 2)


if __name__ == '__main__':
    unittest.main()
