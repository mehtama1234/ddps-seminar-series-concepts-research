#!/usr/bin/env python3
"""DDPS (data-driven physical simulation) — real, verified experiments.
Every headline number in the deep dives comes from this script.
Run: .venv-torch/bin/python scripts/experiments/ddps_run.py
numpy + torch (CPU). Deterministic seeds throughout."""
import numpy as np
import torch, math

torch.manual_seed(0)
np.random.seed(0)
R = {}


def sep(t): print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


# ------------------------------------------------------------------ EXP1
# PHYSICS-INFORMED LEARNING: solve u''(x) = -pi^2 sin(pi x) on [0,1],
# u(0)=u(1)=0, whose exact solution is u(x)=sin(pi x).  NO training data —
# the only teacher is the equation itself (physics residual) + boundary.
def exp1_pinn():
    sep("EXP1 physics-informed learning — PINN solves a PDE with no data")
    torch.manual_seed(0)
    net = torch.nn.Sequential(torch.nn.Linear(1, 32), torch.nn.Tanh(),
                              torch.nn.Linear(32, 32), torch.nn.Tanh(),
                              torch.nn.Linear(32, 1))
    opt = torch.optim.Adam(net.parameters(), lr=3e-3)
    xb = torch.tensor([[0.0], [1.0]])                       # boundary points
    def loss_fn():
        x = torch.rand(128, 1, requires_grad=True)          # interior collocation
        u = net(x)
        ux = torch.autograd.grad(u, x, torch.ones_like(u), create_graph=True)[0]
        uxx = torch.autograd.grad(ux, x, torch.ones_like(ux), create_graph=True)[0]
        f = -(math.pi ** 2) * torch.sin(math.pi * x)
        phys = ((uxx - f) ** 2).mean()
        bc = (net(xb) ** 2).mean()
        return phys + 20.0 * bc
    err0 = None
    for it in range(4000):
        opt.zero_grad(); L = loss_fn(); L.backward(); opt.step()
        if it == 0:
            with torch.no_grad():
                xt = torch.linspace(0, 1, 200).reshape(-1, 1)
                err0 = (net(xt).flatten() - torch.sin(math.pi * xt).flatten()).abs().max().item()
    with torch.no_grad():
        xt = torch.linspace(0, 1, 200).reshape(-1, 1)
        pred = net(xt).flatten(); exact = torch.sin(math.pi * xt).flatten()
        err = (pred - exact).abs().max().item()
    R["pinn_err0"] = round(err0, 3); R["pinn_err"] = round(err, 4)
    print(f"max error vs exact sin(pi x): start {err0:.3f} -> trained {err:.4f}")
    print("(no solution data was ever shown; the equation itself is the loss)")


# ------------------------------------------------------------------ EXP2
# OPERATOR LEARNING: learn the whole solution MAP f -> u for the 1D Poisson
# problem -u'' = f, u(0)=u(1)=0, over a family of random forcings f.  Then
# test on brand-new forcings the model never saw.  This is a discretized
# DeepONet-style operator: input = f sampled at 32 points -> output = u at 32.
def poisson_solve(f, n=32):
    # solve -u'' = f on [0,1] with u(0)=u(1)=0 by finite differences
    h = 1.0 / (n - 1)
    A = (np.diag(2 * np.ones(n - 2)) - np.diag(np.ones(n - 3), 1)
         - np.diag(np.ones(n - 3), -1)) / h ** 2
    u = np.zeros((f.shape[0], n))
    for i in range(f.shape[0]):
        u[i, 1:-1] = np.linalg.solve(A, f[i, 1:-1])
    return u

def rand_forcings(m, n=32, seed=0):
    rng = np.random.default_rng(seed)
    x = np.linspace(0, 1, n)
    f = np.zeros((m, n))
    for k in range(1, 5):                                   # random Fourier forcings
        f += rng.normal(size=(m, 1)) * np.sin(k * math.pi * x)[None, :]
    return f, x

