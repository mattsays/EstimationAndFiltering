"""Build the project report and figures from the single current results file.

Run: python3 make_kf_report.py
Requires NumPy and Matplotlib. Does not modify the exported presentation.
"""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator
import numpy as np

HERE = Path(__file__).resolve().parent
ORDER = ('KF', 'EKF', 'UKF', 'CKF', 'SCKF')
COLORS = {'KF': '#20252b', 'EKF': '#9467bd', 'UKF': '#0072b2',
          'CKF': '#d55e00', 'SCKF': '#009e73'}
LABELS = {name: ('KF-CV (converted)' if name == 'KF' else name) for name in ORDER}
AXES = {
    'sigma_b_deg': ('Bearing noise', 'Bearing SD (degrees)'),
    'sigma_r': ('Range noise', 'Range SD (m)'),
    'q_position': ('Process noise on position', 'Position increment SD per substep (m)'),
    'q_velocity': ('Process noise on velocity', 'Velocity increment SD per substep (m/s)'),
}

INTRODUCTION = r'''# State estimation: KF comparison and noise sensitivity

## What the assignment asks

[Project 2](../Project%202.md) includes both process noise $\mathbf{W}_k\sim\mathcal{N}(0,Q)$ and measurement noise $\mathbf{V}_k\sim\mathcal{N}(0,R)$. It gives no numerical values for their covariances and does not require a noise sensitivity sweep. Replacing white noise with coloured noise, AR noise or a random walk is an optional improvement direction. The project already follows the nonlinear radar measurement direction.

The experiments below model **both process and measurement noise** as independent, temporally white Gaussian sequences. Varying their standard deviations studies noise intensity; it does not implement the optional coloured-noise extension.

## Models and parameters

The code's state is $\mathbf{x}=[p_x,p_y,v_x,v_y]^T$. The simulated ship and all nonlinear filters use the existing nonlinear shore-turn model. A velocity correction acts outside a radius of 5 m when the vessel moves away from the origin. The linear KF baseline uses constant velocity, without this turning correction.

Per integration substep, the additive process-noise covariance is

$$
Q=\operatorname{diag}(q_p^2,q_p^2,q_v^2,q_v^2).
$$

Here $q_p$ is the standard deviation of each position increment, in metres per substep, and $q_v$ is that of each velocity increment, in m/s per substep. These are discrete increment standard deviations, not continuous-time spectral densities. Increments are mutually independent and independent across time.

The radar at the origin measures

$$
r_m=\sqrt{p_x^2+p_y^2}+v_r,
\qquad \theta_m=\operatorname{atan2}(p_y,p_x)+v_\theta.
$$

Its independent range and bearing errors have covariance

$$
R=\operatorname{diag}(\sigma_r^2,\sigma_\theta^2).
$$

Bearing standard deviations are displayed in degrees, converted to radians before computing $R$. Position and velocity process noises belong to $Q$; range and bearing noises belong to $R$.

| Parameter | Nominal SD | Sweep values |
| --- | --- | --- |
| Bearing measurement $\sigma_\theta$ | 0.5 degrees | 0.5, 2, 5, 10, 20, 30 degrees |
| Range measurement $\sigma_r$ | 0.01 m | 0.01, 0.02, 0.05, 0.1, 0.2, 0.5 m |
| Position process increment $q_p$ | 0.01 m | 0.0025, 0.005, 0.01, 0.02, 0.04, 0.08 m |
| Velocity process increment $q_v$ | 0.01 m/s | 0.0025, 0.005, 0.01, 0.02, 0.04, 0.08 m/s |

**One parameter varies at a time.** Within a process-noise sweep, the same SD is used for the two symmetric spatial axes, while the other process-noise block and both measurement noises stay nominal. Standard deviations are varied, so multiplying an SD by two multiplies its variance by four.

## Linear KF baseline

For the state ordering used here, the fixed linear state and observation matrices are

$$
F=\begin{bmatrix}1&0&\Delta t&0\\0&1&0&\Delta t\\0&0&1&0\\0&0&0&1\end{bmatrix},
\qquad H=\begin{bmatrix}1&0&0&0\\0&1&0&0\end{bmatrix}.
$$

The baseline aggregates five linear predictions and their process covariance exactly into one radar-scan prediction. It receives the same radar observations as the nonlinear filters, converted to Cartesian position. For example, a 5 m range at 0 degrees corresponds to $(5,0)$ m. Angular uncertainty makes converted errors anisotropic and non-Gaussian.

Let $a=\sigma_\theta^2$. The raw Cartesian conversion shrinks the expected position by $e^{-a/2}$. The baseline removes that bias using

$$
\mathbf{z}_c=e^{a/2}r_m\begin{bmatrix}\cos\theta_m\\\sin\theta_m\end{bmatrix}.
$$

At a fixed true range $\rho$, the radial and tangential error variances of this conversion are

$$
d_r=(\rho^2+\sigma_r^2)\cosh(a)-\rho^2,
\qquad d_t=(\rho^2+\sigma_r^2)\sinh(a).
$$

Rotate $\operatorname{diag}(d_r,d_t)$ by the target bearing to obtain the Cartesian covariance. Since truth is unavailable, the KF substitutes its predicted position. Its matrices $F,H$ are fixed, but its measurement covariance varies with the prediction. This plug-in approximation is not an exact Gaussian/MMSE solution or a full implementation of a published consistent converted-measurement filter.

Converted-measurement filtering and its conversion bias and covariance issues are discussed by [Pei (2025)](https://www.jhuapl.edu/sites/default/files/2025-09/38-01-Pei.pdf) and [Spitzmiller and Adhami (2010)](https://file.scirp.org/pdf/iim20100400006_66126447.pdf).

## Experimental protocol

'''


