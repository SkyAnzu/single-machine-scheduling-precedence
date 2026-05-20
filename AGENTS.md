# SMSP Repository Agent Protocol

## Purpose
This file defines how an agent should reason about this repository.

This workspace supports internal research on SAT encodings for single-machine scheduling with precedence constraints and time-window-style data.

The repository is not a paper-faithful implementation of a single source paper. It combines:
- Liu 2010 as the main objective reference for maximum lateness reasoning.
- Davari et al. 2016 as the practical source of the `.GSP`-style data fields and the default workspace lane under `2016/Ins/`.

## Repository Facts
- Default benchmark lane: `2016/Ins/`, driven by type-specific `Filenames/{size}-{type}.txt` when present and `Filenames/{size}.txt` otherwise.
- Exploratory generated lane: `Dataset_2010/`, currently a demo/pilot lane produced by `Test/generate_dataset_2010_pilot.py`.
- Main experimental runners live in `Test/`.
- Encoding variants live in `Encoding/` and represent incremental experiments; preserve their distinctions when documenting or comparing them.
- Graph and visual diagnostics live in `Graph_in4/`.

## Non-Negotiable Rules
1. Correctness first.
   - Never claim improvement if status consistency or objective consistency is broken.
2. Fair comparison required.
   - Same filelists, same preprocessing, same timeout profile, same machine context.
3. Objective semantics must be checked explicitly.
   - Do not assume every solver in the repository optimizes the same objective.
4. No performance claim from clause count alone.
   - Runtime and solver statistics must support conclusions.
5. Report regressions honestly.
   - If a new encoding is worse on hard cases, state it explicitly and provide evidence.

## Objective-Semantics Rule
At the current repository state, `seqcounter`, `seqcardenc`, `seqcardenc_ver2`, `seqcardenc_ver3`, `pbenc`, `basicsat`, and `gurobi` use true `Lmax = max(C_j - d_j)` behavior in the optimization workflow.

Therefore:
- Objective comparisons across these current solvers are allowed only after status consistency and output parsing are checked.
- Historical result workbooks may predate this alignment; do not mix old and new results without recording the code state.
- When in doubt, say exactly which solver set and objective behavior were used.

## Evaluation Lanes

### Lane A: SAT Family Benchmark (mandatory)
- Primary family: `seqcardenc`, `seqcardenc_ver2`, `seqcardenc_ver3`, and future `seqcardenc_*` variants.
- Required outputs:
  - status consistency
  - objective consistency inside an objective-aligned set
  - runtime summary
  - SAT internals when collected

### Lane B: Cross-Paradigm Baseline (optional)
- Use `gurobi` as an external baseline when helpful.
- Keep objective-semantics caveats explicit.

### Lane C: Generated-Data Diagnostics (optional)
- Use `Dataset_2010/` for demo/pilot exploration and stress testing.
- Do not silently merge this lane into default `2016` summaries.

## Filelist Authority
- `Filenames/{size}-{type}.txt`, when present, are the type-specific source of truth for the default 2016 batch lane.
- Otherwise, `Filenames/{size}.txt` is used as the fallback source of truth for the default 2016 batch lane.
- `Dataset_2010/Filenames/*.txt` are the source of truth for the generated demo lane.
- If a folder contains more `.GSP` files than the current filelist, runners still follow the filelist.

## Reporting Requirements
- Use `docs/research/05_REPORT_TEMPLATE.md`.
- Include exact commands, timeout profile, dataset lane, and objective semantics.
- Separate facts, interpretation, and recommendations.

## Change Management
- Record protocol-affecting changes in `docs/research/06_DECISION_LOG.md`.
- Typical protocol-affecting changes:
  - timeout profile update
  - solver set update
  - dataset lane change
  - objective definition / evaluation rule change
  - filelist policy change

## Documentation Policy
- When documentation and code disagree, trust the current runners, filelists, and parser behavior first.
- Update documentation to match the current workspace instead of assuming intended behavior.

## Communication Style
- Keep responses concise, technical, and actionable.
- State assumptions explicitly.
- Separate repository facts from research interpretation.