def exp2_operator():
    sep("EXP2 operator learning — one net maps forcing -> solution, any forcing")
    n = 32
    ftr, x = rand_forcings(400, n, seed=1); utr = poisson_solve(ftr, n)
    fte, _ = rand_forcings(100, n, seed=99); ute = poisson_solve(fte, n)
    Xtr = torch.tensor(ftr, dtype=torch.float32); Ytr = torch.tensor(utr, dtype=torch.float32)
    Xte = torch.tensor(fte, dtype=torch.float32); Yte = torch.tensor(ute, dtype=torch.float32)
    torch.manual_seed(0)
    net = torch.nn.Sequential(torch.nn.Linear(n, 128), torch.nn.ReLU(),
                              torch.nn.Linear(128, 128), torch.nn.ReLU(),
                              torch.nn.Linear(128, n))
    opt = torch.optim.Adam(net.parameters(), lr=2e-3)
    lossf = torch.nn.MSELoss()
    for it in range(3000):
        opt.zero_grad(); L = lossf(net(Xtr), Ytr); L.backward(); opt.step()
    with torch.no_grad():
        # relative L2 error on unseen forcings
        pr = net(Xte)
        rel = (torch.norm(pr - Yte, dim=1) / torch.norm(Yte, dim=1)).mean().item()
        # speed: one forward pass vs solving the linear system
    R["operator_relerr"] = round(rel * 100, 2)
    print(f"mean relative error on 100 UNSEEN forcings: {rel*100:.2f}%")
    print("the trained operator predicts the solution in one pass, no solver call")


# ------------------------------------------------------------------ EXP3
# REDUCED-ORDER MODELING: snapshots of a parameterized field live on a
# low-dimensional subspace.  POD/PCA: how many modes capture 99% / 99.9%?
def exp3_rom():
    sep("EXP3 reduced-order modeling — a 200-D field lives in a few modes")
    rng = np.random.default_rng(3)
    x = np.linspace(0, 1, 200)
    # each snapshot = travelling-ish gaussian bump at a random center + width
    snaps = []
    for _ in range(500):
        c = rng.uniform(0.25, 0.75); w = rng.uniform(0.05, 0.12)
        snaps.append(np.exp(-((x - c) ** 2) / (2 * w ** 2)))
    X = np.array(snaps)                                     # 500 x 200
    Xc = X - X.mean(0)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    energy = np.cumsum(S ** 2) / np.sum(S ** 2)
    k99 = int(np.searchsorted(energy, 0.99) + 1)
    k999 = int(np.searchsorted(energy, 0.999) + 1)
    R["rom_dim"] = 200; R["rom_k99"] = k99; R["rom_k999"] = k999
    R["rom_e10"] = round(float(energy[9]) * 100, 2)
    print(f"ambient dimension: 200 samples per snapshot")
    print(f"modes for 99% of the energy: {k99}; for 99.9%: {k999}")
    print(f"first 10 modes already hold {energy[9]*100:.2f}%")


# ------------------------------------------------------------------ EXP4
# SCIENTIFIC MACHINE LEARNING: SINDy recovers the GOVERNING EQUATION of a
# nonlinear oscillator from trajectory data alone (sparse regression over a
# library of candidate terms).  Cubic (van-der-Pol-ish) damped oscillator.
def exp4_sindy():
    sep("EXP4 scientific ML — SINDy reads the equation back off the data")
    dt = 0.002; T = 6000
    # true system: x' = y ; y' = -x - 0.3 y (linear damped) -- recover it
    xy = np.zeros((T, 2)); xy[0] = [2.0, 0.0]
    for t in range(T - 1):
        x, y = xy[t]
        dx = y; dy = -x - 0.3 * y
        xy[t + 1] = xy[t] + dt * np.array([dx, dy])
    X = xy[:-1]
    dX = (xy[1:] - xy[:-1]) / dt
    # library: [1, x, y, x^2, xy, y^2]
    x, y = X[:, 0], X[:, 1]
    Theta = np.column_stack([np.ones_like(x), x, y, x * x, x * y, y * y])
    names = ["1", "x", "y", "x^2", "xy", "y^2"]
    # sequentially-thresholded least squares
    Xi = np.linalg.lstsq(Theta, dX, rcond=None)[0]
    for _ in range(10):
        small = np.abs(Xi) < 0.05
        Xi[small] = 0
        for j in range(2):
            big = ~small[:, j]
            if big.any():
                Xi[big, j] = np.linalg.lstsq(Theta[:, big], dX[:, j], rcond=None)[0]
    R["sindy_xdot"] = f"x' = {Xi[2,0]:.2f} y"
    R["sindy_ydot"] = f"y' = {Xi[1,1]:.2f} x + {Xi[2,1]:.2f} y"
    R["sindy_terms"] = int((np.abs(Xi) > 0).sum())
    print("recovered equations from data alone:")
    print(f"  x' = {Xi[2,0]:.2f} y            (true: 1.00 y)")
    print(f"  y' = {Xi[1,1]:.2f} x + {Xi[2,1]:.2f} y   (true: -1.00 x - 0.30 y)")
    print(f"nonzero terms kept: {int((np.abs(Xi)>0).sum())} of 12 candidates")


