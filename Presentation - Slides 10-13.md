---
date: 21/10/26
type: presentation-draft
status: content only (layout and style come later)
---
# Presentation draft: slides 10-13

This file is the **content** draft for my part of the presentation. It only covers the
items 10, 11, 12 and 13 of the structure in `E&F_presentation.md` (the comparison of the
filter family, the computational trade-off, the limits of the Kalman family and the
particle filter answer). Layout, colours and graphics are deliberately left out: they
come in a later pass.

Everything here is derived from the notes already in the vault:

A first HTML rendering of these slides, to be able to see how they are structured, is in
`deck-draft.html` in the same folder: open it in a browser, the arrow keys move from one
slide to the next.

| Source note | What I take from it |
| --- | --- |
| `Notes/3. State Estimation in Discrete-time Linear Dynamic Systems.md` | the KF, the LMMSE correction engine, the Joseph form |
| `Notes/5. State Estimation for Nonlinear Systems.md` | EKF, unscented transform, EKF vs UF table, the `f(x) = x^2` example |
| `Notes/6. Cubature Kalman Filter.md` | cubature rule, UT vs CKF table, `kappa = 0` result, consistency metrics (NEES, NIS), failure modes |

---

## 0. Conventions used in this document

- **Slide numbering**: `S1 ... S8` are *my* slides. The "draft item" column says which
  point of the shared structure each slide answers.
- **Notation**: same as the course notes, so nothing has to be re-learned by the audience.
  $\hat{x}_{k|k}$ is the filtered estimate, $P_{k|k}$ its MSE, $z^k = \{z_i, i \le k\}$ the
  measurements up to time $k$, $n = \dim(x)$, $m = \dim(z)$.
- **Transpose**: always `^{T}`.
- **Sigma points**: $\chi_i$ with weights $w_i$, tuning parameter $\kappa$ (the course
  convention, $n + \kappa = 3$ for a Gaussian state). The $(\alpha, \beta, \kappa)$
  parametrisation of the draft is the scaled variant of the same thing, see S2.
- **Slide writing rules** (to apply in the layout pass): one message per slide, the point
  of the slide written as the title itself, at most two bullets or one table, and the
  sentence that must stay in the audience's head in the takeaway box at the bottom.
- **Type sizes for projection** (already applied in `deck-draft.html`): title 50 px, body
  and table 22 to 27 px, formulas 30 px. Nothing below 19 px anywhere, because the room
  is not the laptop.
- **The slide is not the notes**: this document keeps the full argument, the deck keeps
  only what is read from the back of the room.

## 1. Slide map

| Slide | Draft item | Title | Purpose | Time |
| --- | --- | --- | --- | --- |
| S0 | intro | Let's compare the filters we have seen | the opening slide of my part | 0.5 min |
| S1 | 10 | One model, three ways to the same filter | the schema of the draft, animated in 4 steps | 1.5 min |
| S2 | 10 | The four filters side by side | the comparison table | 2 min |
| S3 | 11 | What each filter actually costs | cost accounting | 1.5 min |
| S4 | 11 | First order versus third order | accuracy, with the worked example | 2 min |
| S5 | 11 | The trade-off in one picture | the figure that needs the simulation | 1 min |
| S6 | 12 | What no Kalman filter can do | Gaussianity, multimodality, inconsistency | 2 min |
| S7 | 13 | Beyond the Gaussian | the nonparametric answer, as a pointer | 1 min |
| S8 | 12, 13 | Where the family ends | closing map and takeaways | 1 min |

Total: about 12 minutes. If the slot is shorter, drop S5 (the figure is evidence, the
other slides carry the argument) and compress S3 into S4.

---

## 2. Slide content

### S0. Let's compare the filters we have seen

**Opening slide of my part.** No content of its own: it hands over from the UKF and CKF
part to the comparison.

**On the slide**

The central text, large, with the second line highlighted:

*Now, let's look at the*
***non linearity big picture***

And, below it, the sentence that frames the whole section:

> Nonlinearity breaks exactly one thing: the mean and the covariance stop propagating.
> Every filter we have seen is a different way of getting them back.

**Speaker notes**

- Half a minute. The job of this slide is to signal the change of perspective: the two
  previous parts introduced the filters one at a time, this part looks at all of them
  together.
