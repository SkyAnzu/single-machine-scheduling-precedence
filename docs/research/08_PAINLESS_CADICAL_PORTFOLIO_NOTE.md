# Painless/CaDiCaL Portfolio SAT Architecture Note

## Scope
- Topic: design a minimal portfolio SAT prototype for this Python SMSP repository, inspired by Painless and possible CaDiCaL workers.
- Repository action: design only; no code was modified.
- Dataset/protocol assumption: any future benchmark must use the same lane, filelists, preprocessing, timeout profile, machine context, and true `Lmax` objective checks.

## External Facts
- Painless is a C++ framework for parallel/distributed SAT solving with separate components for solver interfaces, worker organization, clause sharing, containers, preprocessing, and utilities.
- Painless core directories include `src/working/`, `src/sharing/`, `src/solvers/`, `src/containers/`, and `src/preprocessors/`.
- Painless integrates multiple sequential solvers, including CaDiCaL, Kissat, Glucose, MiniSat, Lingeling, MapleCOMSPS, and YalSAT.
- Painless build requirements are heavier than this repo: C++20, Boost, OpenMPI, make/autoconf, POSIX-compatible environment.
- CaDiCaL can be built as a standalone binary and as `libcadical.a`; command-line usage is `cadical [ dimacs [ proof ] ]`.
- CaDiCaL supports useful portfolio knobs such as `--seed`, `--sat`, `--unsat`, `--plain`, preprocessing options, and statistics output.
- CaDiCaL supports incremental `p inccnf` files and assumptions/cubes, but using this cleanly from the current Python code would require a new DIMACS/incremental interface.

## Current Repository Facts
- Active SAT encodings are Python/PySAT functions under `Encoding/`.
- Current SAT calls use PySAT `Solver(name="g421"/"g4", bootstrap_with=cnf)` inside each encoding.
- Runners already use Python subprocess isolation per instance in `Test/run_batch_from_filelist.py`, `Test/run_compare_seqcardenc_v3_v4.py`, and `Test/run_single_instance.py`.
- Available solver names are registered in `common/project_paths.py`.
- There is no current `cadical`, `kissat`, external DIMACS worker, IPASIR binding, or clause-sharing implementation in the repository.
- Result parsing expects solution text with `Lmax = ...` and optional `STATS conflicts=... decisions=... propagations=... restarts=...` lines.

## Design Principle From Painless
- Separate the sequential solver engine from worker orchestration.
- Treat each worker as independently configurable.
- Keep result aggregation separate from solving.
- Delay learnt-clause sharing until a non-sharing portfolio has demonstrated value.
- Make worker logs and status semantics explicit; performance claims are invalid if objective/status consistency breaks.

## Recommended Phase 1 Prototype
- Build a portfolio at the Python runner level, not inside each encoding first.
- Run 2-4 independent workers for the same instance and same encoding.
- Each worker uses a different configuration, seed, or solver backend.
- First useful worker set should be conservative:
  - `seqcardenc_ver3` with current PySAT backend
  - `seqcardenc_ver4_3` with current PySAT backend
  - optional duplicate backend with different random seed only if the backend exposes a stable seed option
- Return the first proven `FINISHED` result only after recomputing true `Lmax` from the output schedule or using existing parser plus schedule validation.
- Keep all worker outputs so status/objective divergences can be audited.

## Process Model
- Parent process owns timeout, worker launch, worker termination, and result aggregation.
- Worker process runs one existing solver path through `Test/run_single_instance.py --single` or a new equivalent internal command.
- Worker writes to an isolated temporary solution file.
- Parent polls workers until one of these happens:
  - a worker returns `FINISHED` with parseable `Lmax`
  - all workers return terminal non-finished statuses
  - portfolio timeout expires
- Parent terminates still-running workers after selecting a result or hitting timeout.
- Parent writes one portfolio solution file using the selected worker's solution content plus portfolio metadata.

