= Estimation methods

== Linear constant-velocity baseline

The KF-CV baseline replaces the turning increment by zero. For the state order $[p_x,p_y,v_x,v_y]^T$, its substep transition and Cartesian observation matrices are

$ F = mat(1,0,delta,0; 0,1,0,delta; 0,0,1,0; 0,0,0,1), quad
  H_c = mat(1,0,0,0; 0,1,0,0). $ <eq-kf-matrices>

Five substeps are aggregated exactly: $A=F^5$ and $Q_Delta=sum_(ell=0)^4 F^ell Q (F^ell)^T$. The prediction is $hat(bold(x))^-_k=A hat(bold(x))^+_(k-1)$ and $P^-_k=A P^+_(k-1) A^T+Q_Delta$.

Raw Cartesian conversion is biased because $bb(E)[cos(nu_theta)]=exp(-sigma_theta^2/2)$. With $a=sigma_theta^2$, we use the multiplicatively unbiased observation

$ bold(z)_(c,k) = exp(a/2) r_(m,k) vec(cos(theta_(m,k)), sin(theta_(m,k))). $ <eq-conversion>

At a fixed true range $rho$, its radial and tangential error variances are

$ d_r &= (rho^2+sigma_r^2) cosh(a)-rho^2, \
  d_t &= (rho^2+sigma_r^2) sinh(a). $ <eq-conversion-cov>

These expressions follow from the Gaussian sine and cosine moments. Rotating $op("diag")(d_r,d_t)$ into Cartesian axes gives the covariance at a fixed true position. Since truth is unavailable, the implementation substitutes its predicted position. This is a plug-in approximation, not the full statistically consistent converted-measurement algorithm of @lerro1993 or @spitzmiller2010. Although $F$ and $H_c$ are fixed, the converted covariance is prediction-dependent, and converted errors are non-Gaussian. Thus KF-CV is a linear-model baseline with an approximate radar interface, not an exact Gaussian solution to @eq-radar.

== Common correction and extended Kalman filter

The nonlinear methods maintain a predicted state, predicted observation, innovation covariance $S_k$, and state-observation cross-covariance $C_k$. Their correction uses

$ K_k &= C_k S_k^(-1), \
  hat(bold(x))^+_k &= hat(bold(x))^-_k + K_k (bold(z)_k-hat(bold(z))_k), \
  P^+_k &= P^-_k-K_k S_k K_k^T. $ <eq-correction>

For KF-CV the observation and covariance are Cartesian. For the nonlinear filters, the bearing component of the innovation is wrapped. The implementation uses the Joseph covariance form for KF-CV and EKF.

The EKF propagates $hat(bold(x))_(j+1)=f(hat(bold(x))_j)$ and $P_(j+1)=F_j P_j F_j^T+Q$, evaluating the dynamics Jacobian at the state *before* propagation. For nonzero range, the observation Jacobian is

$ H_k = mat(p_x/rho, p_y/rho, 0, 0; -p_y/rho^2, p_x/rho^2, 0, 0). $ <eq-H>

On a fixed active branch, $F_j=mat(I_2,delta I_2; J_c,I_2)$ with $J_c=-lambda(I_2/rho-bold(p)bold(p)^T/rho^3)$; on the inactive branch $J_c=0$. The switching surface is not differentiable, so local Gaussian approximations are especially restrictive near turns.

== Unscented, cubature, and square-root filters

The implemented UKF uses $n=4$, $alpha=1$, $beta=2$, and $kappa=1$, so $lambda_U=alpha^2(n+kappa)-n=1$. It places $2n+1=9$ sigma points at the mean and at symmetric offsets given by columns of $sqrt((n+lambda_U)P)$. The mean weights are $W_0^m=0.2$ and $W_i^m=0.1$ for outer points; the central covariance weight is $W_0^c=2.2$. Points are transformed through the actual nonlinear maps, then recombined @julier2004.

For the CKF, if $P=L L^T$, the eight points and weights are

$ bold(chi)_(i,plus.minus) = hat(bold(x)) plus.minus sqrt(n) L bold(e)_i, quad
  w_(i,plus.minus)=1/(2n), quad i=1,dots,n. $ <eq-ckf>

For a transformation $g$, their weighted mean and centered outer products approximate its mean and covariance; additive process or measurement covariance is then included. The CKF and its square-root variant use this same cubature rule @arasaratnam2009. SCKF carries covariance factors and uses QR factorizations and triangular solves rather than explicit covariance subtraction. It changes numerical representation, not the underlying integration rule.

Both UKF and CKF regenerate points after adding process noise. Their predicted bearing uses a weighted circular mean, $op("atan2")(sum_i w_i sin(theta_i),sum_i w_i cos(theta_i))$. Equal positive CKF weights do not establish exact nonlinear moments, strict positive definiteness in every numerical situation, or universal accuracy superiority.
