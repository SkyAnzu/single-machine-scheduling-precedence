# Metrics Guide

## Purpose
Define how benchmark metrics are collected and interpreted for internal comparisons.

## Metric Groups

### 1) Correctness Metrics (mandatory)
- Status consistency on shared instances.
- `Lmax` consistency on shared `FINISHED` instances.

Interpretation rule:
- If correctness is inconsistent, performance claims are invalid until resolved.

### 2) Runtime Metrics (mandatory)
- `time_s` on finished runs.
- solved count.
- timeout count.

Recommended summaries:
- mean and median runtime on shared `FINISHED` set
- paired runtime deltas between compared versions
- hard-case subset summary

### 3) SAT Internal Metrics (recommended when available)
- decisions
- conflicts
- propagations

Interpretation rule:
- SAT internal shifts should be used as supporting evidence for runtime behavior.

## Clause-Structure Diagnostics (optional)
- total clause count
- variable count
- clause-length profile (unit/binary/ternary/other)

Interpretation rule:
- Clause count alone is not sufficient evidence of runtime improvement.

## Propagation Diagnostics (optional deep-dive)
- forward check examples (for example, `S -> A` behavior)
- reverse check examples (for example, `A=0` implication strength toward `S`)

Use case:
- explain regressions or unexpected SAT internal behavior.

## Comparison Protocol
For each candidate `seqcardenc_*` versus reference:
1. Shared-instance status comparison.
2. Shared-`FINISHED` `Lmax` comparison.
3. Runtime paired comparison.
4. Hard-case regression extraction.
5. SAT internal comparison when collected.

## Required Conclusion Format
- Facts: direct observed metrics.
- Interpretation: likely mechanism.
- Recommendation: keep, reject, or iterate.

Claims must map back to measured evidence.