## Worker Lifecycle
- Create per-worker temp directory.
- Launch worker subprocess with explicit solver name, instance path, solution path, and timeout.
- Capture start time, exit code, parsed status, parsed `Lmax`, optional gap, optional SAT stats.
- On timeout, terminate gracefully, then kill after a grace period.
- Preserve worker logs/solution files under a debug directory when a divergence occurs.

## Result Aggregation Semantics
- `FINISHED` beats `TIMEOUT`, `ERROR`, and `FILE_NOT_FOUND` only if objective parsing succeeds.
- If multiple workers finish, choose the best true `Lmax`, not necessarily the first result, when the parent waits until all active workers finish within the same timeout.
- For a race-style prototype, first-finished mode is acceptable only as a runtime experiment and must be reported as such.
- If worker statuses differ unexpectedly on the same instance, mark the portfolio result as diagnostic until root cause is checked.
- Do not mix `TIME_LIMIT_FEASIBLE` semantics from MIP/Gurobi with SAT `FINISHED` semantics without an explicit status table.

## Incumbent UB Propagation
- Phase 1 should not share learnt clauses.
- Phase 1 can optionally share incumbent objective values through parent-managed cancellation/restart, but this is not required for the first prototype.
- Simple safe option: no UB sharing; workers independently optimize and parent takes the best finished result.
- Next option: if a worker finds a better `Lmax`, parent records it and may terminate workers whose configurations are only meant to race for any solution.
- More advanced option: restart workers with a tighter initial UB, but this needs encoding API changes to accept an external incumbent bound.
- Clause sharing should be postponed because current workers are PySAT solver objects inside separate Python processes and do not expose learnt clauses through the existing interface.

## CaDiCaL Integration Options

| Option | Description | Pros | Cons | Recommendation |
|---|---|---|---|---|
| PySAT CaDiCaL backend | Use PySAT solver name for CaDiCaL if installed and compatible. | Minimal architecture change; keeps current CNF objects. | Need environment/backend verification; seed/config access may be limited. | Best first CaDiCaL check if available. |
| External `cadical` subprocess | Export CNF/DIMACS and run `cadical` binary. | Clear process isolation; easy seeds/configs; close to portfolio worker model. | Need DIMACS export, model parsing, and incremental optimization redesign. | Good Phase 2 path after portfolio runner exists. |
| Native C++ extension | Bind directly to `libcadical.a`. | Strong control; possible assumptions/incremental solve. | High build/maintenance cost, especially on Windows. | Not first. |
| `ctypes`/`cffi` binding | Call a C ABI wrapper. | More direct than subprocess. | Requires stable wrapper and memory/error handling. | Not first. |
| RustSAT backend | Use RustSAT/CaDiCaL/IPASIR later. | Could unify solver abstraction with future Rust tools. | New language/toolchain; separate research topic. | Defer to Topic 3. |

## Windows vs Linux/WSL Maintenance
- Painless itself is not a good immediate dependency for this Windows-oriented Python repo because it assumes a POSIX-like build stack and OpenMPI.
- CaDiCaL binary integration is more realistic than full Painless integration.
- If native CaDiCaL builds are painful on Windows, prefer WSL or prebuilt binaries for experiments.
- Keep Painless as an architecture reference, not as a vendored dependency, unless the project explicitly moves to a C++/Linux solver infrastructure.

## Proposed Repository Files For Future Implementation
- Implemented `Test/portfolio_common.py`: shared worker launch, timeout, parsing, selected-worker aggregation, and portfolio solution writing.
- Implemented `Test/run_portfolio_instance.py`: one-instance portfolio runner that launches workers and aggregates results.
- Implemented `Test/run_portfolio_batch_from_filelist.py`: batch runner using authoritative filelists and the same output conventions as `run_batch_from_filelist.py`.
- Did not add portfolio solver registration in `common/project_paths.py`; the portfolio remains an explicit experimental runner.
- Avoided editing encoding files in Phase 1 because no encoding needs initial UB or backend selection yet.
- Added portfolio output conventions under `2016/solutions_portfolio*` and workbook/CSV fields for `selected_worker`, `worker_count`, `worker_statuses`, and `worker_Lmax_values`.
- Updated `Test/runner_common.py` so single-instance paths can run even when `pandas` is not installed; Excel read/write paths still require `pandas`.

