#import "../data.typ": data

= Experimental design

Four sweeps vary $sigma_theta$, $sigma_r$, $q_p$, and $q_v$ separately. Within a process-noise sweep, one standard deviation is applied symmetrically to the two spatial axes; the other process block and both radar noises stay nominal. Every filter receives the true process and polar-noise parameters; KF-CV still approximates the converted Cartesian covariance as described in Section 3.1. This is a study of *matched noise intensity*, not unknown covariance estimation or robustness to incorrect assumed $Q$ and $R$.

#figure(
  table(
    columns: (1.35fr, 1fr, 3fr),
    align: left,
    inset: (x: 5pt, y: 4pt),
    stroke: 0.35pt + rgb("cbd1d7"),
    table.header([*Parameter*], [*Nominal*], [*Sweep values*]),
    [$sigma_theta$ (degrees)], [0.5], [0.5, 2, 5, 10, 20, 30],
    [$sigma_r$ (m)], [0.01], [0.01, 0.02, 0.05, 0.1, 0.2, 0.5],
    [$q_p$ (m)], [0.01], [0.0025, 0.005, 0.01, 0.02, 0.04, 0.08],
    [$q_v$ (m/s)], [0.01], [0.0025, 0.005, 0.01, 0.02, 0.04, 0.08],
  ),
  kind: table,
  caption: [One standard deviation varies at a time. Process parameters are SDs of discrete substep increments, not diffusion intensities. All other entries retain their nominal values. Units follow Section 2.1.],
) <tab-parameters>

Each condition uses #data.runs trajectories and #data.scans scans with seed #data.seed. True initial states are drawn uniformly from $[-0.5,0.5]^4$; every filter starts from $hat(bold(x))_0=(1,1,1,1)^T$ and $P_0=10I_4$. The same initial states and standardized Gaussian process and measurement draws are reused across conditions. Measurement sweeps therefore preserve truth; process sweeps necessarily change trajectories, but preserve the underlying random draws. Within each condition, all methods receive the same observations. The nominal condition is shared across sweeps, yielding 21 unique configurations and 24 displayed points.

For trajectory $i$, let $bold(e)_(p,k)^(i)$ denote its two-dimensional position error at radar scan $k$. We compute

$ "RMSE"_p(k) = sqrt(1/N sum_(i=1)^N norm(bold(e)_(p,k)^(i))^2), quad
  overline("RMSE")_p = 1/(K-B) sum_(k=B+1)^K "RMSE"_p(k). $ <eq-metric>

Velocity uses the same construction. Here $N=30$, $K=800$, and $B=300$. Thus summary results average per-scan RMSE over scans 301-800, corresponding to 15.05-40 s under the display convention. They are not obtained by pooling time and trajectory errors before taking a square root. A failed or non-finite track invalidates the whole method-condition pair; no survivor-only averages are used. All methods completed every track in every condition.

Elapsed filtering time includes the baseline's conversion and excludes simulation and plotting. It is averaged over the tracks in one batch, not over repeated timing experiments. The execution environment was #data.environment. Eleven numerical tests cover conversion moments, process covariance propagation, parameter isolation, paired random draws, and failure handling. The current dataset and simulation source hashes are stored together in `noise-sensitivity.json`.
