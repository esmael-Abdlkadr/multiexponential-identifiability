#!/usr/bin/env python3
"""Multi-exponential relaxation traces with repeated acquisitions per case,
labelled by what a reference estimator actually recovers.

Each case is one relaxing system observed several times over the same window,
at the same noise level:

    y_r(t) = sum_k A_k exp(-t / tau_k) + eps_r,   eps_r ~ N(0, sigma^2),  r = 1..R

Labels
------
A component's label is not a threshold on its parameters. It is the observed
behaviour of a fixed reference estimator on single acquisitions of that case.
N_MC further single acquisitions are drawn from the same system (keyed, never
released), the estimator is run on each, and every true component is scored per
draw:

  0 resolved      the nearest estimated peak lies within 25% in lifetime and 50%
                  in amplitude, and that peak is nearer to this component than to
                  any other
  1 confounded    the nearest estimated peak is nearer to a neighbouring component:
                  this component's signal went into a peak it shares
  2 unobservable  neither: no estimated peak is attributable to it within tolerance

The label is the most frequent outcome over the N_MC draws; a tie goes to the
less resolvable class. The released repeats are evidence for predicting that
behaviour; they are not the draws it was measured on.

Reference estimator: non-negative least squares on 72 log-spaced lifetimes from
0.02 to 200 plus a constant offset; adjacent non-zero weights are grouped into
peaks (lifetime = weight-averaged log-lifetime, amplitude = summed weight); the
three largest peaks by amplitude are kept.

Keying
------
Every draw is derived from HMAC-SHA256(secret, "<purpose>:<case>"). **The secret
is not published.** Running this script produces *a* valid dataset from this
family; it does not reproduce *the* released one.

That is deliberate. An earlier release drew every parameter from SHA-256 of the
case identifier and a seed printed in the dataset card, and kept those case
identifiers in the released test split. Feeding the public test ids to the
published generator regenerated every test trace byte for byte, and the labels
with it. Re-keying the ids alone would not have closed it: the ids were
sha256(seed:i) for i in 0..5999, so all 6,000 cases could be enumerated and
every released trace matched back to its generating case by content (1000/1000).
Only a withheld key closes both routes.

Usage
-----
    python generate.py OUT --secret PATH [--n 6000] [--repeats 16] [--dtype float16]
                           [--n-mc N_MC] [--workers 8]
"""
import argparse
import hashlib
import hmac
import json
from multiprocessing import get_context
from pathlib import Path

import numpy as np
from scipy.optimize import nnls

N_COMPONENTS = 3
N_SAMPLES = 256
TAU_RANGE = (0.05, 60.0)        # log-uniform
AMP_RANGE = (0.3, 2.0)          # uniform
WINDOW_RANGE = (1.5, 12.0)      # uniform, varies per case
SIGMA_RANGE = (0.05, 0.80)      # log-uniform, never disclosed to solvers
DTYPES = {"float16": np.float16, "float32": np.float32}

N_MC = 129                      # label draws per case; ties (0.8% of components) go to the less resolvable class
TAU_GRID = np.exp(np.linspace(np.log(0.02), np.log(200.0), 72))
TAU_TOL = float(np.log(1.25))   # 25% in lifetime
AMP_TOL = 0.5                   # 50% in amplitude


def _key(secret: bytes, *parts) -> bytes:
    return hmac.new(secret, ":".join(str(p) for p in parts).encode(), hashlib.sha256).digest()


def _rng(secret: bytes, *parts) -> np.random.Generator:
    return np.random.default_rng(int.from_bytes(_key(secret, *parts)[:8], "big"))


def case_id(secret: bytes, index: int) -> str:
    return "case_" + _key(secret, "case", index).hex()[:12]


def params(secret: bytes, cid: str):
    """Generating parameters, unrounded. The draw order is part of the format."""
    rng = _rng(secret, "params", cid)
    tau = np.sort(np.exp(rng.uniform(*np.log(TAU_RANGE), size=N_COMPONENTS)))
    amp = rng.uniform(*AMP_RANGE, size=N_COMPONENTS)
    window = float(rng.uniform(*WINDOW_RANGE))
    sigma = float(np.exp(rng.uniform(*np.log(SIGMA_RANGE))))
    return tau, amp, window, sigma


def _clean(t, tau, amp):
    return (amp[:, None] * np.exp(-t[None, :] / tau[:, None])).sum(axis=0)


def simulate(secret: bytes, cid: str, n_repeats: int, dtype=np.float16):
    """The released acquisitions and the generating parameters. No labels."""
    tau, amp, window, sigma = params(secret, cid)
    t = np.linspace(0.0, window, N_SAMPLES)
    noise = _rng(secret, "noise", cid).normal(0.0, sigma, size=(n_repeats, N_SAMPLES))
    y = _clean(t, tau, amp)[None, :] + noise
    truth = {
        "case_id": cid,
        "tau": [round(float(x), 6) for x in tau],
        "amp": [round(float(x), 6) for x in amp],
        "window": round(window, 6),
        "sigma": round(sigma, 6),
    }
    return t.astype(np.float32), y.astype(dtype), truth