- The agenda of the section is said out loud, not written: the comparison (item 10), the
  cost and the accuracy (item 11), the limits and what comes after (items 12 and 13).
  Then move on.

---

### S1. One model, three routes to the same filter

**Draft item 10.** This is the schema already sketched in the shared draft, with the
"KF" branch added and the wording fixed.

**On the slide**

Title: *One model, three ways to the same filter.*

The slide is **animated in six steps**, one click each:

1. **step 1**: the model alone, in the centre, with the label "Nonlinear model" above it:
   $$x_{k+1} = f_k(x_k) + w_k, \qquad z_k = h_k(x_k) + v_k$$
2. **step 2**: the model moves up and shrinks to its place at the top of the diagram;
3. **step 3**: **EKF** spawns, with its arrow from the model (Taylor, 1st order);
4. **step 4**: **UKF** spawns ($2n+1$ sigma points);
5. **step 5**: **CKF** spawns ($2n$ cubature points);
6. **step 6**: the three arrows converge on **(mean, covariance)**, which feeds the
   **LMMSE correction engine (standard KF)**, output $x(k+1|k+1)$, $P(k+1|k+1)$.

No text on the slide other than the labels of the boxes: the sentence that closes the
section is spoken, not written.

**Speaker notes**

- Open by recalling the question the whole presentation has been building towards: the
  nonlinear map destroys the closed-form propagation of the mean and the covariance that
  made the Kalman filter exact. Every filter we have seen is an *answer to the same
  question*: find $\mathbb{E}[f(x)]$ and $\operatorname{cov}(f(x))$ when $f$ is nonlinear.
- The four clicks are the argument: the model is common, the three ways are three
  different *approximations of the same integral*, and the block at the bottom is chapter 3
  of the course, untouched. Say the sentence about the correction engine out loud while
  the engine is on screen: when we compare the filters later, we are comparing the top
  block only.
- This slide is the natural place to repeat the Julier and Uhlmann quote that opens the
  UKF part of the presentation, and to say that the CKF is the UKF with $\kappa = 0$ (the
  one-parameter-family result from the CKF note). The audience should leave this slide
  knowing the family is one family, not four unrelated algorithms.

---

### S2. The four filters side by side

**Draft item 10.** The comparison table, the core deliverable of this item.

**On the slide**

Title: *The four filters side by side.*

Three boxes side by side: the row labels on the left, then the **Linear** group (the KF)
and the **Non-Linear** group (EKF, UKF, CKF).

|  | **KF** | **EKF** | **UKF** | **CKF** |
| --- | --- | --- | --- | --- |
| Derivatives | no | yes | no | no |
| Work per cycle | matrix products | 2 Jacobians | $2n+1$ points | $2n$ points |
| Accuracy | exact | 1st order | 3rd order | 3rd order |
| HyperParameters | $Q$, $R$ | $Q$, $R$ | $Q$, $R$, $\kappa$ | $Q$, $R$ |
| P stays positive definite | yes | yes | not if $\kappa < 0$ | yes |

The slide is **animated in six steps**: the three boxes and their headers are there from
the start, then the five rows appear one at a time, in this order: Derivatives, Work per
cycle, Accuracy, HyperParameters, P stays positive definite.

Two rows of the first draft of this slide are gone: the row "Nonlinearity" (redundant,
the Linear and Non-Linear headers say it already) and the conclusion box at the bottom
($\kappa = 0$ turns the sigma points into the cubature points), which is said out loud
instead.

**Speaker notes**

- Read the table **by rows**, not column by column: it is the answer to "what do I lose
  and what do I gain by leaving the EKF?".
- Row "Work per cycle": the EKF row says 0 points but 2 Jacobians. This is the row that
  hides the real cost of the EKF: a Jacobian is not free, it must be derived by hand (or
  obtained by automatic differentiation), and it must be correct at every step.
- Row "Accuracy": be precise, this is about the *propagated distribution*, not about the
  whole estimator. Both UKF and CKF reproduce the moments of a Gaussian input up to third
  order; the EKF reproduces them to first order only.
- Row "HyperParameters": this is the row that motivates the whole CKF part of the
  presentation. The UKF has a free parameter $\kappa$ whose only job is to place the
  points, and the popular choice $n + \kappa = 3$ makes the centre weight
  $w_{2n+1} = \kappa/(n+\kappa)$ **negative** as soon as $n > 3$. Negative weights break
  the covariance estimate: $P$ is a sum of outer products with negative coefficients, so it
  need not be positive semidefinite, and the filter can fail for numerical reasons
  rather than modelling ones. The last row is the same argument, from the other side.
