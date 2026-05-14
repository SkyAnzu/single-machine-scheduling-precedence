# SMSP Repository Agent Protocol

## Purpose
This file defines agent behavior for this repository.

Primary goal: support internal research on SAT encodings for single-machine scheduling with precedence and time-window style constraints.

## Repository Scope
- Default dataset lane: current `2016/Ins` workflow used by runners in `Test/`.
- Primary solver family: `seqcardenc`, `seqcardenc_ver2`, `seqcardenc_ver3`, and future `seqcardenc_*` versions.
- Optional external baseline lane: `gurobi`.

## Non-Negotiable Rules
1. Correctness first.
   - Never claim improvement if status consistency or objective consistency is broken.
2. Fair comparison required.
   - Same instance list, same preprocessing, same timeout profile, same machine context.
3. No performance claim from clause count alone.
   - Runtime and solver statistics must support conclusions.
4. Report regressions honestly.
   - If a new encoding is worse on hard cases, state it explicitly and provide evidence.

## Evaluation Lanes

### Lane A: SAT Family Benchmark (mandatory)
- Compare versions inside the `seqcardenc` family.
- Required outputs:
  - Correctness: status and Lmax consistency.
  - Runtime: solved/timeout and wall-clock summaries.
  - SAT internals: decisions, conflicts, propagations (when collected).

### Lane B: Cross-Paradigm Baseline (optional)
- Compare SAT lane against `gurobi` to position SAT in the broader optimization picture.
- This lane is optional per run and not required for every benchmark.

### Lane C: Diagnostic Deep-Dive (optional)
- Use for propagation diagnostics, clause-structure analysis, and root-cause checks.
- Keep separate from the timed benchmark lane when instrumentation overhead can bias runtime.

## Mandatory Comparison Checks
For any new `seqcardenc` version:
1. Shared-instance status comparison versus reference version.
2. Lmax comparison on shared `FINISHED` cases.
3. Runtime summary with paired deltas.
4. Hard-case regression table.
5. SAT internal summary (if collected in that run).

## Dataset Policy (high level)
- Follow `docs/research/02_DATASET_POLICY.md`.
- Do not silently mix exploratory datasets into default 2016 benchmark summaries.
- If data anomalies are detected, record them in the decision log before claiming results.

## Reporting Requirements
- Use the template in `docs/research/05_REPORT_TEMPLATE.md`.
- Keep conclusions evidence-based and reproducible.
- Include exact commands and timeout profile used.

## Change Management
- Record protocol-affecting changes in `docs/research/06_DECISION_LOG.md`.
- Typical protocol-affecting changes:
  - timeout profile update
  - solver set update
  - dataset lane change
  - metric definition change

## Communication Style
- Keep responses concise, technical, and actionable.
- Separate facts, interpretation, and recommendations.
- If uncertain, state assumptions explicitly.