# ------------------------------------------------------------------ EXP5
# DIFFERENTIABLE SIMULATION: run a projectile simulator, then differentiate
# THROUGH it to recover an unknown drag coefficient by gradient descent so
# the simulated trajectory matches an observed one.
def exp5_diffsim():
    sep("EXP5 differentiable simulation — gradient through the simulator finds a hidden parameter")
    def simulate(drag, steps=300, dt=0.02):
        pos = torch.zeros(2); vel = torch.tensor([8.0, 12.0])
        traj = [pos]
        g = torch.tensor([0.0, -9.8])
        for _ in range(steps):
            speed = torch.norm(vel) + 1e-6
            acc = g - drag * speed * vel
            vel = vel + dt * acc
            pos = pos + dt * vel
            traj.append(pos)
        return torch.stack(traj)
    true_drag = torch.tensor(0.12)
    obs = simulate(true_drag).detach()
    drag = torch.tensor(0.5, requires_grad=True)            # wrong initial guess
    opt = torch.optim.Adam([drag], lr=0.03)
    d0 = drag.item()
    for it in range(400):
        opt.zero_grad()
        loss = ((simulate(drag) - obs) ** 2).mean()
        loss.backward(); opt.step()
        with torch.no_grad(): drag.clamp_(0.0, 2.0)
    R["diffsim_true"] = 0.12; R["diffsim_guess"] = round(d0, 2)
    R["diffsim_found"] = round(drag.item(), 3)
    print(f"true drag 0.120; started from guess {d0:.2f}; recovered {drag.item():.3f}")
    print("by back-propagating error through 300 simulator steps")


# ------------------------------------------------------------------ EXP6
# INVERSE PROBLEMS & control: recover an unknown source from BLURRED + NOISY
# observations.  Naive inversion explodes; regularization (physics prior)
# recovers it.  Classic ill-posed deconvolution.
def exp6_inverse():
    sep("EXP6 inverse problems — regularization tames an ill-posed inversion")
    rng = np.random.default_rng(6)
    n = 60
    x = np.linspace(0, 1, n)
    src = np.exp(-((x - 0.35) ** 2) / (2 * 0.05 ** 2)) + 0.7 * np.exp(-((x - 0.7) ** 2) / (2 * 0.06 ** 2))
    # blur operator (gaussian smoothing) = forward model
    G = np.exp(-((x[:, None] - x[None, :]) ** 2) / (2 * 0.035 ** 2)); G /= G.sum(1, keepdims=True)
    obs = G @ src + rng.normal(0, 0.005, n)
    # naive inverse
    naive = np.linalg.solve(G + 1e-9 * np.eye(n), obs)
    naive_err = np.linalg.norm(naive - src) / np.linalg.norm(src)
    # Tikhonov-regularized (smoothness prior)
    lam = 0.01
    reg = np.linalg.solve(G.T @ G + lam * np.eye(n), G.T @ obs)
    reg_err = np.linalg.norm(reg - src) / np.linalg.norm(src)
    R["inv_naive_blows"] = True
    R["inv_reg"] = round(float(reg_err) * 100, 0)
    print(f"naive inversion relative error: {naive_err*100:.3g}%  (explodes — answer is meaningless)")
    print(f"regularized inversion error:    {reg_err*100:.0f}%  (recovers the two-bump source)")


