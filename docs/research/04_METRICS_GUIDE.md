# Metrics Guide

## Purpose
Define how results are measured and interpreted in this repository.

## Metric Groups

### 1. Status / Feasibility Metrics (mandatory)
- status on shared instances
- solved / timeout / unsat / error counts

Interpretation rule:
- if status behavior diverges unexpectedly, runtime claims are secondary until the cause is understood

### 2. Objective Metrics (mandatory inside objective-aligned sets)
- reported objective value
- matching / mismatching objective cases on shared finished instances

Critical caveat:
- true `Lmax` is `max(C_j - d_j)` and may be negative
- clamped objective `max(0, C_j - d_j)` is different
- current active solver code is aligned to true `Lmax`

Current implementation note:
- `seqcounter`, `seqcardenc`, `seqcardenc_ver2`, `seqcardenc_ver3`, `pbenc`, `basicsat`, and `gurobi`: true `Lmax` behavior
- historical workbooks may predate this alignment

Interpretation rule:
- compare objective values only after confirming the results were produced under the aligned code state
- if an analysis spans old and new results, label it explicitly as a code-state mismatch

### 3. Runtime Metrics (mandatory)
- `time_s`
- solved count
- timeout count
- paired runtime deltas on shared solved sets

Current repository note:
- `time_s` in result workbooks is runner subprocess wall time.
- It includes solver execution plus surrounding overhead such as parsing, preprocessing, solution formatting, file writing, and process startup/teardown.
- Do not describe `time_s` as pure solver-search time unless a separate metric was collected.

Recommended summaries:
- mean runtime on the shared comparable set
- median runtime on the shared comparable set
- faster / slower counts
- hard-case subset summary

### 4. SAT Internal Metrics (recommended)
- conflicts
- decisions
- propagations
- restarts

Interpretation rule:
- SAT internal changes are supporting evidence, not a standalone victory condition

### 5. Structural Diagnostics (optional)
- clause count
- variable count
- clause-length profile
- graph or dataset characteristics when they explain hard cases

Interpretation rule:
- clause count alone is not sufficient evidence of improvement

## Comparison Protocol
For each candidate solver or encoding variant:
1. verify dataset lane and filelist equality
2. verify preprocessing equality
3. verify timeout equality
4. verify objective semantics
5. compare status on shared instances
6. compare objective only within an objective-aligned set
7. compare runtime on the comparable set
8. inspect hard-case divergences
9. use SAT internals to explain, not to replace, runtime evidence

## Minimum Conclusion Format
- Facts:
  - directly observed metrics
- Interpretation:
  - likely mechanism or limitation
- Recommendation:
  - keep, reject, or iterate

## Red Flags
Treat any of the following as a warning:
- solver groups or result files from different objective-semantics code states reported in one `Lmax` table without annotation
- folder counts used instead of authoritative filelists
- runtime comparison made on different shared-instance sets without saying so
- improvement claimed from clause count alone
