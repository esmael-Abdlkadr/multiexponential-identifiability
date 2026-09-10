#!/usr/bin/env python3
"""Multi-exponential relaxation traces, with repeated acquisitions per case.

Each case is one relaxing system observed several times over the same window,
at the same noise level:

    y_r(t) = sum_k A_k exp(-t / tau_k) + eps_r,   eps_r ~ N(0, sigma^2),  r = 1..R

The component labels describe what a SINGLE acquisition at that noise level can
support. The repeats are evidence for making that judgement, not a change to
what is being judged. That is what gives the task room for skill: one noisy
trace does not carry enough information to place components near a decision
boundary, so every competent solver lands on the same plateau; several repeats
do, but only a solver that actually inverts the signal well converts them into
better decisions.

Keying
------
Every draw is derived from HMAC-SHA256(secret, "<purpose>:<case>"). **The secret
is not published.** Running this script produces *a* valid dataset from this
family; it does not reproduce *the* released one.

That is deliberate. The previous release drew every parameter from SHA-256 of
the case identifier and a seed printed in the dataset card, and kept those case
identifiers in the released test split. Feeding the public test ids to the
published generator regenerated every test trace byte for byte, with its exact
lifetimes, amplitudes, window and noise level, and applying the published label
rule scored 1.0000 through the grader. Re-keying the ids alone would not have
closed it: the ids were sha256(seed:i) for i in 0..5999, so all 6,000 cases could
be enumerated and every released trace matched back to its generating case by
content (1000/1000). Only a withheld key closes both routes.

Case identifiers are also keyed, so they cannot be enumerated.

Usage
-----
    python generate.py OUT --secret PATH [--n 6000] [--repeats 16] [--dtype float16]
"""
import argparse
import hashlib
import hmac
import json
from pathlib import Path

import numpy as np

N_COMPONENTS = 3
N_SAMPLES = 256
TAU_RANGE = (0.05, 60.0)        # log-uniform
AMP_RANGE = (0.3, 2.0)          # uniform
WINDOW_RANGE = (1.5, 12.0)      # uniform, varies per case
SIGMA_RANGE = (0.05, 0.80)      # log-uniform, never disclosed to solvers
DTYPES = {"float16": np.float16, "float32": np.float32}


def _key(secret: bytes, *parts) -> bytes:
    return hmac.new(secret, ":".join(str(p) for p in parts).encode(), hashlib.sha256).digest()


def _rng(secret: bytes, *parts) -> np.random.Generator:
    return np.random.default_rng(int.from_bytes(_key(secret, *parts)[:8], "big"))


def case_id(secret: bytes, index: int) -> str:
    return "case_" + _key(secret, "case", index).hex()[:12]


def simulate(secret: bytes, cid: str, n_repeats: int, dtype=np.float16):
    rng = _rng(secret, "params", cid)
    tau = np.sort(np.exp(rng.uniform(*np.log(TAU_RANGE), size=N_COMPONENTS)))
    amp = rng.uniform(*AMP_RANGE, size=N_COMPONENTS)
    window = float(rng.uniform(*WINDOW_RANGE))
    sigma = float(np.exp(rng.uniform(*np.log(SIGMA_RANGE))))

    t = np.linspace(0.0, window, N_SAMPLES)
    clean = (amp[:, None] * np.exp(-t[None, :] / tau[:, None])).sum(axis=0)
    noise = _rng(secret, "noise", cid).normal(0.0, sigma, size=(n_repeats, N_SAMPLES))
    y = clean[None, :] + noise

    truth = {
        "case_id": cid,
        "tau": [round(float(x), 6) for x in tau],
        "amp": [round(float(x), 6) for x in amp],
        "window": round(window, 6),
        "sigma": round(sigma, 6),
    }
    return t.astype(np.float32), y.astype(dtype), truth


def load_secret(path: Path) -> bytes:
    secret = Path(path).read_bytes()
    if len(secret) < 32:
        raise ValueError("the secret must be at least 32 bytes")
    return secret


def main(out: Path, secret_path: Path, n_cases: int, n_repeats: int, dtype_name: str):
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
    (out / "truth.json").write_text(json.dumps(records, separators=(",", ":")))
    print(f"{n_cases} cases x {n_repeats} repeats ({dtype_name}) -> {out}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("out", type=Path)
    p.add_argument("--secret", type=Path, required=True)
    p.add_argument("--n", type=int, default=6000)
    p.add_argument("--repeats", type=int, default=16)
    p.add_argument("--dtype", choices=sorted(DTYPES), default="float16")
    a = p.parse_args()
    main(a.out, a.secret, a.n, a.repeats, a.dtype)
