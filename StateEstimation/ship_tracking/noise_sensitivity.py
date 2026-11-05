"""Paired one-factor-at-a-time sweeps of radar measurement noise with fixed process covariance.

All noises are independent white Gaussian sequences. Each sweep varies exactly
one radar standard deviation. The process covariance Q remains fixed.
Run: python3 noise_sensitivity.py --runs 30 --scans 800
"""

import argparse
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import platform
import time

import numpy as np

import ship_benchmark as sb

BASE = {'sigma_r': 0.01, 'sigma_b_deg': 0.5, 'q_position': 0.01, 'q_velocity': 0.01}
SWEEPS = {
    'sigma_b_deg': (0.5, 2., 5., 10., 20., 30.),
    'sigma_r': (0.01, 0.02, 0.05, 0.1, 0.2, 0.5),
}


def configuration(parameter, value):
    if parameter not in SWEEPS or not np.isfinite(value) or value <= 0:
        raise ValueError('only bearing/range noise may vary, with a positive finite SD')
    return {**BASE, parameter: float(value)}


def validate_configuration(config):
    if set(config) != set(BASE) or any(not np.isfinite(v) or v <= 0 for v in config.values()):
        raise ValueError('noise configuration must contain positive finite standard deviations')
    if any(config[name] != BASE[name] for name in ('q_position', 'q_velocity')):
        raise ValueError('process noise is fixed at the nominal Q in this experiment')


@contextmanager
def filter_noise(config):
    """Give all filters the actual noise parameters and restore globals on exit."""
    validate_configuration(config)
    names = ('Q1', 'Q2', 'SIGMA_R', 'SIGMA_B', 'Q', 'R')
    saved = {name: getattr(sb, name) for name in names}
    try:
        sb.Q1, sb.Q2 = config['q_position'], config['q_velocity']
        sb.SIGMA_R = config['sigma_r']
        sb.SIGMA_B = np.deg2rad(config['sigma_b_deg'])
        sb.Q = np.diag([sb.Q1 ** 2, sb.Q1 ** 2, sb.Q2 ** 2, sb.Q2 ** 2])
        sb.R = np.diag([sb.SIGMA_R ** 2, sb.SIGMA_B ** 2])
        yield
    finally:
        for name, value in saved.items():
            setattr(sb, name, value)


def draw_randomness(rng, scans):
    """Same draw order as the original sweep, independent of noise amplitudes."""
    initial = rng.uniform(-.5, .5, 4)
    process = np.empty((scans, sb.SUBSTEPS, 4))
    measurement = np.empty((scans, 2))
    for k in range(scans):
        process[k] = rng.standard_normal((sb.SUBSTEPS, 4))
        measurement[k] = rng.standard_normal(2)
    return initial, process, measurement


def simulate(draws, config):
    """Replay fixed standard-normal draws at the specified true noise levels."""
    validate_configuration(config)
    initial, process, measurement = draws
    x = initial.copy()
    states = np.empty((len(process), 4))
    std = np.array([config['q_position']] * 2 + [config['q_velocity']] * 2)
    for k, increments in enumerate(process):
        for increment in increments:
            x = sb.f_batch(x[:, None])[:, 0] + std * increment
        states[k] = x
    observations = sb.h_batch(states.T).T
    observations[:, 0] += config['sigma_r'] * measurement[:, 0]
    observations[:, 1] = sb.wrap(observations[:, 1]
                               + np.deg2rad(config['sigma_b_deg']) * measurement[:, 1])
    return states, observations