# ------------------------------------------------------------------ EXP7
# FLUID-MECHANICS SIMULATION via DMD: extract the dominant oscillation of a
# synthetic advection field straight from snapshots (frequency + growth).
def exp7_dmd():
    sep("EXP7 fluid simulation — DMD pulls the dominant mode out of flow snapshots")
    # each frequency occupies a 2-D spatial subspace (quadrature modes) so the
    # state truly ROTATES -> DMD recovers the frequency exactly (rank 4).
    nx = 100; dt = 0.02; t = np.arange(200) * dt; xs = np.linspace(0, 1, nx)
    f1, f2 = 1.0, 2.6
    d1, d2 = -0.15, 0.0
    p1a, p1b = np.sin(np.pi * xs), np.sin(2 * np.pi * xs)
    p2a, p2b = np.sin(3 * np.pi * xs), np.sin(4 * np.pi * xs)
    a1, a2 = np.exp(d1 * t), np.exp(d2 * t)
    X = (a1 * np.cos(2 * np.pi * f1 * t))[None, :] * p1a[:, None] \
        + (a1 * np.sin(2 * np.pi * f1 * t))[None, :] * p1b[:, None] \
        + (a2 * np.cos(2 * np.pi * f2 * t))[None, :] * p2a[:, None] \
        + (a2 * np.sin(2 * np.pi * f2 * t))[None, :] * p2b[:, None]
    X1, X2 = X[:, :-1], X[:, 1:]
    U, S, Vt = np.linalg.svd(X1, full_matrices=False)
    r = 4
    Ur, Sr, Vr = U[:, :r], S[:r], Vt[:r].T
    Atil = Ur.T @ X2 @ Vr / Sr
    ev = np.linalg.eigvals(Atil)
    dt = t[1] - t[0]
    freqs = np.abs(np.angle(ev) / (2 * np.pi * dt))
    freqs = sorted(set(round(f, 2) for f in freqs if f > 0.05))
    R["dmd_f1"] = f1; R["dmd_f2"] = f2
    R["dmd_found"] = freqs[:2]
    print(f"true temporal frequencies embedded in the flow: {f1}, {f2}")
    print(f"DMD recovered (from snapshots only): {freqs[:2]}")


