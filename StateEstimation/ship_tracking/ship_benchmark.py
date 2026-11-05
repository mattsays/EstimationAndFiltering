"""Ship-tracking benchmark from Arasaratnam's CKF thesis, section 6.1.

The scenario, parameters and metrics are taken from the thesis so the comparison
can be checked against a published setup:

  x1' = x1 + dt*x3 + q1*v1
  x2' = x2 + dt*x4 + q1*v2
  x3' = x3 + f1(x) + q2*v3
  x4' = x4 + f2(x) + q2*v4

with the turning force f = -lambda * (x1, x2) / |x| acting only outside the shore
radius r and only while the ship moves away from the origin.  The radar at the
origin measures range and bearing.

The project adds a constant-velocity KF with converted radar measurements to
EKF, UKF, CKF and SCKF. This KF is a project baseline, not a thesis result.
The thesis
also reports a CDKF and a particle filter, which are outside the scope here, and
omits the EKF/UKF curves because those filters diverged.

Run:  python3 ship_benchmark.py [--runs N] [--scans N] [--seed N]
"""

import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np

# --- scenario parameters (thesis, section 6.1) -----------------------------
DELTA = 0.05              # radar measurement interval
SUBSTEPS = 5              # predictions between two measurements
DT = DELTA / SUBSTEPS     # integration step of the ship model
R_SHORE = 5.0             # shore radius
LAMBDA = 2.0              # strength of the turning force
Q1 = 0.01                 # position process-noise intensity
Q2 = 0.01                 # velocity process-noise intensity
SIGMA_R = 0.01            # radar range standard deviation
SIGMA_B = np.deg2rad(0.5) # radar bearing standard deviation
P0 = 10.0                 # initial covariance, 10 * I
X0_HAT = np.array([1., 1., 1., 1.])

Q = np.diag([Q1 ** 2, Q1 ** 2, Q2 ** 2, Q2 ** 2])
R = np.diag([SIGMA_R ** 2, SIGMA_B ** 2])

KF_DESCRIPTION = {
    "label": "KF-CV (converted measurements)",
    "motion": "constant velocity; no nonlinear shore-turn force",
    "measurement": "exp(sigma_b^2/2)*r*[cos(b),sin(b)]; unbiased conversion",
    "covariance": "exact conversion moments evaluated at predicted position (plug-in approximation)",
    "process_noise": "same substep Q as nonlinear filters; no separate tuning",
}


def wrap(angle):
    """Wrap an angular difference to [-pi, pi)."""
    return (angle + np.pi) % (2 * np.pi) - np.pi


def circular_mean(angles, weights):
    """Weighted mean direction of angles, not their arithmetic mean."""
    return np.arctan2(np.sum(weights * np.sin(angles)),
                      np.sum(weights * np.cos(angles)))


def f_batch(X):
    """Propagate one integration step for a batch of states, X shape (4, N)."""
    px, py, vx, vy = X[0], X[1], X[2], X[3]
    r = np.hypot(px, py)
    outward = px * vx + py * vy >= 0.
    active = (r >= R_SHORE) & outward & (r > 1e-12)
    inv_r = np.zeros_like(r)
    np.divide(1., r, out=inv_r, where=active)
    Y = np.empty_like(X)
    Y[0] = px + DT * vx
    Y[1] = py + DT * vy
    Y[2] = vx - LAMBDA * px * inv_r
    Y[3] = vy - LAMBDA * py * inv_r
    return Y


def jacobian_f(x):
    """Jacobian of one integration step, state shape (4,)."""
    px, py, vx, vy = x
    r = np.hypot(px, py)
    active = (r >= R_SHORE) and (px * vx + py * vy >= 0.) and (r > 1e-12)
    F = np.eye(4)
    F[0, 2] = DT
    F[1, 3] = DT
    if active:
        r3 = r ** 3
        F[2, 0] = -LAMBDA * py ** 2 / r3
        F[2, 1] = LAMBDA * px * py / r3
        F[3, 0] = LAMBDA * px * py / r3
        F[3, 1] = -LAMBDA * px ** 2 / r3
    return F


def h_batch(X):
    """Radar measurement for a batch of states, X shape (4, N)."""
    px, py = X[0], X[1]
    return np.vstack((np.hypot(px, py), np.arctan2(py, px)))


def jacobian_h(x):
    px, py = x[0], x[1]
    r2 = px ** 2 + py ** 2
    r = np.sqrt(r2)
    H = np.zeros((2, 4))
    H[0, 0] = px / r
    H[0, 1] = py / r
    H[1, 0] = -py / r2
    H[1, 1] = px / r2
    return H


def chol_psd(P):
    """Cholesky factor with a small jitter, so a nearly singular P still works."""
    P = (P + P.T) / 2
    try:
        return np.linalg.cholesky(P)
    except np.linalg.LinAlgError:
        jitter = 1e-12 * max(1., np.trace(P))
        return np.linalg.cholesky(P + jitter * np.eye(4))


