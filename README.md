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
| Acquisitions per case | 16 repeated measurements of the same system |
| Samples per acquisition | 256 |
| Lifetimes | 0.05 to 60, log-uniform, reported ascending |
| Amplitudes | 0.3 to 2.0 |
| Observation window | 1.5 to 12, varies per case, **not disclosed** |
| Noise sigma | 0.05 to 0.80, log-uniform, **not disclosed** |
| Storage | float16; rounding error under 4% of the smallest noise level |
| Size | 49 MB |
| Licence | CC0 1.0 Universal |

## Why it is interesting

Decomposing a trace into exponentials is textbook. Knowing **which components a
measurement can actually support a claim about** is not. A component whose lifetime
exceeds its observation window has barely begun to decay before the measurement
stops; one shorter than a few sampling intervals is gone before the first points;
two with similar lifetimes cannot be told apart at all. Every component is labelled
`resolved`, `confounded` or `unobservable` according to what a **single**
acquisition supports.

| Label | Count | Share |
|---|---:|---:|
| resolved | 10,227 | 56.8% |
| confounded | 5,221 | 29.0% |
| unobservable | 2,552 | 14.2% |

Neither the window nor the noise level is published, so all three inputs to that
judgement have to be inferred from the signal.

Each case carries sixteen acquisitions because a single one is not enough to decide
the hard cases. On one acquisition, about a fifth of all components sit so close to
a decision boundary that noise has erased the distinction, and every competent
approach converges on the same score. Repeated acquisitions move those components
back into the decidable range — but only for a method that uses them.

Scored by Cohen's kappa over all components, on the release as shipped:

| Method | Kappa |
|---|---|
| Perfect | 1.0000 |
| **NNLS lifetime spectrum + per-acquisition noise level, gradient boosting, all 16 acquisitions** | **0.5797** |
| Summary statistics of the averaged acquisitions | 0.4533 |
| The same gradient-boosting model given only the first acquisition | 0.4285 |
| Estimate the parameters, then apply the labelling rule | 0.2052 |
| Random at class frequencies | 0.0020 |
| All resolved | 0.0000 |

Using the sixteen acquisitions is worth 0.1512 on identical cases — about ten
bootstrap standard errors. Fitting the parameters and thresholding them stays low:
sixteen acquisitions pin the noise level to 0.8%, but neighbouring lifetimes and
amplitudes remain ill-conditioned (34.5% and 51.7% median relative error).

## Files

- [`DATASET_CARD.md`](DATASET_CARD.md) — schema, construction, labelling rule, quality checks
- [`VALIDATION_REPORT.json`](VALIDATION_REPORT.json) — machine-readable self-audit, including the leak audit
- [`generate.py`](generate.py) — the generator, keyed to a withheld secret
- [`LICENSE`](LICENSE) — CC0 1.0 Universal

## Generator

The generator is published here, and it is keyed to a secret that is not. Every
draw — the parameters, the noise, and the case identifiers — derives from
`HMAC-SHA256(secret, "<purpose>:<case>")`. Running it produces valid data from this
family; it does not reproduce the released dataset, and so discloses nothing about
any benchmark built on it.

An earlier version of this dataset derived every draw from a seed stated in its
documentation. That was reproducible from public material: the released test
identifiers, fed to the generator, regenerated every test trace exactly, and the
labelling rule applied to the recovered parameters scored 1.0000. That construction
is retired. The current one was audited against every attack available from public
material — including enumerating identifiers and matching traces by content — and
all of them score at chance, while the same attacks run with the real secret recover
every test trace. The numbers are in `VALIDATION_REPORT.json`, which also records a
SHA-256 over all released traces so the dataset's integrity can be checked.

## Provenance

No human annotation, no language-model annotation, no pseudo-labeling and no
model-generated content is used anywhere. Labels follow from the exact parameters
used to synthesise each case, by a fixed rule stated in `DATASET_CARD.md`.

## Licence

CC0 1.0 Universal — https://creativecommons.org/publicdomain/zero/1.0/