## Phase Roadmap

### Phase 1: Race Without Clause Sharing
- Implemented a one-instance portfolio runner around existing solvers.
- Worker set: `seqcardenc_ver3`, `seqcardenc_ver4_3`, optionally `seqcardenc_ver4_1` or `seqcardenc_ver4_2` for architecture comparison.
- Use the same `.GSP` input and same `window_tightening` path via existing `runner_common.py`.
- Record per-worker status, `Lmax`, `time_s`, and SAT stats if available.
- Verify same objective semantics before runtime claims.

### Phase 2: External CaDiCaL Experiment
- Add CNF/DIMACS export for exactly one encoding first, likely `seqcardenc_ver4_3`.
- Run external `cadical` workers with different `--seed`, `--sat`, `--unsat`, or `--plain` settings.
- Parse SAT/UNSAT/model output and reconstruct schedule from positive variables.
- Compare against the PySAT path on identical instances.
- Only then decide whether assumptions/incremental `p inccnf` are worth the complexity.

### Phase 3: Controlled UB Sharing
- Add an optional initial incumbent parameter to one encoding's incremental optimizer.
- Parent broadcasts best known `UB` to future worker launches or restarts.
- Do not claim benefit unless status and objective consistency remain exact.

### Phase 4: Clause Sharing Research
- Investigate learnt-clause exchange only after subprocess portfolio has evidence of value.
- This likely requires native bindings or a dedicated C++/Rust sidecar because current PySAT subprocess workers cannot exchange learnt clauses through the repository interface.

## Benchmark Checklist
- Start with a smoke subset before full lane: one type such as `S`, short timeout such as 60 seconds.
- Use the same filelist authority as all default runners.
- Use same timeout per instance and report whether portfolio timeout is total wall time or per-worker timeout.
- Report CPU/core count because portfolio wall time consumes multiple cores.
- Compare status first, objective second, runtime third.
- Runtime comparison should include both wall-clock time and worker-core cost when possible.
- Include hard-case divergences and worker disagreement cases.
- Do not compare against historical workbooks unless the code state and objective semantics are recorded.

## Implemented Commands
- Single-instance smoke: `python Test/run_portfolio_instance.py 2016/Ins/wtrd_pred10/S/10_00_005_100_00_1.GSP --output 2016/solutions_portfolio_smoke/10-S/10_00_005_100_00_1.GSP.txt --timeout 30`
- Batch smoke by type: `python Test/run_portfolio_batch_from_filelist.py --types S --timeout 60`
- Custom worker set: `python Test/run_portfolio_instance.py <instance.GSP> --output <solution.txt> --workers seqcardenc_ver3 seqcardenc_ver4_3 --timeout 300`

## Current Verification Note
- The current Python environment must install `requirements.txt` before SAT workers can solve instances.
- Without `python-sat`, worker subprocesses fail with `ModuleNotFoundError: No module named 'pysat'`.
- Without `pandas`/`openpyxl`, `run_portfolio_batch_from_filelist.py` writes a combined CSV fallback next to the requested workbook path.

## Sources
- Painless GitHub README: `https://github.com/lip6/painless`
- CaDiCaL GitHub README: `https://github.com/arminbiere/cadical`
- CaDiCaL man page summaries for options such as `--seed`, `--sat`, `--unsat`, `--plain`, and incremental `p inccnf` support.
- D-Painless TACAS 2025 summary: distributed portfolio SAT solving, worker/group organization, and clause-sharing strategy separation.

## Recommendation
- Do not try to integrate full Painless first.
- Build a small Python portfolio runner around existing repository solvers first.
- Treat CaDiCaL as a Phase 2 external worker or PySAT backend experiment.
- Treat clause sharing as a later research track, not a prerequisite for useful portfolio experiments.
