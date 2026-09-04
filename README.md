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
| Observation window | 2 to 30, varies per case, **not disclosed** |
| Noise sigma | 0.005 to 0.30, log-uniform, **not disclosed** |
| Size | 14 MB |
| Licence | CC0 1.0 Universal |

## Why it is interesting

Fitting a sum of exponentials is textbook. Knowing *how much the fit is worth* is
not. A component whose lifetime exceeds its observation window has barely begun to
decay before the measurement stops, and its amplitude and lifetime trade off
almost freely. A component shorter than a few sampling intervals is gone before
the first points. Under heavy noise everything loosens.

**Of the 18,000 components, 3,783 have a lifetime longer than their own
observation window and 2,961 decay within the first three samples.** About a third
sit in a regime where the data constrains them only weakly — and neither the
window nor the noise level is published, so which third is a judgement to be made
from the trace.

Scoring interval predictions by the normalised Winkler interval score at nominal
80%, where reporting the prior range scores 0:

| Method | Score |
|---|---|
| Near-exact oracle (±1%) | 0.9927 |
| Oracle centre, 2× too wide | 0.6669 |
| Tuned classical fit + asymptotic CI | 0.4645 |
| Global mean point estimate | 0.0963 |
| Prior range | 0.0000 |

The classical approach is **miscalibrated**, not just beaten: its intervals cover
the truth 71.4% of the time against a nominal 80%, because asymptotic confidence
intervals fail exactly where the problem is ill-conditioned. Sweeping the
confidence multiplier only lowers the score — widening rescues the degenerate
cases and ruins the well-determined ones.

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