- In the $(\alpha,\beta,\kappa)$ parametrisation of the draft, the same filter appears with
  $\lambda = \alpha^2(n+\kappa) - n$, $w_0 = \kappa/(n+\kappa)$ and the remaining weights
  $\frac{1}{2(n+\kappa)}$. Mention it in one sentence for the audience who knows that
  convention; then keep $\kappa$ for the rest of the talk.

---

### S3. What each filter actually costs

**Draft item 11.**

**On the slide**

Title: *What each filter actually costs.*

Per cycle, the cost of a filter is two very different things:

1. **how many times you evaluate $f$ and $h$** (each evaluation may be an orbit
   propagation, an aerodynamic model, a rotation);
2. **how much linear algebra** (the covariances cost $O(n^3)$, the innovations $O(n^2 m)$).

| Filter | evaluations of $f$, $h$ per cycle | linear algebra | comments |
| --- | --- | --- | --- |
| KF | 0 | $O(n^3)$ | the baseline |
| EKF | 2 Jacobians | $O(n^3)$ | the Jacobian is often the expensive part |
| UKF | $2n+1$ of $f$, $2n+1$ of $h$ | $O(n^3)$ | one set of points, propagated through both |
| CKF | $2n$ of $f$, $2n$ of $h$ | $O(n^3)$ | points regenerated from the prediction for the measurement stage |

The particle filter is deliberately **not** on this slide: it belongs to the second half of
the section, where the non-Gaussian posterior is discussed. What is said here is that the
sigma-point filters grow **linearly** in the dimension $n$.

**Speaker notes**

- The point of the slide: the *number* of function evaluations is the wrong metric if the
  function is expensive, and the right metric if the function is cheap. In a radar
  tracker $f$ is a matrix product plus a rotation, so $2n+1$ evaluations are nearly free
  and the covariance algebra dominates. In orbit determination $f$ is a Kepler
  propagation, so the count of evaluations is everything.
- The classical UKF propagates **one** set of $2n+1$ points through $f$ and then through
  $h$; the CKF in our notes **regenerates** a fresh set of $2n$ points from the
  prediction before the measurement stage, which is why it costs $2n + 2n$ rather than
  $2n$. Both conventions exist in the literature: what matters is that the numbers in
  the table match the implementation we actually run in the simulation.
- Live demo, if the timing allows: open the Desmos UKF simulation
  (`https://www.desmos.com/calculator/jvuspyhbn9`) and change the spread of the points on
  the fly. It makes the $2n+1$ points concrete for the audience in ten seconds, better
  than any static figure.

---

### S4. First order versus third order

**Draft item 11.** The accuracy half of the trade-off, with the worked example already in
the notes.

**On the slide**

Title: *First order versus third order.*

- The EKF propagates the moments of a **first order Taylor expansion** of $f$: the terms
  of order two and above are dropped, so the predicted mean is **biased** and the
  propagated covariance is **too optimistic**.
- The UKF and the CKF propagate the moments of the **exact** function, through points
  that sample the curvature: they match the expansion up to third order (the cubature
  rule is exact for any polynomial of total degree $\le 3$).

Worked example, $f(x) = x^2 + 0.5$ with $x \sim \mathcal{N}(0, \sigma^2)$:

|  | predicted mean $\hat{y}$ | true $\mathbb{E}[y]$ | error |
| --- | --- | --- | --- |
| EKF (tangent at $x = 0$) | $0.5$ | $\sigma^2 + 0.5$ | $-\sigma^2$ |
| UKF / CKF (points at $\pm\sqrt{3}\sigma$) | $\sigma^2 + 0.5$ | $\sigma^2 + 0.5$ | $0$ |

With $\sigma = 1$ the EKF is off by $100\%$ of the signal, and it is not a matter of
tuning: the tangent at the mean is flat, the curvature is simply **not visible** to it.

![[EKF-vs-UT.svg | 620]]

**Speaker notes**

- Do the example on the board if there is time, it takes thirty seconds and it is the
  single most convincing moment of the talk. The EKF replaces the parabola by its
  tangent at the mean, which is the horizontal line, and averages it: the answer is
  $0.5$, while the true mean of the parabola is $0.5 + \sigma^2$. The sigma-point filters
  evaluate the parabola at $\pm\sqrt{3}\sigma$ and at the mean, and the weighted average
  comes out exactly right.
