= State and observation models

== Discrete ship dynamics

Let $j$ index integration substeps and let $k$ index radar scans. The state is $bold(x)_j = (bold(p)_j^T, bold(v)_j^T)^T$, with two-dimensional position $bold(p)_j$ and velocity $bold(v)_j$. The implementation advances

$ bold(p)_(j+1) &= bold(p)_j + delta bold(v)_j + q_p bold(epsilon)_(p,j), \
  bold(v)_(j+1) &= bold(v)_j + bold(c)(bold(p)_j, bold(v)_j) + q_v bold(epsilon)_(v,j). $ <eq-dynamics>

The independent noise vectors have standard normal distributions. The deterministic turning increment is

$ bold(c)(bold(p), bold(v)) = cases(
  -lambda bold(p) / norm(bold(p)), & norm(bold(p)) >= r_s " and " bold(p)^T bold(v) >= 0,
  bold(0), & "otherwise".
) $ <eq-turn>

Here $r_s=5$ and $lambda=2$. The turning term is a *discrete velocity increment*, exactly as coded; it is not multiplied by $delta$ again. The additive substep covariance is

$ Q = op("diag")(q_p^2, q_p^2, q_v^2, q_v^2). $ <eq-Q>

We use $delta=0.01$ and five substeps per scan, giving a radar interval $Delta=0.05$. The thesis uses normalized space and time units. To retain the existing plot labels, this project assigns one space unit to 1 m and one time unit to 1 s. These are display conventions, not an empirically calibrated vessel model; comparisons are unchanged by retaining normalized units.

#pagebreak()
== Radar observations

A stationary radar at the origin observes $bold(x)_(5k)$:

$ bold(z)_k = h(bold(x)_(5k)) + bold(nu)_k, quad
  h(bold(x)) = vec(sqrt(p_x^2+p_y^2), op("atan2")(p_y,p_x)), $ <eq-radar>
$ bold(nu)_k ~ cal(N)(bold(0), R), quad R = op("diag")(sigma_r^2, sigma_theta^2). $ <eq-R>

Measurement noise, process noise, and initial states are independent. Bearing standard deviations are specified in degrees and converted to radians before constructing $R$. Bearing residuals are wrapped to $[-pi,pi)$. The additive Gaussian range model is retained without clipping, so near the origin a noisy range can be negative.