def reference_estimator(t, y):
    """NNLS lifetime spectrum, peaks grouped, three largest kept (ascending lifetime)."""
    D = np.hstack([np.exp(-t[:, None] / TAU_GRID[None, :]), np.ones((len(t), 1))])
    spec = nnls(D, y)[0][:-1]
    idx = np.where(spec > 1e-8)[0]
    if len(idx) == 0:
        return np.ones(N_COMPONENTS), np.zeros(N_COMPONENTS)
    groups, cur = [], [idx[0]]
    for i in idx[1:]:
        if i - cur[-1] <= 1:
            cur.append(i)
        else:
            groups.append(cur); cur = [i]
    groups.append(cur)
    taus = [float(np.exp(np.average(np.log(TAU_GRID[g]), weights=spec[g]))) for g in groups]
    amps = [float(spec[g].sum()) for g in groups]
    keep = np.argsort(amps)[::-1][:N_COMPONENTS]
    taus = [taus[i] for i in keep]; amps = [amps[i] for i in keep]
    while len(taus) < N_COMPONENTS:
        taus.append(taus[-1] if taus else 1.0); amps.append(0.0)
    o = np.argsort(taus)
    return np.array(taus)[o], np.array(amps)[o]


def outcome(t, y, tau, amp):
    """Per-component outcome of the reference estimator on ONE acquisition."""
    th, ah = reference_estimator(t, y)
    th, ah = th[ah > 0], ah[ah > 0]
    out = np.full(N_COMPONENTS, 2)
    if len(th) == 0:
        return out
    lt, lth = np.log(tau), np.log(th)
    near_peak = np.argmin(np.abs(lth[None, :] - lt[:, None]), axis=1)
    owner = np.argmin(np.abs(lt[None, :] - lth[:, None]), axis=1)
    for k in range(N_COMPONENTS):
        j = near_peak[k]
        if owner[j] != k:
            out[k] = 1
        elif abs(lth[j] - lt[k]) < TAU_TOL and abs(ah[j] - amp[k]) / amp[k] < AMP_TOL:
            out[k] = 0
    return out


def label_from_params(tau, amp, window, sigma, rng, n_mc: int = N_MC, dtype=np.float16):
    """The published label procedure, given parameters and a source of noise.

    Modal outcome of the reference estimator over n_mc single acquisitions;
    ties go to the less resolvable class."""
    tau, amp = np.asarray(tau, float), np.asarray(amp, float)
    t = np.linspace(0.0, window, N_SAMPLES)
    draws = _clean(t, tau, amp)[None, :] + rng.normal(0.0, sigma, size=(n_mc, N_SAMPLES))
    draws = draws.astype(dtype).astype(np.float64)       # the precision a solver's data has
    t64 = t.astype(np.float32).astype(np.float64)
    outs = np.array([outcome(t64, draws[m], tau, amp) for m in range(n_mc)])
    counts = np.stack([(outs == k).sum(0) for k in range(3)], axis=1)   # (component, class)
    classes = [max(k for k in range(3) if counts[j, k] == counts[j].max()) for j in range(N_COMPONENTS)]
    return classes, counts.tolist()


def label_case(secret: bytes, cid: str, n_mc: int = N_MC, dtype=np.float16):
    """The released label of a case: the label procedure on withheld keyed draws."""
    tau, amp, window, sigma = params(secret, cid)
    return label_from_params(tau, amp, window, sigma, _rng(secret, "mc", cid), n_mc, dtype)


def load_secret(path: Path) -> bytes:
    secret = Path(path).read_bytes()
    if len(secret) < 32:
        raise ValueError("the secret must be at least 32 bytes")
    return secret


def _label_job(args):
    secret, cid, n_mc, dtype_name = args
    return cid, label_case(secret, cid, n_mc, DTYPES[dtype_name])


def main(out: Path, secret_path: Path, n_cases: int, n_repeats: int, dtype_name: str,
         n_mc: int, workers: int):
    secret = load_secret(secret_path)
    dtype = DTYPES[dtype_name]
    out.mkdir(parents=True, exist_ok=True)
    (out / "traces").mkdir(exist_ok=True)
    records, seen = [], set()
    for i in range(n_cases):
        cid = case_id(secret, i)
        if cid in seen:
            raise ValueError(f"case id collision at index {i}")
        seen.add(cid)
        t, y, truth = simulate(secret, cid, n_repeats, dtype)
        np.savez_compressed(out / "traces" / f"{cid}.npz", t=t, y=y)
        records.append(truth)
    jobs = [(secret, r["case_id"], n_mc, dtype_name) for r in records]
    with get_context("fork").Pool(workers) as pool:
        labelled = dict(pool.map(_label_job, jobs, chunksize=20))
    for r in records:
        r["classes"], r["outcome_counts"] = labelled[r["case_id"]]
    (out / "truth.json").write_text(json.dumps(records, separators=(",", ":")))
    print(f"{n_cases} cases x {n_repeats} repeats ({dtype_name}), labels from {n_mc} draws -> {out}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("out", type=Path)
    p.add_argument("--secret", type=Path, required=True)
    p.add_argument("--n", type=int, default=6000)
    p.add_argument("--repeats", type=int, default=16)
    p.add_argument("--dtype", choices=sorted(DTYPES), default="float16")
    p.add_argument("--n-mc", type=int, default=N_MC)
    p.add_argument("--workers", type=int, default=8)
    a = p.parse_args()
    main(a.out, a.secret, a.n, a.repeats, a.dtype, a.n_mc, a.workers)
