# Multi-Exponential Relaxation Traces Labelled by Estimator Recovery

## Overview

Each case is one relaxing system — a sum of three exponential decays — observed **sixteen times** over the same finite window at the same noise level:

```
y_r(t) = sum_k A_k exp(-t / tau_k) + eps_r,    eps_r ~ N(0, sigma^2),    r = 1..16
```

Every component carries a label describing **what a fixed reference estimator actually recovers from a single acquisition of that system**, measured by running the estimator on 129 further acquisitions that are not released. The label is an observed behaviour, not a threshold on the parameters: it depends jointly on how close the lifetimes are, how the amplitudes compare, where the observation window ends and how much noise sits under the signal.

The sixteen released acquisitions are evidence for predicting that behaviour; they are not the draws it was measured on. Neither the observation window nor the noise level is published as a label: the window is readable from the time axis, the noise level only from the spread between acquisitions.

This is synthetic data. The generator is included as `generate.py`. It is keyed to a secret that is not published, so it produces valid data from this family but **does not reproduce this release** — see Construction.

## Number of Rows

- 6,000 independent cases (5,000 train / 1,000 test)
- 3 exponential components per case, 18,000 labelled components
- 16 released acquisitions per case, 256 samples each
- 129 withheld acquisitions per case, used only to measure the labels
- Lifetimes 0.05 to 60, log-uniform; amplitudes 0.3 to 2.0; windows 1.5 to 12.0; noise standard deviation 0.05 to 0.80, log-uniform, undisclosed

## File Structure

```
traces/case_<id>.npz     6,000 files, one per case
truth.json               generating parameters, labels and outcome counts for every case
generate.py              the generator and label procedure, keyed to a withheld secret
DATASET_CARD.md
VALIDATION_REPORT.json
LICENSE
```

## Feature Table

### `traces/case_<id>.npz`

| Array | Type | Shape | Description |
|---|---|---|---|
| `t` | float32 | `(256,)` | Sample times, from 0 to the case's window length |
| `y` | float16 | `(16, 256)` | Sixteen independent acquisitions of the same system |

The noise level is not recorded in the file. Half-precision rounding is at most 0.002, under 4% of the smallest noise level.

### `truth.json`

| Field | Type | Description |
|---|---|---|
| `case_id` | string | Opaque case identifier |
| `tau` | 3 floats | Lifetimes, ascending |
| `amp` | 3 floats | Amplitudes, in the same order |
| `window` | float | Observation length |
| `sigma` | float | Noise standard deviation of a single acquisition |
| `classes` | 3 ints | The label of each component |
| `outcome_counts` | 3 × 3 ints | Per component, how many of the 129 withheld draws ended resolved / confounded / unobservable |

## Construction

Lifetimes are drawn log-uniformly on `[0.05, 60]` and sorted; amplitudes uniformly on `[0.3, 2.0]`; the window uniformly on `[1.5, 12]`; the noise standard deviation log-uniformly on `[0.05, 0.80]`. Each acquisition is 256 evenly spaced samples of the clean sum plus independent Gaussian noise.

**Labels.** For each case, 129 further single acquisitions are drawn and stored at the same half precision as the released ones. The reference estimator — non-negative least squares on 72 log-spaced lifetimes from 0.02 to 200 plus a constant, adjacent non-zero weights grouped into peaks, the three largest peaks kept — is run on each. Every true component is scored per draw: **resolved** if the nearest estimated peak is within 25% in lifetime and 50% in amplitude and is nearer to it than to any other component; **confounded** if the nearest peak is nearer to a neighbouring component; **unobservable** otherwise. The label is the most frequent outcome; ties (147 of 18,000 components) go to the less resolvable class. The full outcome counts are stored in `truth.json`.

**Label stability.** On 600 cases labelled twice from independent sets of draws, two 128-draw labellings agree at kappa 0.844, and a 128-draw label agrees with a 256-draw label at kappa 0.919. One component in five is genuinely borderline — its most frequent outcome wins by under ten points — which is a property of the estimator on that configuration, not of the label count.

**Keying.** Every draw — parameters, released noise, withheld label noise and the case identifier — derives from `HMAC-SHA256(secret, "<purpose>:<case>")`. The secret is not published. An earlier construction derived every draw from a seed printed in this card; the released test identifiers fed to the published generator then regenerated every test trace byte for byte, and its labels with it. Only a withheld key closes that route, and enumerating identifiers to match traces by content as well.

**Audited** on this release, against every attack available from public material. Feeding the released test identifiers to the earlier published-seed generator and applying the label procedure scores kappa 0.0519. The keyed generator under three guessed keys scores 0.0798, 0.0527 and 0.0683. Enumerating 6,000 identifiers under each guessed key finds 0 of 1,000 test traces by content. For scale, the true test labels shuffled across cases score 0.0591 ± 0.0133 (maximum 0.1018), so every attack sits inside chance. The same harness given the real secret reproduces all 1,000 test labels exactly and matches all 1,000 test traces.

No human annotation, no language-model annotation, no pseudo-labelling and no model-generated content is used anywhere. Labels follow deterministically from the generating parameters, the keyed withheld draws and the stated estimator.

## Quality Checks

- 6,000 cases, 6,000 trace files, no duplicate identifiers
- Every trace finite, `(16, 256)`, the same repeat count in every case
- Lifetimes stored ascending in every record; labels in ascending-lifetime order
- Window and noise level never exposed to solvers; case identifiers keyed and uninformative
- Regeneration under the withheld secret is byte-identical; `prepare.py` is byte-identical across runs

## Component Labels

| Label | Meaning | Count | Share |
|---|---|---:|---:|
| `0` resolved | The estimator recovers this component from one acquisition, in most draws | 3,309 | 18.4% |
| `1` confounded | Its signal most often lands in a peak shared with a neighbour | 6,577 | 36.5% |
| `2` unobservable | Most often no estimated peak is attributable to it | 8,114 | 45.1% |

All 27 possible label triples occur. The labels agree with a fixed-threshold labelling of the true parameters (lifetime under three sampling intervals, amplitude under one noise standard deviation or under 10% decayed → unobservable; neighbour within 0.7 in log-lifetime → confounded) only at kappa 0.1406.

## Difficulty

Scored by Cohen's kappa over all components, on the release as shipped:

| Method | Kappa |
|---|---|
| Perfect | 1.0000 |
| **NNLS spectrum of the averaged acquisitions plus per-acquisition noise level, gradient boosting** | **0.5086** |
| Summary statistics of the averaged acquisitions, a quarter of the training data | 0.3729 |
| The same model given only the first acquisition | 0.4156 |
| The estimator on each released acquisition, most frequent outcome, no learning | 0.2064 |
| Fixed cut-offs on fitted parameters | 0.0606 |
| Random at class frequencies | 0.0224 |
| All resolved | 0.0000 |

Bootstrap standard error of the reference: 0.0143. The sixteen acquisitions are worth 0.0930 over the first alone.

## Intended Challenge Use

A challenge can withhold the parameters, the window and the noise level for test cases and ask only for the three labels: a prediction of an estimator's reliability on a signal it has not yet been run on, with repeated acquisitions as the evidence. The signal family is synthetic and unlike anything in a public checkpoint, which suits a from-scratch challenge.

## License

CC0 1.0 Universal (Public Domain Dedication) — https://creativecommons.org/publicdomain/zero/1.0/

Entirely synthetic, generated by the included script, containing no third-party data and no personal data.
