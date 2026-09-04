# Multi-Exponential Relaxation Traces with Case-Dependent Identifiability

Documentation and provenance record for a synthetic dataset built to study a
specific question: **when can you tell how much a measurement actually
determines?**

**This repository is the canonical source record for the dataset.** The dataset is
original — not derived from, sampled from, or transformed from any existing
dataset, archive, repository or measurement campaign.

## What the dataset contains

| | |
|---|---|
| Cases | 6,000 (5,000 train / 1,000 test) |
| Components per case | 3 exponential decays |
| Samples per trace | 256 |
| Lifetimes | 0.05 to 60, log-uniform, reported ascending |
| Amplitudes | 0.3 to 2.0 |
| Observation window | 1.5 to 12, varies per case, **not disclosed** |
| Noise sigma | 0.05 to 0.80, log-uniform, **not disclosed** |
| Size | 14 MB |
| Licence | CC0 1.0 Universal |

## Why it is interesting

Decomposing a trace into exponentials is textbook. Knowing **which components the
measurement can actually support a claim about** is not. A component whose lifetime
exceeds its observation window has barely begun to decay before the measurement
stops; one shorter than a few sampling intervals is gone before the first points;
two with similar lifetimes cannot be told apart at all. Every component is labelled
`resolved`, `confounded` or `unobservable` accordingly.

| Label | Count | Share |
|---|---:|---:|
| resolved | 10,130 | 56.3% |
| confounded | 5,424 | 30.1% |
| unobservable | 2,446 | 13.6% |

Neither the window nor the noise level is published, so all three inputs to that
judgement have to be inferred from the trace.

Scored by Cohen's kappa over all components:

| Method | Kappa |
|---|---|
| Perfect | 1.0000 |
| Oracle labels with 20% randomised | 0.7624 |
| Gradient boosting on distilled features | **0.3281** |
| Tuned classical heuristic | 0.0481 |
| Random at class frequencies | 0.0263 |
| Uniform random, or all resolved | 0.0000 |

The classical heuristic sits at chance: a decomposition's own reported precision is
unreliable in exactly the regimes that make a component hard to resolve. A learned
classifier over the same outputs reaches 0.3281 on 1,500 training cases, so the
signal is there — it simply is not where the textbook points.

## Files

- [`DATASET_CARD.md`](DATASET_CARD.md) — schema, construction, quality checks
- [`VALIDATION_REPORT.json`](VALIDATION_REPORT.json) — machine-readable self-audit
- [`LICENSE`](LICENSE) — CC0 1.0 Universal

## Generator

The dataset is produced by a deterministic generator that regenerates it byte for
byte. **The generator ships with the dataset rather than here**, because it
reproduces the ground-truth parameters along with the traces, and publishing it
openly would disclose the answers for any benchmark built on this data.
`VALIDATION_REPORT.json` records a SHA-256 over all traces so a holder of the
generator can verify reproduction independently.

## Provenance

No human annotation, no language-model annotation, no pseudo-labeling and no
model-generated content is used anywhere. Labels are the exact parameters used to
synthesise each trace.

## Licence

CC0 1.0 Universal — https://creativecommons.org/publicdomain/zero/1.0/
