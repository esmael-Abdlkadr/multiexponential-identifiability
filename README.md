# Multi-Exponential Relaxation Traces Labelled by Estimator Recovery

Documentation and provenance record for a synthetic dataset built to study one question: **will a standard estimator actually recover each component of a decaying signal from a single measurement?**

**This repository is the canonical source record for the dataset.** The dataset is original — not derived from, sampled from, or transformed from any existing dataset, archive, repository or measurement campaign.

## What the dataset contains

| | |
|---|---|
| Cases | 6,000 (5,000 train / 1,000 test) |
| Components per case | 3 exponential decays |
| Released acquisitions per case | 16 repeated measurements of the same system |
| Withheld acquisitions per case | 129, used only to measure the labels |
| Samples per acquisition | 256 |
| Lifetimes | 0.05 to 60, log-uniform, reported ascending |
| Amplitudes | 0.3 to 2.0 |
| Observation window | 1.5 to 12, varies per case, **not disclosed** |
| Noise sigma | 0.05 to 0.80, log-uniform, **not disclosed** |
| Storage | float16; rounding error under 4% of the smallest noise level |
| Licence | CC0 1.0 Universal |

## The labels

Each component's label is **what a fixed reference estimator was observed to do** on single acquisitions of that system — not a threshold on its parameters. A non-negative least-squares lifetime spectrum is fitted to each of 129 withheld acquisitions, and every true component is scored per draw as **resolved** (a peak within 25% in lifetime and 50% in amplitude, closest to it), **confounded** (its nearest peak belongs to a neighbour) or **unobservable** (neither). The label is the most frequent outcome.

| Label | Count | Share |
|---|---:|---:|
| resolved | 3,309 | 18.4% |
| confounded | 6,577 | 36.5% |
| unobservable | 8,114 | 45.1% |

These labels agree with a fixed-threshold labelling of the true parameters only at kappa 0.1406: estimator behaviour depends jointly on the whole configuration of a case, not on any single cut-off.

Scored by Cohen's kappa over all components, on the release as shipped:

| Method | Kappa |
|---|---|
| Perfect | 1.0000 |
| **NNLS spectrum + per-acquisition noise level, gradient boosting, all 16 acquisitions** | **0.5086** |
| Summary statistics of the averaged acquisitions | 0.3729 |
| The same model given only the first acquisition | 0.4156 |
| The estimator on each released acquisition, most frequent outcome, no learning | 0.2064 |
| Fixed cut-offs on fitted parameters | 0.0606 |
| Random at class frequencies | 0.0224 |
| All resolved | 0.0000 |

## Files

- [`DATASET_CARD.md`](DATASET_CARD.md) — schema, construction, label procedure, quality checks
- [`VALIDATION_REPORT.json`](VALIDATION_REPORT.json) — machine-readable self-audit, including the leak audit
- [`generate.py`](generate.py) — the generator and label procedure, keyed to a withheld secret
- [`LICENSE`](LICENSE) — CC0 1.0 Universal

## Generator

The generator is published here, and it is keyed to a secret that is not. Every draw — the parameters, the released noise, the withheld label draws and the case identifiers — derives from `HMAC-SHA256(secret, "<purpose>:<case>")`. Running it produces valid data from this family; it does not reproduce the released dataset or its labels.

Audited against every attack available from public material — the earlier published-seed generator on the released identifiers, the keyed generator under guessed keys, and enumerating identifiers to match traces by content — every attack scores inside chance (0.0591 ± 0.0133 for shuffled labels) with 0 content matches, while the same harness given the real secret reproduces every test label and trace. The numbers are in `VALIDATION_REPORT.json`.

## Provenance

No human annotation, no language-model annotation, no pseudo-labeling and no model-generated content is used anywhere. Labels follow deterministically from the generating parameters, the keyed withheld draws and the stated estimator.

## Licence

CC0 1.0 Universal — https://creativecommons.org/publicdomain/zero/1.0/