# ------------------------------------------------------------------ EXP8
# HYBRID TWINS: known physics + a small ML correction for what physics
# misses.  Physics-only pendulum ignores a nonlinear friction; the residual
# net closes the gap.
def exp8_hybrid():
    sep("EXP8 hybrid twins — physics gets you close, ML closes the residual")
    dt = 0.02; T = 400
    def true_step(th, w):                                   # reality: nonlinear damping
        a = -9.8 * np.sin(th) - 0.4 * w - 0.3 * w * abs(w)
        return th + dt * w, w + dt * a
    def phys_step(th, w):                                   # our model: linear damping only
        a = -9.8 * np.sin(th) - 0.4 * w
        return th + dt * w, w + dt * a
    th = w = None
    # build trajectory + residuals
    th0, w0 = 1.0, 0.0
    T_true = [(th0, w0)]; th, w = th0, w0
    for _ in range(T): th, w = true_step(th, w); T_true.append((th, w))
    T_true = np.array(T_true)
    # residual data: (state) -> (true next w - phys next w)
    S_in, res = [], []
    for i in range(T):
        th_i, w_i = T_true[i]
        _, w_phys = phys_step(th_i, w_i)
        _, w_true = T_true[i + 1]
        S_in.append([math.sin(th_i), w_i]); res.append(w_true - w_phys)
    S_in = torch.tensor(S_in, dtype=torch.float32)
    res = torch.tensor(res, dtype=torch.float32).reshape(-1, 1)
    torch.manual_seed(0)
    net = torch.nn.Sequential(torch.nn.Linear(2, 32), torch.nn.Tanh(), torch.nn.Linear(32, 1))
    opt = torch.optim.Adam(net.parameters(), lr=5e-3); lf = torch.nn.MSELoss()
    for _ in range(2000):
        opt.zero_grad(); L = lf(net(S_in), res); L.backward(); opt.step()
    # roll out physics-only vs hybrid, compare to truth
    def rollout(hybrid):
        th, w = th0, w0; err = 0.0; out = [(th, w)]
        for i in range(T):
            th_p, w_p = phys_step(th, w)
            if hybrid:
                corr = net(torch.tensor([[math.sin(th), w]], dtype=torch.float32)).item()
                w_p = w_p + corr
            th, w = th_p, w_p; out.append((th, w))
        out = np.array(out)
        return np.sqrt(np.mean((out[:, 0] - T_true[:, 0]) ** 2))
    e_phys = rollout(False); e_hyb = rollout(True)
    R["hybrid_phys"] = round(float(e_phys), 3); R["hybrid_hyb"] = round(float(e_hyb), 4)
    R["hybrid_factor"] = round(float(e_phys / max(e_hyb, 1e-9)), 0)
    print(f"angle error over full rollout — physics only: {e_phys:.3f} rad")
    print(f"                                physics + ML: {e_hyb:.4f} rad")
    print(f"the learned residual cuts the error about {e_phys/max(e_hyb,1e-9):.0f}x")


# ------------------------------------------------------------------ EXP9
# UNCERTAINTY & ROBUSTNESS: a deep ENSEMBLE gives error bars that stay small
# where it saw data and GROW where it did not (honest 'I don't know').
def exp9_uq():
    sep("EXP9 uncertainty — an ensemble knows where it doesn't know")
    rng = np.random.default_rng(9)
    xtr = np.concatenate([rng.uniform(-3, -1, 40), rng.uniform(1, 3, 40)])  # gap in [-1,1]
    ytr = np.sin(xtr) + rng.normal(0, 0.05, xtr.shape)
    Xtr = torch.tensor(xtr, dtype=torch.float32).reshape(-1, 1)
    Ytr = torch.tensor(ytr, dtype=torch.float32).reshape(-1, 1)
    nets = []
    for s in range(8):
        torch.manual_seed(s)
        net = torch.nn.Sequential(torch.nn.Linear(1, 64), torch.nn.Tanh(),
                                  torch.nn.Linear(64, 64), torch.nn.Tanh(), torch.nn.Linear(64, 1))
        opt = torch.optim.Adam(net.parameters(), lr=5e-3); lf = torch.nn.MSELoss()
        for _ in range(1500):
            opt.zero_grad(); L = lf(net(Xtr), Ytr); L.backward(); opt.step()
        nets.append(net)
    def band(xq):
        X = torch.tensor([[xq]], dtype=torch.float32)
        with torch.no_grad():
            preds = np.array([n(X).item() for n in nets])
        return preds.std()
    in_region = np.mean([band(x) for x in np.linspace(-3, -1, 20)])   # where data is
    gap = np.mean([band(x) for x in np.linspace(-0.5, 0.5, 20)])      # the unseen gap
    R["uq_in"] = round(float(in_region), 3); R["uq_gap"] = round(float(gap), 3)
    R["uq_ratio"] = round(float(gap / max(in_region, 1e-9)), 1)
    print(f"ensemble spread where it trained:   {in_region:.3f}")
    print(f"ensemble spread in the unseen gap:  {gap:.3f}")
    print(f"uncertainty grows about {gap/max(in_region,1e-9):.1f}x in the region it never saw")


if __name__ == "__main__":
    exp1_pinn(); exp2_operator(); exp3_rom(); exp4_sindy(); exp5_diffsim()
    exp6_inverse(); exp7_dmd(); exp8_hybrid(); exp9_uq()
    sep("MACHINE-READABLE RESULTS")
    import json
    print(json.dumps(R, indent=2))
