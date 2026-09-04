# Multi-Exponential Relaxation Traces Labelled by Component Resolvability

## Overview

Each case is one noisy observation of a relaxing system: a sum of three
exponential decays, sampled on a finite window, with additive Gaussian noise.

```
y(t) = sum_k A_k exp(-t / tau_k) + eps,    eps ~ N(0, sigma^2)
```

The point of the dataset is not the curve fit. It is that **how much the data
determines about each parameter varies enormously from case to case, and nothing
in the observation states it.** A component whose lifetime exceeds the
observation window has barely begun to decay, and its amplitude and lifetime
trade off almost freely. A component shorter than a few sampling intervals is
gone before the first points. Under heavy noise everything loosens. The generator
spans all of these regimes deliberately.

Neither the observation window nor the noise level is published as a label. Both
are visible only through the trace itself.

This is synthetic data with a reproducible generator, included as `generate.py`.

## Number of Rows

- 6,000 independent cases (5,000 train / 1,000 test)
- 3 exponential components per case
- 256 samples per trace
- Lifetimes span 0.05 to 60, log-uniform
- Amplitudes span 0.3 to 2.0
- Observation windows span 1.5 to 12.0, varying per case
- Noise standard deviation spans 0.05 to 0.80, log-uniform, undisclosed

**Of the 18,000 components, 5,819 have a lifetime longer than their own
observation window and 1,125 decay within the first three samples.** Well over a
third of all components are therefore in a regime where the data constrains them
only weakly, and which third depends on the case.

## File Structure

```
traces/case_<id>.npz     6,000 files, one per case
truth.json               generating parameters for every case
generate.py              the generator, deterministic under seed 20260905
DATASET_CARD.md
VALIDATION_REPORT.json
LICENSE
```

## Feature Table

### `traces/case_<id>.npz`

| Array | Type | Shape | Description |
|---|---|---|---|
| `t` | float32 | `(256,)` | Sample times, from 0 to the case's window length |
| `y` | float32 | `(256,)` | The observed signal at those times |

Nothing else is stored. The noise level is not recorded in the file.

### `truth.json`

One record per case:

| Field | Type | Description |
|---|---|---|
| `case_id` | string | Opaque case identifier |
| `tau` | list of 3 floats | Lifetimes, ascending. Sorting removes any labelling ambiguity |
| `amp` | list of 3 floats | Amplitudes, in the same order as `tau` |
| `window` | float | Observation length. Held back from solvers |
| `sigma` | float | Noise standard deviation. Held back from solvers |

The resolvability label of each component is derived from these four fields by the
rule given below, so the dataset carries both the generating parameters and the
labels they imply.

## Construction

Lifetimes are drawn log-uniformly on `[0.05, 60]` and sorted ascending;
amplitudes uniformly on `[0.3, 2.0]`; the observation window uniformly on
`[1.5, 12]`; the noise standard deviation log-uniformly on `[0.05, 0.80]`. The
trace is 256 evenly spaced samples of the clean sum plus independent Gaussian
noise.

Every draw derives from a SHA-256 hash of the case identifier and the global seed
20260905, so the dataset regenerates byte for byte.

No human annotation, no language-model annotation, no pseudo-labeling and no
model-generated content is used anywhere. Labels are the exact parameters used to
synthesise each trace.

## Quality Checks

- 6,000 cases, 6,000 trace files, no duplicate identifiers
- All traces finite float32 of length 256
- Lifetimes stored ascending in every record
- Window and noise level never exposed to solvers
- Case identifiers are opaque hashes and encode nothing about the answer
- Deterministic regeneration verified by SHA-256 over all traces

## Component Labels

Every component carries a label describing what the measurement can support:

| Label | Meaning | Count | Share |
|---|---|---:|---:|
| `0` resolved | The trace pins this component down | 10,130 | 56.3% |
| `1` confounded | Too close in lifetime to a neighbour to separate | 5,424 | 30.1% |
| `2` unobservable | Buried in noise, gone before the first samples, or barely decayed when the window ends | 2,446 | 13.6% |

A component is `unobservable` when its lifetime is under three sampling intervals,
its amplitude-to-noise ratio is below 1, or it has decayed less than 10% by the
end of the window. It is `confounded` when its nearest neighbour lies within 0.7
in log-lifetime. Otherwise it is `resolved`. All three inputs to that rule — the
window, the noise level, the neighbouring lifetimes — are hidden from solvers.

21 of the 27 possible label triples occur in the data.

## Difficulty

Scored by Cohen's kappa over all components, which corrects for chance:

| Method | Kappa |
|---|---|
| Perfect | 1.0000 |
| Oracle labels with 20% noise | 0.7624 |
| **Gradient boosting on features distilled from a curve decomposition** | **0.3281** |
| Tuned classical heuristic (decompose, then judge from reported precision) | 0.0481 |
| Random at the class frequencies | 0.0263 |
| Uniform random, or calling every component resolved | 0.0000 |

The classical heuristic sits at chance. Reading resolvability off a decomposition's
own reported precision does not work, because that precision is unreliable in
exactly the regimes that make a component hard to resolve. A learned classifier
over the same outputs reaches 0.3281 using only 1,500 training cases and eleven
hand-built features, so the signal is there — it simply is not where the textbook
points.

## Intended Challenge Use

A challenge can withhold the parameters, the window and the noise level, and ask
only for the three labels. The task is then not estimation but **judging what a
measurement can support** — a categorical decision about the observation rather
than a quantity read out of it.

## License

CC0 1.0 Universal (Public Domain Dedication) —
https://creativecommons.org/publicdomain/zero/1.0/

Entirely synthetic, generated by the included script, containing no third-party
data and no personal data.