- The point to make explicit: **the EKF is not "less precise", it is blind**. It has no
  information about the curvature, so no choice of $Q$, $R$ or $\kappa$ can fix it.
- The figure shows the geometry: the tangent line (red) and the two sigma points
  (blue) landing on the parabola, with their weighted mean falling on the true mean.
- Caveat to state out loud, because it is the honest limit of the whole family: matching
  the third order does **not** make the filter MMSE. The UKF and the CKF are still
  LMMSE filters, they just propagate the two moments much better.

---

### S5. The trade-off in one picture

**Draft item 11.** This slide is the figure produced by the simulation (the TODO
"simulazione che vale anche come base per il secondo progetto"), so it is the one that
needs work outside this document.

**On the slide**

Title: *Cost against accuracy.*

Two panels, both on the same radar-tracking benchmark of chapter 5 and 6
($\text{state} = [x, \dot{x}, y, \dot{y}]$, measurement = range and bearing):

- **left panel**: RMSE of the state estimate on the vertical axis, number of function
  evaluations per cycle (or milliseconds per cycle) on the horizontal axis. One point per
  filter: KF is off the chart because the model is nonlinear, then EKF, UKF, CKF, PF.
  Expected reading: the EKF is the cheapest and the worst, UKF and CKF nearly coincide
  (same geometry, different radius), the particle filter is far to the right and only
  wins when the posterior becomes multimodal.
- **right panel**: RMSE against the strength of the nonlinearity (for instance the bearing
  noise, or a curvature parameter in $h$), with the crossover point where the EKF stops
  being acceptable.

**Speaker notes**

- Use the numbers honestly: if the UKF and the CKF overlap in the simulation, say so,
  because that is exactly the message of the CKF note (the CKF is the UKF with
  $\kappa = 0$, so it cannot be more accurate than that particular UKF, only cheaper and
  safer).
- The right panel is the honest answer to "when should I stop using the EKF?": there is a
  region of the problem where the EKF is fine and everywhere else it is not.
- If the simulation is not ready, replace this slide with the table "cost versus accuracy
  in words" (derivative free or not, order of accuracy, tuning, positivity) and move on:
  the argument does not depend on the figure.

---

### S6. What no Kalman filter can do

**Draft item 12.**

**On the slide**

Title: *What no Kalman filter can do.*

Every filter we have seen, from the KF to the CKF, closes the posterior with a single
Gaussian:

$$p(x_k \mid z^k) \approx \mathcal{N}(\hat{x}_{k|k},\, P_{k|k})$$

Two numbers against an infinite-dimensional object. And a nonlinear map of a Gaussian is
**not** a Gaussian: it is skewed, heavy-tailed, or **multimodal**.

Two concrete failures:

1. **Bearing-only tracking.** The bearing of a target does not fix its range: the
   admissible positions form a ray. With a prior, the posterior can have **two modes**
   (target on one side of the sensor or on the other). The filter averages the two modes:
   the mean is a position where the target **is not**, and the covariance, while huge,
   has the wrong shape entirely.
2. **Angles live on a circle.** The innovation of a bearing measurement is the wrapped
   difference $\operatorname{wrap}(z - \hat{z})$, not the raw difference. A Gaussian filter
   that ignores this jumps by $2\pi$ every time the target crosses the branch cut.

The consequence is called **inconsistency**: the filter reports a $P$ that is smaller than
its real error. It is measurable, with the two standard metrics:

- **NEES** (normalised estimation error squared), from the state error: tests whether the
  reported covariance is the true one;
- **NIS** (normalised innovation squared), from the residuals: tests the same property
  using only the measurements.

And the other limits, in one line each:

- the EKF needs hand-derived, correct, differentiable Jacobians;
- the UKF needs $\kappa$, and $\kappa < 0$ breaks the positivity of $P$;
- all of them are **LMMSE**, not MMSE: the estimator is a linear function of the data by
  construction;
- none of them can impose hard constraints (positivity, bounds, contact, no-collision).

**Speaker notes**

- This is the hinge of the presentation: everything so far has been about *how to
  approximate* a distribution, and now we ask *what if the distribution is not the shape
  we assume*.
