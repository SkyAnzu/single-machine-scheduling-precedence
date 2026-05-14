# Internal Research Protocol Scope

## Purpose
This document defines the internal research scope for this repository.

The protocol targets comparative evaluation of SAT encodings for single-machine scheduling with precedence and time-window style constraints, under reproducible and fair conditions.

## Primary Research Questions
1. Within the `seqcardenc` family, which version gives the best trade-off between correctness, runtime, and SAT internal behavior?
2. For a given dataset lane and timeout profile, what are the hard-case regressions and likely root causes?
3. Optionally, how does the SAT lane compare to `gurobi` as a cross-paradigm baseline?

## In Scope
- SAT family comparisons for:
  - `seqcardenc`
  - `seqcardenc_ver2`
  - `seqcardenc_ver3`
  - future `seqcardenc_*` versions
- Correctness checks:
  - status consistency on shared instances
  - objective (`Lmax`) consistency on shared `FINISHED` instances
- Runtime and timeout behavior under fixed timeout profile.
- SAT internals when collected:
  - decisions
  - conflicts
  - propagations

## Out of Scope
- Inferential statistical testing (for example, p-values or hypothesis tests).
- Cross-machine benchmarking claims without controlled machine conditions.
- Claims based only on clause count.

## Evaluation Lanes

### Lane A (mandatory): SAT Family
- Compare versions only inside the `seqcardenc` family.
- This lane is required for every encoding change.

### Lane B (optional): Cross-Paradigm Baseline
- Compare SAT against `gurobi` on the same instance list and timeout profile.
- This lane is optional and should be used when positioning SAT in the broader optimization picture.

### Lane C (optional): Diagnostic Deep Dive
- Used for propagation diagnostics and root-cause analysis.
- Keep this separate from timed benchmark runs if instrumentation adds overhead.

## Baseline and Acceptance Policy
- Current operational baseline: `seqcardenc_ver2`.
- A candidate version can only be called "better" if:
  - correctness is preserved (status and `Lmax` consistency), and
  - runtime and/or SAT internals provide supporting evidence.
- If hard-case regressions exist, they must be explicitly reported.

## Required Deliverables Per Benchmark Cycle
1. Run metadata (dataset lane, timeout profile, solver set, machine context).
2. Correctness table (status + `Lmax` consistency).
3. Runtime summary (solved/timeout counts and paired deltas).
4. Hard-case regression table.
5. SAT internal summary (when collected).
6. Evidence-based conclusion and next steps.
