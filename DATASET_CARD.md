# Multi-Exponential Relaxation Traces Labelled by Component Resolvability

## Overview

Each case is one relaxing system — a sum of three exponential decays — observed
**sixteen times** over the same finite window at the same noise level:

```
y_r(t) = sum_k A_k exp(-t / tau_k) + eps_r,    eps_r ~ N(0, sigma^2),    r = 1..16
```

The point of the dataset is not the curve fit. It is that **how much the data
determines about each parameter varies enormously from case to case, and nothing
in the observation states it.** A component whose lifetime exceeds the
observation window has barely begun to decay, and its amplitude and lifetime
trade off almost freely. A component shorter than a few sampling intervals is
gone before the first points. Under heavy noise everything loosens. The generator
spans all of these regimes deliberately.

Every component carries a label describing what a **single acquisition** at that
case's noise level can support. The sixteen repeats are evidence for making that
judgement; they do not change what is being judged.

Why sixteen. On a single acquisition, roughly a fifth of all components sit so
close to a decision boundary that no solver can call them better than a coin
flip, and every competent approach converges on the same score. Repeated
acquisitions move those components back into the decidable range — but only for
a solver that uses them. On this release the same model scores 0.1512 higher on
all sixteen acquisitions than on the first alone.

Neither the observation window nor the noise level is published as a label. The
window is readable from the time axis; the noise level only from the spread
between acquisitions.

This is synthetic data. The generator is included as `generate.py`. It is keyed to
a secret that is not published, so it produces valid data from this family but
**does not reproduce this release** — see Construction.

## Number of Rows

- 6,000 independent cases (5,000 train / 1,000 test)
- 3 exponential components per case
- 16 repeated acquisitions per case, 256 samples each
- Lifetimes span 0.05 to 60, log-uniform
- Amplitudes span 0.3 to 2.0
- Observation windows span 1.5 to 12.0, varying per case
- Noise standard deviation spans 0.05 to 0.80, log-uniform, undisclosed

**Of the 18,000 components, 5,812 have a lifetime longer than their own
observation window and 1,216 decay within the first three samples.** Well over a
third of all components are therefore in a regime where the data constrains them
only weakly, and which third depends on the case.

## File Structure

```
traces/case_<id>.npz     6,000 files, one per case
truth.json               generating parameters for every case
generate.py              the generator, keyed to a withheld secret
DATASET_CARD.md
VALIDATION_REPORT.json
LICENSE
```

## Feature Table

### `traces/case_<id>.npz`

| Array | Type | Shape | Description |
|---|---|---|---|
| `t` | float32 | `(256,)` | Sample times, from 0 to the case's window length |
| `y` | float16 | `(16, 256)` | Sixteen independent acquisitions of the same system at those times |

Nothing else is stored. The noise level is not recorded in the file. The signal is
stored at half precision: the rounding error is at most 0.002, under 4% of the
smallest noise level in the dataset, and a paired comparison on identical cases
shows it changes the achievable score by 0.001.

### `truth.json`

One record per case:

| Field | Type | Description |
|---|---|---|
| `case_id` | string | Opaque case identifier |
| `tau` | list of 3 floats | Lifetimes, ascending. Sorting removes any labelling ambiguity |
| `amp` | list of 3 floats | Amplitudes, in the same order as `tau` |
| `window` | float | Observation length |
| `sigma` | float | Noise standard deviation of a single acquisition |

The resolvability label of each component is derived from these four fields by the
rule given below, so the dataset carries both the generating parameters and the
labels they imply.

## Construction

Lifetimes are drawn log-uniformly on `[0.05, 60]` and sorted ascending;
amplitudes uniformly on `[0.3, 2.0]`; the observation window uniformly on
`[1.5, 12]`; the noise standard deviation log-uniformly on `[0.05, 0.80]`. Each
acquisition is 256 evenly spaced samples of the clean sum plus independent
Gaussian noise; the sixteen acquisitions of a case share every parameter and
differ only in their noise.

**Keying.** Every draw — the parameters, the noise, and the case identifier
itself — derives from `HMAC-SHA256(secret, "<purpose>:<case>")`. The secret is not
published. Running `generate.py` produces a dataset from the same family; it does
not produce this one.