- The bimodality example is worth drawing: a posterior with two peaks, and the Gaussian
  surrogate sitting on the valley between them. The mean is the worst possible estimate.
- The consistency metrics are the honest engineering answer: a filter that lies about its
  own uncertainty is worse than useless, because every downstream decision trusts that
  number. NEES and NIS are cheap to compute and they are what tells you that your filter
  has left the region where its own covariance is meaningful.
- The two additional limits (derivatives, tuning, constraints) are the ones quoted in the
  EKF failure-modes material we used: a filter that is "confident while wrong" is the
  standard diagnosis of an inconsistent EKF-SLAM.
- Close the slide by pointing forward: the family we have just surveyed shares one
  assumption, and the next slide removes it.

---

### S7. Beyond the Gaussian: particle filters as a pointer

**Draft item 13.** Deliberately short: this slide is a *starting point to look into*, not
an introduction to the method.

**On the slide**

Title: *Beyond the Gaussian.*

The assumption that all four filters share, dropped: represent the posterior by a weighted
cloud of samples instead of by two moments.

$$x_k^{(i)} \sim p(x_k \mid x_{k-1}^{(i)}), \qquad w_k^{(i)} \propto w_{k-1}^{(i)}\, p(z_k \mid x_k^{(i)})$$

- **what it buys**: any posterior shape, multimodal included, with no derivatives and no
  linearisation;
- **what it costs**: $N \sim 10^3$ to $10^5$ samples per cycle, and a sample cost that
  grows exponentially with the dimension, which is why the Kalman family stays the default
  in SLAM and navigation.

Where to go from here:

- Doucet, de Freitas, Gordon (2001), *An Introduction to Particle Filters*: the standard
  reference;
- Del Moral, *Bayesian filtering: from Kalman filters to particle filters, and beyond*:
  the survey, which also places the hybrids;
- the middle ground worth looking at, a finite **mixture** of Gaussians instead of a
  single one: Gaussian sum filters (Arasaratnam and Haykin, 2009), Gaussian particle
  filter (Dearden, 2003), unscented particle filter (van der Merwe, de Freitas, Doucet,
  2000).

**Speaker notes**

- One minute on this slide. The audience must leave with three things only: the name, the
  idea (sample instead of summarise), and the two prices (many samples, exponential in
  the dimension).
- Do not derive anything here. The point is not to teach the particle filter but to say
  that the Gaussian assumption can be removed, and to point at where that road leads.
- The three references at the bottom are the real deliverable of the slide: they are the
  starting points for the "new research" part of the presentation, together with the
  Gaussian sum filters, which attack the multimodality of S6 without the full price of a
  particle cloud.
- Hand over to S8: the table of the family is the summary of the whole talk.

---

### S8. Where the family ends

**Draft items 12 and 13, closing slide.**

**On the slide**

Title: *Where the family ends.*

A map of the whole talk, from the most to the least structured assumption:

|  | Posterior assumed | Cost per cycle | Fails when |
| --- | --- | --- | --- |
| KF | Gaussian, and the model is linear | cheapest | the model is nonlinear |
| EKF | Gaussian | 2 Jacobians | the nonlinearity is strong, or $P$ is not small |
| UKF | Gaussian | $2n+1$ points | the posterior is multimodal, or $\kappa$ is mistuned |
| CKF | Gaussian | $2n$ points | the posterior is multimodal |
| PF | none | $N \sim 10^3$ samples | the dimension is high |

Three takeaways:

1. the filters differ in **how the distribution is approximated**, not in what they
   optimise: all of them are LMMSE estimators with the same correction engine;
2. the sigma-point filters are the sweet spot of the family: derivative free, third
   order accurate, $O(n)$ evaluations;
3. the right question is never "which filter is the best", but **"how non-Gaussian is my
   posterior, and how expensive is one evaluation of $f$?"**

Two open directions, for the research part of the presentation:

- **automatic tuning**: choosing $\kappa$ (or deciding between the UKF and the CKF) from
  the data, instead of by hand;
- **adaptive switching**: deciding at run time which family to use, which is the
  multiple-model logic of the course seen from a different angle.

**Speaker notes**