def load_results():
    results = json.loads((HERE / 'noise-sensitivity.json').read_text())
    if not results['complete']:
        raise ValueError('The noise sweep is incomplete; rerun it before building the report')
    expected = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                for name in results['source_sha256']}
    if expected != results['source_sha256']:
        raise ValueError('Simulation sources changed after these results were generated')
    if set(results['sweeps']) != set(AXES):
        raise ValueError('Expected four independent noise sweeps')
    return results


def plot_family(results, parameters, output_name, family_title):
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8), layout='constrained')
    for row, parameter in enumerate(parameters):
        cases = results['sweeps'][parameter]
        values = [case['value'] for case in cases]
        for col, (metric, label) in enumerate((('pos_rmse', 'Position RMSE (m)'),
                                               ('vel_rmse', 'Velocity RMSE (m/s)'))):
            ax = axes[row, col]
            for name in ORDER:
                y = [case['methods'][name].get(metric, np.nan) for case in cases]
                ax.plot(values, y, color=COLORS[name], label=LABELS[name], marker='o',
                        linestyle={'KF': '--', 'SCKF': ':'}.get(name, '-'),
                        linewidth=2.5 if name == 'SCKF' else 1.8, markersize=4)
            ax.axvline(results['base'][parameter], color='#888888', linestyle=':',
                       linewidth=1, label='Nominal noise' if row == col == 0 else None)
            ax.set_xscale('log')
            ax.set_xticks(values, [f'{v:g}' for v in values])
            ax.xaxis.set_minor_locator(NullLocator())
            ax.set(xlabel=AXES[parameter][1], ylabel=label, title=AXES[parameter][0])
            ax.set_ylim(bottom=0)
            ax.grid(True, alpha=.2)
            ax.spines[['top', 'right']].set_visible(False)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle(f"{family_title}: one parameter varies, all other noises nominal\n"
                 f"{results['runs']} paired tracks, mean per-scan RMSE after initialization", fontsize=13)
    for extension in ('png', 'svg'):
        fig.savefig(HERE / 'figures' / f'{output_name}.{extension}', dpi=180,
                    bbox_inches='tight', facecolor='white')
    plt.close(fig)