def sigma_points(x, P, kappa):
    """Symmetric sigma points and weights for the UKF (thesis, appendix B)."""
    n = 4
    L = chol_psd((n + kappa) * P)
    X = np.column_stack([x] + [x + L[:, i] for i in range(n)]
                        + [x - L[:, i] for i in range(n)])
    w0 = kappa / (n + kappa)
    wi = 1. / (2 * (n + kappa))
    wm = np.full(2 * n + 1, wi)
    wm[0] = w0
    wc = wm.copy()
    wc[0] += 2.  # beta = 2, alpha = 1
    return X, wm, wc


def cubature_points(x, P):
    """2n equally weighted cubature points."""
    n = 4
    L = chol_psd(n * P)
    X = np.column_stack([x + L[:, i] for i in range(n)]
                        + [x - L[:, i] for i in range(n)])
    w = np.full(2 * n, 1. / (2 * n))
    return X, w


def linear_cv_model():
    """Aggregate SUBSTEPS linear predictions and their process covariance."""
    F = np.eye(4)
    F[0, 2] = F[1, 3] = DT
    A = np.eye(4)
    Q_scan = np.zeros((4, 4))
    for _ in range(SUBSTEPS):
        A = F @ A
        Q_scan = F @ Q_scan @ F.T + Q
    return A, Q_scan


def converted_radar_measurement(z):
    """Unbiased position observation for independent Gaussian polar errors."""
    r, bearing = z
    return np.exp(SIGMA_B ** 2 / 2.) * r * np.array([
        np.cos(bearing), np.sin(bearing)])


def converted_radar_covariance(position):
    """Conversion covariance at a position; the KF uses its prediction, not truth.

    Radial/tangential moments are exact at a fixed true position. Substituting
    the predicted position is an approximation, not a consistency guarantee.
    """
    radius = np.hypot(*position)
    angle = np.arctan2(position[1], position[0])
    s2 = SIGMA_B ** 2
    radial = (SIGMA_R ** 2 * np.cosh(s2)
              + radius ** 2 * 2. * np.sinh(s2 / 2.) ** 2)
    tangent = (radius ** 2 + SIGMA_R ** 2) * np.sinh(s2)
    c, s = np.cos(angle), np.sin(angle)
    rotation = np.array([[c, -s], [s, c]])
    return (rotation * np.array([radial, tangent])) @ rotation.T


def run_kf(measurements):
    """Linear constant-velocity KF with unbiased converted measurements.

    F and H are fixed. R_cart varies with predicted position. Converted errors
    are non-Gaussian; this is an approximate radar tracker, not an exact MMSE KF.
    """
    A, Q_scan = linear_cv_model()
    H = np.array([[1., 0., 0., 0.], [0., 1., 0., 0.]])
    x = X0_HAT.copy()
    P = P0 * np.eye(4)
    out = np.empty((len(measurements), 4))
    for k, z in enumerate(measurements):
        x = A @ x
        P = A @ P @ A.T + Q_scan
        R_cart = converted_radar_covariance(x[:2])
        S = H @ P @ H.T + R_cart
        K = np.linalg.solve(S, H @ P).T
        x = x + K @ (converted_radar_measurement(z) - H @ x)
        I_KH = np.eye(4) - K @ H
        P = I_KH @ P @ I_KH.T + K @ R_cart @ K.T
        P = (P + P.T) / 2.
        out[k] = x
    return out


def run_ekf(measurements):
    x = X0_HAT.copy()
    P = P0 * np.eye(4)
    out = np.empty((len(measurements), 4))
    for k, z in enumerate(measurements):
        for _ in range(SUBSTEPS):
            F = jacobian_f(x)
            x = f_batch(x[:, None])[:, 0]
            P = F @ P @ F.T + Q
        H = jacobian_h(x)
        S = H @ P @ H.T + R
        K = P @ H.T @ np.linalg.inv(S)
        innov = z - h_batch(x[:, None])[:, 0]
        innov[1] = wrap(innov[1])
        x = x + K @ innov
        I_KH = np.eye(4) - K @ H
        P = I_KH @ P @ I_KH.T + K @ R @ K.T
        P = (P + P.T) / 2
        out[k] = x
    return out