This replaces an earlier construction that derived every draw from a SHA-256 hash
of the case identifier and a seed printed in this card. That was a leak: the
released test identifiers, fed to the published generator, regenerated every test
trace byte for byte together with its exact parameters, and applying the label
rule scored **1.0000**. Re-keying the identifiers alone would not have closed it —
they were themselves `sha256(seed:i)`, so all 6,000 cases could be enumerated and
every released trace matched back to its generating case by content, 1,000 of
1,000. Only a withheld key closes both routes.

**Audited.** Every attack a reviewer could mount from public material was run
against this release. Feeding the released test identifiers to the earlier
published-seed generator scores kappa 0.0220. Running the keyed generator under
three guessed keys scores 0.0262, 0.0088 and 0.0207. Enumerating 6,000
identifiers under each guessed key and matching the regenerated traces by content
finds 0 of 1,000 test traces. For scale, 100 random keys score 0.0254 ± 0.0154,
maximum 0.0621, so every attack sits inside chance. The same harness given the
real secret recovers 1,000 of 1,000 test traces and scores 1.0000 — the secret is
the only thing standing between a solver and the answers.

No human annotation, no language-model annotation, no pseudo-labeling and no
model-generated content is used anywhere. Labels follow from the exact parameters
used to synthesise each trace.

## Quality Checks

- 6,000 cases, 6,000 trace files, no duplicate identifiers
- Every trace finite, `(16, 256)`, the same repeat count in every case
- Lifetimes stored ascending in every record
- Window and noise level never exposed to solvers
- Case identifiers are keyed and encode nothing about the answer
- Regeneration under the withheld secret is byte-identical; `prepare.py` is byte-identical across runs

## Component Labels

Every component carries a label describing what a single acquisition can support:

| Label | Meaning | Count | Share |
|---|---|---:|---:|
| `0` resolved | A single acquisition pins this component down | 10,227 | 56.8% |
| `1` confounded | Too close in lifetime to a neighbour to separate | 5,221 | 29.0% |
| `2` unobservable | Buried in noise, gone before the first samples, or barely decayed when the window ends | 2,552 | 14.2% |

A component is `unobservable` when its lifetime is under three sampling intervals,
its amplitude is below one noise standard deviation of a single acquisition, or it
has decayed less than 10% by the end of the window. It is `confounded` when its
nearest neighbour lies within 0.7 in log-lifetime. Otherwise it is `resolved`. These
are fixed thresholds on the generating parameters, not the output of an
identifiability analysis.

21 of the 27 possible label triples occur in the data.

## Difficulty

Scored by Cohen's kappa over all components, which corrects for chance. Measured on
the release as shipped:

| Method | Kappa |
|---|---|
| Perfect | 1.0000 |
| **Reference: NNLS lifetime spectrum of the averaged acquisitions plus the per-acquisition noise level, gradient boosting, all sixteen acquisitions** | **0.5797** |
| Summary statistics of the averaged acquisitions, a quarter of the training data | 0.4533 |
| The reference model given only the first acquisition of each case | 0.4285 |
| Estimate the parameters, then apply the published rule | 0.2052 |
| Random at the training class frequencies | 0.0020 |
| Calling every component resolved | 0.0000 |

The reference carries a bootstrap standard error of 0.0154 over test cases. Given
only the first acquisition, the same model loses 0.1512 — about ten standard
errors. That is the value of the repeats, and it accrues only to a solver that
uses them.

Estimating the parameters and applying the rule stays low. Sixteen acquisitions
pin the per-acquisition noise level to 0.8% median relative error, but the
lifetimes and amplitudes of neighbouring components are still recovered only to
34.5% and 51.7%, against 58.3% and 68.1% from a single acquisition. The thresholds
need far better than that, and a hard rule applied to a noisy estimate turns the
error into wrong labels.

## Intended Challenge Use

A challenge can withhold the parameters, the window and the noise level, and ask
only for the three labels. The task is then not estimation but **judging what a
measurement can support** — a categorical decision about the observation rather
than a quantity read out of it — with repeated acquisitions as the evidence.

It suits a **from-scratch** challenge in particular. These traces are a synthetic
signal family that no public checkpoint has seen: there is no backbone to fine-tune
and no embedding to borrow, so an architecture has to be designed and trained from
random initialisation on the provided data alone.

## License

CC0 1.0 Universal (Public Domain Dedication) —
https://creativecommons.org/publicdomain/zero/1.0/

Entirely synthetic, generated by the included script, containing no third-party
data and no personal data.