def paper_figures(results, destination):
    """Export four compact vector plots with legible type at paper width."""
    destination.mkdir(parents=True, exist_ok=True)
    short_axes = {
        'sigma_b_deg': 'Bearing SD (degrees)',
        'sigma_r': 'Range SD (m)',
        'q_position': 'Position increment SD per step (m)',
        'q_velocity': 'Velocity increment SD per step (m/s)',
    }
    with plt.rc_context({'font.size': 8.5, 'axes.titlesize': 9,
                         'svg.fonttype': 'path'}):
        for parameter, cases in results['sweeps'].items():
            fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.55), layout='constrained')
            values = [case['value'] for case in cases]
            for ax, metric, ylabel in zip(axes, ('pos_rmse', 'vel_rmse'),
                                           ('Position RMSE (m)', 'Velocity RMSE (m/s)')):
                for name in ORDER:
                    ax.plot(values, [c['methods'][name].get(metric, np.nan) for c in cases],
                            label='KF-CV' if name == 'KF' else name, color=COLORS[name],
                            linestyle={'KF': '--', 'SCKF': ':'}.get(name, '-'),
                            linewidth=1.9 if name == 'SCKF' else 1.25,
                            marker='o', markersize=2.5)
                ax.axvline(results['base'][parameter], color='#888888', linestyle=':', linewidth=.7)
                ax.set_xscale('log')
                ax.set_xticks(values, [f'{v:g}' for v in values])
                ax.xaxis.set_minor_locator(NullLocator())
                ax.tick_params(axis='x', labelsize=7.5)
                ax.set(xlabel=short_axes[parameter], ylabel=ylabel)
                ax.set_ylim(bottom=0)
                ax.grid(True, alpha=.2)
                ax.spines[['top', 'right']].set_visible(False)
            axes[0].legend(fontsize=6.8, ncol=2)
            fig.savefig(destination / f'{parameter}.svg', bbox_inches='tight', facecolor='white')
            plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paper-dir', type=Path, help='also export four compact SVG figures for the Typst paper')
    args = parser.parse_args()
    results = load_results()
    if args.paper_dir is not None:
        paper_figures(results, args.paper_dir)
    (HERE / 'figures').mkdir(exist_ok=True)
    plt.rcParams.update({'font.size': 10, 'axes.titlesize': 12})
    plot_family(results, ('sigma_b_deg', 'sigma_r'), 'measurement-noise-comparison', 'Measurement noise R')
    plot_family(results, ('q_position', 'q_velocity'), 'process-noise-comparison', 'Process noise Q')
    first_time = (results['burn_in'] + 1) * results['radar_interval']
    last_time = results['scans'] * results['radar_interval']
    text = INTRODUCTION + f'''- {results['runs']} trajectories per condition, {results['scans']} radar scans per trajectory, seed {results['seed']}.
- Integration step {results['dt']:g} s, {results['substeps']} substeps per radar scan, radar interval {results['radar_interval']:g} s, trajectory duration {last_time:g} s.
- The same initial states and standardized process and measurement draws are reused across every condition. Changing measurement noise leaves truth unchanged. Changing process noise necessarily changes the trajectories, using the same underlying random draws.
- Within each condition, all five filters receive identical truth and observations for evaluation. Each filter is given the actual noise levels: both its $Q$ and $R$ are updated to match the simulator. This is a matched-noise sensitivity study, not a covariance-misspecification experiment.
- Every filter starts from mean $[1,1,1,1]^T$ and covariance $10I_4$. The nonlinear shore-turn model and all other parameters remain fixed. KF-CV retains its constant-velocity model and has no separate maneuver-noise tuning.
- Position RMSE at each scan is the square root of the mean squared Euclidean position error across all trajectories. Velocity RMSE uses the two velocity components. Tables average these per-scan RMSE values over scans {results['burn_in']+1}-{results['scans']} ({first_time:g}-{last_time:g} s). They do not pool time samples before taking the square root.
- All tracks enter the metrics. A non-finite estimate or numerical failure invalidates the entire method/condition; survivor-only averages are not reported. Failed points appear as gaps in graphs and `FAILED` in tables.
- The nominal condition is identical in all four sweeps and is evaluated once, then reused within this execution. There are 24 displayed points and 21 unique configurations. CKF and SCKF are both executed, even where their curves overlap.
- The EKF evaluates the dynamics Jacobian before propagation. Timings include filtering and conversion, excluding simulation and plotting; they depend on implementation and hardware.

## Nominal-noise comparison

All four noise standard deviations are nominal. Runtime is per {results['scans']}-scan track.

| Method | Position RMSE (m) | Velocity RMSE (m/s) | Runtime (ms/track) | Tracks |
| --- | ---: | ---: | ---: | ---: |
'''
    nominal = next(case for case in results['sweeps']['sigma_b_deg']
                   if case['config'] == results['base'])
    for name in ORDER:
        m = nominal['methods'][name]
        if m['status'] == 'ok':
            text += (f"| {LABELS[name]} | {m['pos_rmse']:.4f} | {m['vel_rmse']:.4f} | "
                     f"{1000*m['time_s_per_track']:.1f} | {m['tracks']}/{results['runs']} |\n")
        else:
            text += f"| {LABELS[name]} | FAILED | FAILED | n/a | n/a |\n"
    for title, parameters, figure in (
        ('Measurement noise', ('sigma_b_deg', 'sigma_r'), 'measurement-noise-comparison'),
        ('Process noise', ('q_position', 'q_velocity'), 'process-noise-comparison'),
    ):
        text += f'\n## {title}\n\n'
        text += 'Each table cell is **position RMSE (m) / velocity RMSE (m/s)**. All other noise parameters stay at the nominal values above.\n\n'
        text += f'![Independent noise sweeps: position and velocity RMSE for all five filters.](figures/{figure}.png)\n\n'
        for parameter in parameters:
            text += f'### {AXES[parameter][0]}\n\n'
            text += f'| {AXES[parameter][1]} | KF-CV (converted) | EKF | UKF | CKF | SCKF |\n'
            text += '| ---: | ---: | ---: | ---: | ---: | ---: |\n'
            for case in results['sweeps'][parameter]:
                cells = [f"{case['value']:g}"]
                for name in ORDER:
                    m = case['methods'][name]
                    cells.append(f"{m['pos_rmse']:.4f} / {m['vel_rmse']:.4f}" if m['status'] == 'ok' else 'FAILED')
                text += '| ' + ' | '.join(cells) + ' |\n'
            text += '\n'
    failures = [(p, c['value'], n, m['error']) for p, cases in results['sweeps'].items()
                for c in cases for n, m in c['methods'].items() if m['status'] != 'ok']
    text += '## Interpretation and limits\n\n'
    if not failures:
        text += f"All five filters produced finite estimates for all {results['runs']} tracks in every condition.\n\n"
    else:
        text += 'Numerical failures were recorded without excluding individual tracks:\n\n'
        for parameter, value, name, error in failures:
            text += f'- {name}, {parameter}={value:g}: {error}.\n'
        text += '\n'
    for parameter in AXES:
        case = results['sweeps'][parameter][-1]
        kf, ckf = case['methods']['KF'], case['methods']['CKF']
        if kf['status'] == ckf['status'] == 'ok':
            text += (f"At the highest tested {AXES[parameter][0].lower()} ({case['value']:g}), "
                     f"KF-CV vs CKF position RMSE is {kf['pos_rmse']:.4f} vs {ckf['pos_rmse']:.4f} m, "
                     f"and velocity RMSE is {kf['vel_rmse']:.4f} vs {ckf['vel_rmse']:.4f} m/s.\n\n")
    text += r'''The comparison includes motion-model mismatch: nonlinear filters know the ship's turning force, whereas KF-CV does not. Differences must not be attributed solely to measurement nonlinearity. In particular, higher process noise changes the physical trajectories and when turns occur; the process sweep is not merely a change in filter confidence. No monotonic ranking or universal superiority follows from this finite ensemble. A separate constant-velocity truth experiment could isolate measurement effects, and a separate mismatched-noise experiment could test incorrect assumed $Q/R$.

Gaussian range errors are not clipped: the observation model can produce negative noisy ranges near the origin. This retains the stated additive Gaussian model. No samples are removed on that basis.

## Project files and reproduction

The project keeps a single current results file, [noise-sensitivity.json](noise-sensitivity.json), containing settings, source hashes, per-condition summaries, and full per-scan RMSE curves. The simulation entry point is `noise_sensitivity.py`; the filter and ship model implementations are in `ship_benchmark.py`. PNG and SVG versions of the two figures are in `figures/`.

From this folder, with NumPy and Matplotlib installed:

```bash
python3 -m unittest -v test_kf_baseline.py test_noise_sensitivity.py
python3 noise_sensitivity.py --runs 30 --scans 800 --out noise-sensitivity.json
python3 make_kf_report.py
```

Tests cover conversion statistics against Monte Carlo samples, the linear KF, process covariance aggregation, the EKF Jacobian evaluation point, changing exactly one noise parameter, matching simulator/filter covariances, restoring parameters after exceptions, replaying the original random draw order, preserving truth for measurement sweeps, and reusing standardized measurement noise for process sweeps.

The original exported `../presentation.html` remains a source presentation; it does not include these new figures. A short paper with the required literature citations remains to be prepared.

'''
    text += f"Execution environment: {results['environment']}.\n"
    (HERE / 'KF comparison.md').write_text(text)
    print('Wrote KF comparison.md and two PNG/SVG figures from noise-sensitivity.json')


if __name__ == '__main__':
    main()
