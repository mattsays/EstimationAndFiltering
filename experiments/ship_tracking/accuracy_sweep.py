"""Accuracy of EKF, UKF, CKF and SCKF on the ship benchmark as the radar gets noisier.

The thesis uses a very precise radar (range 0.01 m, bearing 0.5 deg).  In that
regime all four filters reach the measurement floor, so their curves overlap and
a single accuracy plot says nothing.  Here the same ship trajectories are re-used
while only the bearing noise grows, which widens the posterior and makes the
EKF linearisation error visible.  The thesis value is the first point.

Run: python3 accuracy_sweep.py [--runs 30] [--scans 800]
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np

import ship_benchmark as sb

SIGMAS_DEG = (0.5, 2., 5., 10., 20., 30.)
THESIS_DEG = 0.5
STRESS_DEG = 30.


def make_run(rng, scans):
    """True states and standardised measurement noise, independent of sigma_b."""
    x = rng.uniform(-.5, .5, 4)
    states = np.empty((scans, 4))
    noise = np.empty((scans, 2))
    noise_std = np.array([sb.Q1, sb.Q1, sb.Q2, sb.Q2])
    for k in range(scans):
        for _ in range(sb.SUBSTEPS):
            x = sb.f_batch(x[:, None])[:, 0] + noise_std * rng.standard_normal(4)
        states[k] = x
        noise[k] = rng.standard_normal(2)
    return states, noise


def measurements(states, noise, sigma_b_deg):
    r = np.hypot(states[:, 0], states[:, 1])
    b = np.arctan2(states[:, 1], states[:, 0])
    return np.column_stack((r + sb.SIGMA_R * noise[:, 0],
                            sb.wrap(b + np.deg2rad(sigma_b_deg) * noise[:, 1])))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=30)
    ap.add_argument("--scans", type=int, default=800)
    ap.add_argument("--seed", type=int, default=20261026)
    ap.add_argument("--out", default="accuracy-sweep.json")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    runs = [make_run(rng, args.scans) for _ in range(args.runs)]

    filters = (("EKF", sb.run_ekf), ("UKF", sb.run_ukf),
               ("CKF", sb.run_ckf), ("SCKF", sb.run_sckf))
    out = {"sigmas_deg": list(SIGMAS_DEG), "runs": args.runs,
           "scans": args.scans, "seed": args.seed,
           "substeps": sb.SUBSTEPS, "dt": sb.DT,
           "sigma_r": sb.SIGMA_R, "p0": sb.P0,
           "thesis_deg": THESIS_DEG, "stress_deg": STRESS_DEG,
           "summary": {name: {"pos_rmse": [], "vel_rmse": [], "time_s_per_track": []}
                       for name, _ in filters},
           "curves_thesis": {}, "curves_stress": {}}

    for sigma_b in SIGMAS_DEG:
        print(f"bearing sigma {sigma_b:g} deg")
        sb.SIGMA_B = np.deg2rad(sigma_b)
        sb.R = np.diag([sb.SIGMA_R ** 2, sb.SIGMA_B ** 2])
        data = [(s, measurements(s, n, sigma_b)) for s, n in runs]
        for name, fn in filters:
            t0 = time.perf_counter()
            est = [fn(z) for _, z in data]
            elapsed = time.perf_counter() - t0
            pos = np.array([np.hypot(e[:, 0] - s[:, 0], e[:, 1] - s[:, 1])
                            for e, (s, _) in zip(est, data)])
            vel = np.array([np.hypot(e[:, 2] - s[:, 2], e[:, 3] - s[:, 3])
                            for e, (s, _) in zip(est, data)])
            rmse_pos = np.sqrt(np.nanmean(pos ** 2, axis=0))
            rmse_vel = np.sqrt(np.nanmean(vel ** 2, axis=0))
            out["summary"][name]["pos_rmse"].append(round(float(rmse_pos[300:].mean()), 4))
            out["summary"][name]["vel_rmse"].append(round(float(rmse_vel[300:].mean()), 4))
            out["summary"][name]["time_s_per_track"].append(round(elapsed / args.runs, 4))
            if sigma_b in (THESIS_DEG, STRESS_DEG):
                key = "curves_thesis" if sigma_b == THESIS_DEG else "curves_stress"
                out[key][name] = {
                    "rmse_pos": [round(float(v), 4) for v in rmse_pos],
                    "rmse_vel": [round(float(v), 4) for v in rmse_vel],
                }
            print(f"  {name:4s} pos {rmse_pos[300:].mean():.3f}  "
                  f"vel {rmse_vel[300:].mean():.3f}  {elapsed / args.runs:.3f} s/track")

    path = Path(args.out)
    path.write_text(json.dumps(out, indent=2))
    print("wrote", path)


if __name__ == "__main__":
    main()