def run_ukf(measurements, kappa=1.):
    """UKF with the course parameters alpha=1, beta=2, kappa=1.

    With alpha=1 the beta correction only enters the covariance weights:
    Wc0 = Wm0 + 2.
    """
    x = X0_HAT.copy()
    P = P0 * np.eye(4)
    out = np.empty((len(measurements), 4))
    for k, z in enumerate(measurements):
        for _ in range(SUBSTEPS):
            X, wm, wc = sigma_points(x, P, kappa)
            Y = f_batch(X)
            x = Y @ wm
            d = Y - x[:, None]
            P = (d * wc) @ d.T + Q
            P = (P + P.T) / 2
        X, wm, wc = sigma_points(x, P, kappa)
        Z = h_batch(X)
        z_pred = Z @ wm
        z_pred[1] = circular_mean(Z[1], wm)
        dx = X - x[:, None]
        dz = Z - z_pred[:, None]
        dz[1] = wrap(dz[1])
        Pzz = (dz * wc) @ dz.T + R
        Pxz = (dx * wc) @ dz.T
        K = Pxz @ np.linalg.inv(Pzz)
        innov = z - z_pred
        innov[1] = wrap(innov[1])
        x = x + K @ innov
        P = P - K @ Pzz @ K.T
        P = (P + P.T) / 2
        out[k] = x
    return out


def run_ckf(measurements):
    x = X0_HAT.copy()
    P = P0 * np.eye(4)
    out = np.empty((len(measurements), 4))
    for k, z in enumerate(measurements):
        for _ in range(SUBSTEPS):
            X, w = cubature_points(x, P)
            Y = f_batch(X)
            x = Y @ w
            d = Y - x[:, None]
            P = (d * w) @ d.T + Q
            P = (P + P.T) / 2
        X, w = cubature_points(x, P)
        Z = h_batch(X)
        z_pred = Z @ w
        z_pred[1] = circular_mean(Z[1], w)
        dx = X - x[:, None]
        dz = Z - z_pred[:, None]
        dz[1] = wrap(dz[1])
        Pzz = (dz * w) @ dz.T + R
        Pxz = (dx * w) @ dz.T
        K = Pxz @ np.linalg.inv(Pzz)
        innov = z - z_pred
        innov[1] = wrap(innov[1])
        x = x + K @ innov
        P = P - K @ Pzz @ K.T
        P = (P + P.T) / 2
        out[k] = x
    return out


def qr_sqrt(M):
    """Lower-triangular S with S S^T = M M^T (M has at least as many rows as columns)."""
    _, R = np.linalg.qr(M, mode="reduced")
    return R.T


def run_sckf(measurements):
    """Square-root cubature Kalman filter (Arasaratnam-Haykin, Table II).

    Same cubature rule as run_ckf, but the covariance is carried as a
    lower-triangular square root and updated with QR factorisations.
    """
    x = X0_HAT.copy()
    S = np.sqrt(P0) * np.eye(4)
    Lq = np.diag([Q1, Q1, Q2, Q2])
    Lr = np.diag([SIGMA_R, SIGMA_B])
    w = np.full(8, 1. / 8.)
    out = np.empty((len(measurements), 4))
    for k, z in enumerate(measurements):
        for _ in range(SUBSTEPS):
            X = np.column_stack([x + 2. * S[:, i] for i in range(4)]
                                + [x - 2. * S[:, i] for i in range(4)])
            Y = f_batch(X)
            x = Y @ w
            D = (Y - x[:, None]) / np.sqrt(8.)
            S = qr_sqrt(np.hstack([D, Lq]).T)
        X = np.column_stack([x + 2. * S[:, i] for i in range(4)]
                            + [x - 2. * S[:, i] for i in range(4)])
        Z = h_batch(X)
        z_pred = Z @ w
        z_pred[1] = circular_mean(Z[1], w)
        Dx = (X - x[:, None]) / np.sqrt(8.)
        Dz = Z - z_pred[:, None]
        Dz[1] = wrap(Dz[1])          # wrap the angle before scaling the residual
        Dz /= np.sqrt(8.)
        Szz = qr_sqrt(np.hstack([Dz, Lr]).T)
        W = np.linalg.solve(Szz, Dz)
        K0 = Dx @ W.T
        K = np.linalg.solve(Szz.T, K0.T).T
        innov = z - z_pred
        innov[1] = wrap(innov[1])
        x = x + K @ innov
        D = Dx - K @ Dz
        E = K @ Lr
        S = qr_sqrt(np.hstack([D, E]).T)
        out[k] = x
    return out


def simulate_run(rng, scans):
    """One true ship trajectory and its radar measurements."""
    x = rng.uniform(-.5, .5, 4)
    states = np.empty((scans, 4))
    measurements = np.empty((scans, 2))
    noise_std = np.array([Q1, Q1, Q2, Q2])
    for k in range(scans):
        for _ in range(SUBSTEPS):
            x = f_batch(x[:, None])[:, 0] + noise_std * rng.standard_normal(4)
        states[k] = x
        r = np.hypot(x[0], x[1])
        b = np.arctan2(x[1], x[0])
        measurements[k] = (r + SIGMA_R * rng.standard_normal(),
                           wrap(b + SIGMA_B * rng.standard_normal()))
    return states, measurements


