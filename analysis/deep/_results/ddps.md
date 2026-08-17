# DDPS (data-driven physical simulation) — verified measured results

Every number below is computed by a short program we ran. Script: scripts/experiments/ddps_run.py
(numpy + torch, CPU, fixed seeds). Cite numbers verbatim; do NOT invent new ones.

## EXP1 — physics-informed learning (concept: physics-informed-learning)
- A small network is trained to solve a differential equation with **no solution data at all** — the
  only teacher is the equation itself (plug the network into the equation, punish the mismatch) plus the
  values fixed at the two ends. Target problem has the exact answer sin(pi x) on the interval 0 to 1.
- Largest gap between the network's answer and the true answer: **0.911 at the start -> 0.0023 after
  training**. It learned the whole curve from the physics alone.
- Insight: you can replace training data with the law the answer must obey. The equation becomes the loss.

## EXP2 — operator learning (concept: operator-learning)
- Instead of solving one problem, we train ONE network to map any forcing (the push applied along a bar)
  to its solution, for the equation -u'' = f with the ends pinned to zero. Trained on 400 random
  forcings, then tested on **100 brand-new forcings it never saw**.
- Mean relative error on the unseen forcings: **3.69%**. One forward pass replaces a fresh solve.
- Insight: you can learn the whole solution map (a function-to-function operator), not just one solution —
  so new cases are answered instantly, with no solver call.

## EXP3 — reduced-order modeling (concept: reduced-order-modeling)
- Snapshots of a field sampled at **200 points** each, but the field only ever varies in a few simple ways.
- Number of modes (found by principal-component / POD analysis) needed to capture **99% of the variation: 7;
  for 99.9%: 9**. The first 10 modes already hold **99.97%**.
- Insight: high-dimensional physics data usually lives on a low-dimensional surface; keep a handful of
  modes and you keep almost everything, at a fraction of the cost.

## EXP4 — scientific machine learning / SINDy (concept: scientific-machine-learning)
- From trajectory data alone (positions and velocities over time, no equations given), sparse regression
  over a library of candidate terms recovered the governing equations: **x' = 1.00 y** and
  **y' = -1.00 x - 0.30 y** (the true system exactly), keeping only **3 nonzero terms out of 12** candidates.
- Insight: machine learning need not be a black box — you can have it hand you back the actual equation,
  interpretable and reusable, by insisting the answer be simple (sparse).

## EXP5 — differentiable simulation (concept: differentiable-simulation)
- A projectile simulator with an unknown air-drag coefficient. Starting from a wrong guess of **0.50**,
  we differentiated THROUGH 300 simulator steps and used the gradient to correct the guess; it converged
  to **0.120**, the true value.
- Insight: if the simulator itself is differentiable, you can back-propagate error through the physics and
  recover hidden parameters (or design inputs) directly, instead of guessing and re-running blindly.

## EXP6 — inverse problems and control (concept: inverse-problems-and-control)
- Recover a sharp two-bump source from a blurred, noisy measurement (an ill-posed inverse problem).
- The naive direct inversion **explodes** — relative error over **forty million percent**, the answer is
  meaningless noise. Adding a smoothness prior (regularization) brings the error down to **about 3%** and
  recovers both bumps.
- Insight: running physics backward is unstable — tiny measurement noise blows up. A prior about what the
  answer should look like (regularization) is what makes the inverse problem solvable.

## EXP7 — fluid-mechanics simulation / DMD (concept: fluid-mechanics-simulation)
- From snapshots of an evolving field alone, dynamic mode decomposition (DMD) recovered the two temporal
  frequencies baked into the flow: **1.0 and 2.6** — exactly.
- Insight: you can extract the dominant coherent patterns and their rhythms straight from data snapshots,
  with no knowledge of the underlying equations — the backbone of data-driven fluid analysis.

## EXP8 — hybrid twins (concept: hybrid-twins)
- A pendulum simulator that knows only linear friction, run against a reality that also has nonlinear
  friction. Physics-only rollout error: **0.222 radians**. Adding a small learned correction for exactly
  what the physics misses: **0.0018 radians** — about a **122x** reduction.
- Insight: keep the physics you trust and let a small model learn only the residual it gets wrong. The
  hybrid is far more accurate than either the bare physics or a from-scratch black box.

## EXP9 — uncertainty and robustness (concept: uncertainty-and-robustness)
- An ensemble of 8 networks trained on data with a gap in the middle. Their disagreement (spread) where
  they had data: **0.005**; in the unseen gap: **0.041** — uncertainty grows about **8.3x** exactly where
  the model has no data.
- Insight: a good model should know where it doesn't know. An ensemble's disagreement is honest error bars
  that stay tight on familiar ground and widen where the model is extrapolating — essential for trusting
  simulation surrogates.