def evaluate(config, draws, burn_in):
    """All paired tracks enter RMSE, or the whole method/condition is failed."""
    data = [simulate(d, config) for d in draws]
    truth = np.array([s for s, _ in data])
    result = {}
    with filter_noise(config):
        for name, fn in sb.FILTERS:
            start = time.perf_counter()
            estimates = []
            failure = None
            for index, (_, observations) in enumerate(data):
                try:
                    estimate = fn(observations)
                    if estimate.shape != truth[index].shape or not np.isfinite(estimate).all():
                        raise ValueError('non-finite estimate or incorrect output shape')
                    estimates.append(estimate)
                except (np.linalg.LinAlgError, ValueError, FloatingPointError) as exc:
                    failure = {'status': 'failed', 'failed_track_index': index,
                               'completed_tracks': len(estimates), 'error': str(exc)}
                    break
            elapsed = time.perf_counter() - start
            if failure:
                result[name] = failure
                print(f'  {name}: FAILED at track {index}: {failure["error"]}', flush=True)
                continue
            error = np.array(estimates) - truth
            position = np.sqrt(np.mean(np.sum(error[:, :, :2] ** 2, axis=2), axis=0))
            velocity = np.sqrt(np.mean(np.sum(error[:, :, 2:] ** 2, axis=2), axis=0))
            result[name] = {
                'status': 'ok', 'tracks': len(draws),
                'pos_rmse': float(position[burn_in:].mean()),
                'vel_rmse': float(velocity[burn_in:].mean()),
                'time_s_per_track': elapsed / len(draws),
                'curves': {'rmse_pos': position.tolist(), 'rmse_vel': velocity.tolist()},
            }
            print(f'  {name}: pos {result[name]["pos_rmse"]:.4f}, '
                  f'vel {result[name]["vel_rmse"]:.4f}, {len(draws)}/{len(draws)} tracks', flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', type=int, default=30)
    parser.add_argument('--scans', type=int, default=800)
    parser.add_argument('--seed', type=int, default=20261026)
    parser.add_argument('--burn-in', type=int, default=300)
    parser.add_argument('--out', type=Path, default=Path('noise-sensitivity.json'))
    args = parser.parse_args()
    if args.runs < 1 or not 0 <= args.burn_in < args.scans:
        parser.error('runs must be positive and 0 <= burn-in < scans')

    here = Path(__file__).resolve().parent
    hashes = {name: hashlib.sha256((here / name).read_bytes()).hexdigest()
              for name in ('noise_sensitivity.py', 'ship_benchmark.py')}
    result = {
        'schema_version': 2, 'runs': args.runs, 'scans': args.scans,
        'seed': args.seed, 'burn_in': args.burn_in, 'base': BASE,
        'sensitivity_parameters': list(SWEEPS),
        'fixed_process_covariance': np.diag([BASE['q_position'] ** 2] * 2 + [BASE['q_velocity'] ** 2] * 2).tolist(),
        'dt': sb.DT, 'substeps': sb.SUBSTEPS, 'radar_interval': sb.DT * sb.SUBSTEPS,
        'initial_mean': sb.X0_HAT.tolist(), 'initial_covariance_scale': sb.P0,
        'noise_model': 'mutually independent, temporally white Gaussian noise',
        'noise_knowledge': 'matched: filter Q/R use the true noise levels',
        'pairing': 'same initial states and standardized process/measurement draws across all cases',
        'rmse_policy': 'all tracks; a failed/non-finite track fails the entire method/condition',
        'baseline': sb.KF_DESCRIPTION, 'source_sha256': hashes,
        'environment': f'{platform.system()} {platform.machine()}, Python {platform.python_version()}, NumPy {np.__version__}',
        'complete': False, 'sweeps': {},
    }
    rng = np.random.default_rng(args.seed)
    draws = [draw_randomness(rng, args.scans) for _ in range(args.runs)]
    evaluated = {}
    for parameter, values in SWEEPS.items():
        result['sweeps'][parameter] = []
        for value in values:
            config = configuration(parameter, value)
            key = tuple(config[name] for name in BASE)
            print(f'\n{parameter} = {value:g}; all other noise parameters nominal', flush=True)
            if key not in evaluated:
                evaluated[key] = evaluate(config, draws, args.burn_in)
            else:
                print('  Reusing the identical nominal condition from this run.', flush=True)
            result['sweeps'][parameter].append({
                'value': value, 'config': config, 'methods': deepcopy(evaluated[key]),
            })
            # Checkpoint after each condition; incomplete runs are explicitly marked.
            temporary = args.out.with_suffix(args.out.suffix + '.tmp')
            temporary.write_text(json.dumps(result, indent=2, allow_nan=False))
            temporary.replace(args.out)
    result['complete'] = True
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False))
    print(f'\nWrote {args.out}: two measurement sweeps, {len(evaluated)} unique conditions.', flush=True)


if __name__ == '__main__':
    main()