def main():
    global DT, SIGMA_B, SIGMA_R, R, P0
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=50)
    ap.add_argument("--scans", type=int, default=800)
    ap.add_argument("--seed", type=int, default=20261026)
    ap.add_argument("--burn-in", type=int, default=300)
    ap.add_argument("--out", default="ship-results-with-kf.json")
    ap.add_argument("--dt", type=float, default=None,
                    help="integration step; the thesis lists 0.05")
    ap.add_argument("--sigma-b", type=float, default=0.5,
                    help="bearing standard deviation in degrees (thesis: 0.5)")
    ap.add_argument("--sigma-r", type=float, default=SIGMA_R,
                    help="range standard deviation (thesis: 0.01)")
    ap.add_argument("--p0", type=float, default=P0,
                    help="initial covariance scale (thesis: 10)")
    args = ap.parse_args()
    if args.runs < 1 or not 0 <= args.burn_in < args.scans:
        ap.error("runs must be positive and 0 <= burn-in < scans")
    if args.sigma_r <= 0 or args.sigma_b <= 0 or args.p0 <= 0 or (args.dt is not None and args.dt <= 0):
        ap.error("noise standard deviations, p0 and dt must be positive")
    if args.dt is not None:
        DT = args.dt
    SIGMA_B = np.deg2rad(args.sigma_b)
    SIGMA_R = args.sigma_r
    R = np.diag([SIGMA_R ** 2, SIGMA_B ** 2])
    P0 = args.p0

    rng = np.random.default_rng(args.seed)
    data = [simulate_run(rng, args.scans) for _ in range(args.runs)]

    timings = {}
    estimates = {}
    for name, fn in FILTERS:
        t0 = time.perf_counter()
        estimates[name] = [fn(m) for _, m in data]
        timings[name] = time.perf_counter() - t0

    print("runs", args.runs, "scans", args.scans, "dt", DT)
    summary = {"runs": args.runs, "scans": args.scans, "dt": DT,
               "substeps": SUBSTEPS, "seed": args.seed,
               "burn_in": args.burn_in, "radar_interval": DT * SUBSTEPS,
               "baseline": KF_DESCRIPTION,
               "rmse_policy": "all paired runs; non-finite estimates fail the experiment",
               "ekf_jacobian": "evaluated at the pre-propagation state",
               "sigma_r": SIGMA_R, "sigma_b_deg": args.sigma_b, "p0": P0,
               "environment": f"{platform.system()} {platform.machine()}, "
                              f"Python {platform.python_version()}, NumPy {np.__version__}",
               "method": {}, "curves": {}}
    for name in estimates:
        pos = np.array([np.hypot(e[:, 0] - s[:, 0], e[:, 1] - s[:, 1])
                        for e, (s, _) in zip(estimates[name], data)])
        vel = np.array([np.hypot(e[:, 2] - s[:, 2], e[:, 3] - s[:, 3])
                        for e, (s, _) in zip(estimates[name], data)])
        if not np.isfinite(estimates[name]).all():
            raise ValueError(f"{name}: non-finite estimate; no runs silently excluded")
        finite = np.isfinite(pos).all(axis=1)
        rmse_pos = np.sqrt(np.mean(pos ** 2, axis=0))
        rmse_vel = np.sqrt(np.mean(vel ** 2, axis=0))
        steady_pos = rmse_pos[args.burn_in:]
        steady_vel = rmse_vel[args.burn_in:]
        summary["curves"][name] = {
            "rmse_pos": [round(float(v), 4) for v in rmse_pos],
            "rmse_vel": [round(float(v), 4) for v in rmse_vel],
        }
        summary["method"][name] = {
            "time_s_per_track": round(timings[name] / args.runs, 4),
            "finite_runs": int(finite.sum()),
            "mean_pos_after_burn_in": round(float(np.mean(steady_pos)), 4),
            "mean_vel_after_burn_in": round(float(np.mean(steady_vel)), 4),
            "p95_pos": round(float(np.percentile(steady_pos, 95)), 4),
            "max_pos": round(float(np.max(rmse_pos)), 4),
        }
        print(f"{name}: finite {finite.sum()}/{args.runs}, "
              f"RMSE pos k>={args.burn_in} mean {np.mean(steady_pos):.3f} "
              f"p95 {np.percentile(steady_pos, 95):.3f} "
              f"max {rmse_pos.max():.2f}, "
              f"vel mean {np.mean(steady_vel):.3f}, "
              f"per-track {timings[name] / args.runs:.3f} s")
    out = Path(args.out)
    out.write_text(json.dumps(summary, indent=2, allow_nan=False))
    print("wrote", out)


FILTERS = (("KF", run_kf), ("EKF", run_ekf), ("UKF", run_ukf),
           ("CKF", run_ckf), ("SCKF", run_sckf))


if __name__ == "__main__":
    main()