- The table is the summary of everything: read it as a decision procedure. If the model
  is linear, use the KF. If it is mildly nonlinear and the Jacobians are easy, the EKF
  is still fine and it is the cheapest. If it is nonlinear, use the CKF as the default
  (no tuning, guaranteed positive covariance) or the UKF if you have a reason to tune
  $\kappa$. If the posterior can be multimodal, none of them work and you need a particle
  filter or a Gaussian sum filter.
- The three takeaways are the sentences the audience should remember. The last one is the
  bridge to the research part of the presentation and to the second project.

---

## 3. Figures to produce

| Figure | Where | Notes |
| --- | --- | --- |
| Schema of the three routes | S1 | the mermaid block above, to be redrawn as an SVG in the layout pass |
| Comparison table | S2 | already written as a table, no figure needed |
| EKF vs unscented transform | S4 | **already in the vault**: `XJTU/Fall I/Estimation and Filtering/Notes/assets/EKF-vs-UT.svg` |
| UT vs cubature points | optional, S2 or S7 | **already in the vault**: `XJTU/Fall I/Estimation and Filtering/Notes/assets/cubature-vs-ut-points.svg` |
| Cost versus accuracy | S5 | to be produced by the simulation |
| Posteriors: unimodal, skewed, bimodal | S6 | to be drawn, three panels with the Gaussian surrogate on top of each |

## 4. The simulation behind S5 (and the second project)

The TODO in the shared draft says the simulation should also serve as the base for the
second project. What the slides need from it:

1. the benchmark of chapter 5 and 6: constant-velocity target, range and bearing
   measurement, $x = [x, \dot{x}, y, \dot{y}]$, the noise models already written in the CKF
   note;
2. four filters implemented on it: KF (on a linearised model, for reference), EKF, UKF,
   CKF, and optionally the SIR particle filter;
3. a Monte-Carlo loop (the RMSE definition is on the [RMSE article](https://kalman-filter.com/root-mean-square-error/)),
   reporting the RMSE of the state estimate, the number of function evaluations per
   cycle and the wall-clock time;
4. two sweeps: RMSE against the number of evaluations, and RMSE against the strength of
   the nonlinearity;
5. the consistency metrics on the same runs (NEES and NIS), to feed the argument of S6
   with numbers instead of words.

The reference implementation of the CKF cycle is already in the notes (the `ckf_predict`
and `ckf_update` functions in `Notes/6. Cubature Kalman Filter.md`) and is the template
for the other three.

## 5. Material and links

- [Chapter 5 of the course slides](../Chapter05_2026.pdf), slides 12 to 17: the unscented transform and one cycle of the filter.
- [Cubature Kalman Filter article](https://kalman-filter.com/cubature-kalman-filter/): the source of the CKF note, with the UT versus CKF comparison and the "special case" remark.
- [Extended Kalman Filter article](https://kalman-filter.com/extended-kalman-filter/): the failure modes, the checklist of when the EKF is still acceptable, and the list of modern alternatives.
- [Unscented Kalman Filter article](https://kalman-filter.com/unscented-kalman-filter/): the UKF as it is used in the presentation.
- [NEES](https://kalman-filter.com/normalized-estimation-error-squared/) and [NIS](https://kalman-filter.com/normalized-innovation-squared/): the consistency tests of S6.
- [Desmos UKF simulation](https://www.desmos.com/calculator/jvuspyhbn9): the live demo for S3 and S4.
- [Video on the CKF](https://www.youtube.com/watch?v=c_6WDC66aVk): backup material if the live demo fails.
- Primary references already in the CKF note: Arasaratnam and Haykin (2009) on the cubature filter, Crouse (2015) on angular measurement models, Julier and Uhlmann (1997, 2004) on the sigma points.

## 6. Checklist before the layout pass

- [x] content of slides 10 to 13 of the shared structure
- [x] one slide per row of the structure, with the schema expanded into 8 slides
- [x] HTML draft of the slides (`deck-draft.html`), text cut down and type enlarged for projection
- [ ] pick the final number of slides and cut to fit the time slot
- [ ] produce the cost versus accuracy figure from the simulation
- [ ] draw the three posterior panels for S6
- [x] particle filter section kept short and conceptual: pointers to the literature, no derivation
- [ ] decide whether the particle filter pointers need a short verbal mention in the intro slide of the whole talk
- [ ] check the notation against the rest of the presentation ($\chi_i$, $w_i$, $\kappa$, $C^{xz}$)
- [ ] layout and styling pass (to do later)
