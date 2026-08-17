# Decision Log

Use this file to record protocol-affecting decisions, documentation realignments, and data-lane anomalies that change how results should be interpreted.

## Entry Template
- Date:
- Decision ID:
- Context:
- Decision:
- Rationale:
- Evidence:
- Impacted files/process:
- Risk:
- Follow-up actions:

---

## 2026-04-23 | D-001
- Context:
  - Internal research protocol standardization was missing as explicit markdown assets.
- Decision:
  - Introduce repository-level protocol documents under `docs/research/` and repository `AGENTS.md`.
- Rationale:
  - Ensure reproducible, fair, and evidence-based comparisons across SAT encoding versions.
- Evidence:
  - Existing runners and result files are operational, but no formal protocol docs existed.
- Impacted files/process:
  - Added: `AGENTS.md`
  - Added: `docs/research/01_PROTOCOL_SCOPE.md`
  - Added: `docs/research/02_DATASET_POLICY.md`
  - Added: `docs/research/03_EXPERIMENT_RUNBOOK.md`
  - Added: `docs/research/04_METRICS_GUIDE.md`
  - Added: `docs/research/05_REPORT_TEMPLATE.md`
  - Added: `docs/research/06_DECISION_LOG.md`
- Risk:
  - Low. Documentation-only change.
- Follow-up actions:
  - Apply report template in the next SAT family comparison cycle.

---

## 2026-04-24 | D-002
- Context:
  - Tier B (2010-inspired) exploratory lane needed a parser-compatible pilot dataset for early monitoring.
  - Repository `.GSP` format requires `deadline`, while Liu 2010 instance design does not define explicit deadlines.
- Decision:
  - Add a small Tier B pilot lane under `Dataset_2010/` with 24 instances (`n in {20,40,50}`, 8 per size).
  - Use 2016-style deadline mapping for compatibility:
    - `deadline_i ~ U[d_i, d_i + phi * P]`, with `P = sum(p_i)` and pilot `phi = 1.25`.
  - Keep default 2016 lane untouched; add separate runner for Tier B pilot.
- Rationale:
  - Enables quick feedback on behavior before large-scale generation.
  - Keeps lane separation explicit and preserves fairness in Tier A regression tracking.
- Evidence:
  - Added generator: `Test/generate_dataset_2010_pilot.py`.
  - Added lane runner: `Test/run_batch_dataset_2010.py`.
  - Generated pilot files and filelists under `Dataset_2010/`.
  - Smoke run completed on `seqcardenc_ver2` with timeout profile 60s (pilot diagnostic profile).
- Impacted files/process:
  - Added: `Test/generate_dataset_2010_pilot.py`
  - Added: `Test/run_batch_dataset_2010.py`
  - Added output lane content under `Dataset_2010/`
  - Updated: `docs/research/02_DATASET_POLICY.md`
  - Updated: `docs/research/03_EXPERIMENT_RUNBOOK.md`
  - Updated: `docs/research/06_DECISION_LOG.md`
- Risk:
  - Medium. Some generated instances can be UNSAT after precedence + time-window interactions.
  - Tier B only; does not affect Tier A default claims.
- Follow-up actions:
  - Track UNSAT/TIMEOUT ratio in pilot.
  - Adjust `phi` or precedence parameter grid if pilot is too tight or too easy.
  - Expand to larger Tier B set only after pilot review.

---

## 2026-04-24 | D-003
- Context:
  - User requested timeout alignment with Liu 2010 default (1 minute).
- Decision:
  - Set default timeout of `Test/run_batch_dataset_2010.py` to 60 seconds per instance.
  - Keep CLI override via `--timeout` for controlled deviations.
- Rationale:
  - Preserve consistency with 2010 experimental setting while retaining flexibility for diagnostics.
- Evidence:
  - Updated `TIMEOUT` constant in `Test/run_batch_dataset_2010.py` from 300 to 60.
  - Updated runbook/README notes for Dataset_2010 timeout behavior.
- Impacted files/process:
  - Updated: `Test/run_batch_dataset_2010.py`
  - Updated: `docs/research/03_EXPERIMENT_RUNBOOK.md`
  - Updated: `docs/research/06_DECISION_LOG.md`
  - Updated: `README.md`
- Risk:
  - Low. Only changes default in exploratory lane runner.
- Follow-up actions:
  - If comparing with Tier A, always report timeout profile explicitly.

---

## 2026-05-19 | D-004
- Context:
  - Markdown documentation had drifted from the current workspace state.
  - The repository combines a 2016-format data lane with a Liu-2010-inspired `Lmax` research objective.
  - `Dataset_2010/` is currently used as a generated demo/pilot lane rather than a default benchmark lane.
  - The current `Dataset_2010/Filenames/50.txt` does not enumerate all generated `.GSP` files presently stored under `Dataset_2010/Ins/wtrd_pred50/S/`.
  - Some documentation referenced files that are not in the repository anymore.
- Decision:
  - Realign markdown documentation with the current runners, parser behavior, filelists, and research context.
  - Treat filelists as authoritative for batch execution.
  - Document `Dataset_2010/` as a demo/pilot lane.
  - Document the current objective-semantics mismatch across solvers instead of assuming a uniform `Lmax` implementation.
- Rationale:
  - Prevent inaccurate benchmark claims.
  - Preserve reproducibility without changing code or datasets.
  - Make the repo documentation reflect the actual workspace rather than historical assumptions.
- Evidence:
  - `common/project_paths.py` sets the default lane to `2016/Ins/`.
  - `Test/generate_dataset_2010_pilot.py` is the current generated-data entry point.
  - `Dataset_2010/Filenames/50.txt` lists fewer instances than are currently present in `Dataset_2010/Ins/wtrd_pred50/S/`.
  - `README.md` referenced `AIREADME.md` and `Test/rewrite_existing_solutions.py`, both absent from the repo.
  - Objective implementations differ across current solver files.
- Impacted files/process:
  - Updated: `README.md`
  - Updated: `AGENTS.md`
  - Updated: `CLAUDE.md`
  - Updated: `docs/research/01_PROTOCOL_SCOPE.md`
  - Updated: `docs/research/02_DATASET_POLICY.md`
  - Updated: `docs/research/03_EXPERIMENT_RUNBOOK.md`
  - Updated: `docs/research/04_METRICS_GUIDE.md`
  - Updated: `docs/research/05_REPORT_TEMPLATE.md`
  - Updated: `docs/research/06_DECISION_LOG.md`
- Risk:
  - Low. Documentation-only change.
- Follow-up actions:
   - If objective semantics are later unified in code, add a new decision-log entry and update the docs again.
   - If the generated `Dataset_2010` lane is promoted beyond demo use, freeze the authoritative filelists and record the generation policy.

---

## 2026-05-20 | D-005
- Context:
  - SAT solvers still had clamped lateness logic in incremental optimization, while the research protocol targets Liu-style true `Lmax`.
  - `10-L` used fewer physical files than `10-S`, so a size-only filelist caused missing inputs on that lane.
  - Gurobi time-limit incumbents with nonzero MIP gap were previously indistinguishable from finished optimal runs in workbook status.
- Decision:
  - Align `seqcounter`, `seqcardenc`, `seqcardenc_ver2`, `seqcardenc_ver3`, and `pbenc` to true `Lmax = max(C_j - d_j)`.
  - Keep `basicsat` on true `Lmax` and remove its positive-only incremental stop condition.
  - Add type-specific filelist lookup for the default 2016 lane, with `Filenames/{size}-{type}.txt` preferred over `Filenames/{size}.txt`.
  - Record Gurobi time-limit incumbents with nonzero MIP gap as `TIME_LIMIT_FEASIBLE` and workbook `Lmax = -`.
  - Rename the `seqcardenc_ver2` / `seqcardenc_ver3` source-job clause terminology from symmetry breaking to source-ready anchoring.
- Rationale:
  - Cross-solver objective comparisons require aligned objective semantics.
  - Filelist authority must reflect lane-specific available files without deleting valid `S` instances.
  - A nonzero-gap Gurobi incumbent is useful evidence but not an optimal objective value.
- Evidence:
  - Updated SAT optimization loops now search for strict improvements to true `Lmax`, including negative values.
  - Added `Filenames/10-L.txt` for the current 10-job `L` lane.
  - Runner parser recognizes `TIME_LIMIT_FEASIBLE` separately from `FINISHED` and `TIMEOUT`.
- Impacted files/process:
  - Updated: `Encoding/functions_seqcounter.py`
  - Updated: `Encoding/functions_seqcardenc.py`
  - Updated: `Encoding/functions_seqcardenc_ver2.py`
  - Updated: `Encoding/functions_seqcardenc_ver3.py`
  - Updated: `Encoding/functions_pbenc.py`
  - Updated: `Encoding/functions_basicsat.py`
  - Updated: `Encoding/functions_gurobi.py`
  - Updated: `Test/runner_common.py`
  - Updated: `Test/run_batch_from_filelist.py`
  - Updated: `Graph_in4/visualize_batch_from_filelist.py`
  - Added: `Filenames/10-L.txt`
  - Updated: repository protocol docs
- Risk:
  - Medium. Historical result workbooks may no longer be objective-comparable with new runs.
  - SAT runtime may change because optimization no longer stops at `Lmax <= 0`.
- Follow-up actions:
  - Re-run objective comparisons under the aligned code state before making solver-performance claims.
  - Label or archive old workbooks if they are kept for historical diagnostics.

---

## 2026-08-17 | D-006
- Context:
  - User requested three additional cross-paradigm baselines: OR-Tools CP-SAT, IBM CPLEX CP Optimizer, and IBM CPLEX MP/MIP.
  - The local machine does not currently have an IBM CPLEX academic/commercial license configured.
- Decision:
  - Add solver entries `cpsat`, `cplex_cp`, and `cplex_mp` to the default 2016 runner infrastructure.
  - Treat these as direct optimization solvers, not SAT encoding variants.
  - Keep true `Lmax = max(C_j - d_j)` semantics for all three new modules.
  - Return explicit missing-runtime/status values for CPLEX modules when DOcplex/CPLEX is unavailable, instead of silently failing batch runs.
- Rationale:
  - CP-SAT is license-free and can be run immediately once `ortools` is installed.
  - CPLEX CP/MP code can be maintained in the repository now, while benchmark claims are deferred until a valid CPLEX runtime/license is available.
  - Cross-paradigm comparisons require the same filelists, preprocessing, timeout profile, and objective semantics.
- Evidence:
  - Added direct optimization solver modules under `Encoding/`.
  - Registered the new solvers in `common/project_paths.py` and `Test/runner_common.py`.
  - Added Python dependencies for OR-Tools and DOcplex/CPLEX community runtime in `requirements.txt`.
- Impacted files/process:
  - Added: `Encoding/functions_cpsat.py`
  - Added: `Encoding/functions_cplex_cp.py`
  - Added: `Encoding/functions_cplex_mp.py`
  - Updated: `common/project_paths.py`
  - Updated: `Test/runner_common.py`
  - Updated: `requirements.txt`
  - Updated: `docs/research/06_DECISION_LOG.md`
- Risk:
  - Medium. CPLEX Community Edition is size-limited and may not solve benchmark instances beyond the free limits.
  - Medium. CPLEX CP/MP result workbooks should not be used for performance claims until runtime/license availability is verified and status consistency is checked.
- Follow-up actions:
  - Install dependencies and run smoke tests on one small 2016 instance.
  - Record CPLEX license/runtime details in reports before including CPLEX CP/MP results.
  - Compare `cpsat` first against `seqcardenc_ver5` and `gurobi` under the same 300s default timeout.

---

## 2026-08-18 | D-007
- Context:
  - Direct optimization solvers (`cpsat`, `cplex_cp`, `cplex_mp`, and existing `gurobi`) may hit the time limit with a feasible incumbent whose global optimality is unproven (MIP gap > 0 or CP search stopped on a feasible solution).
  - The runner previously recorded these cases as a distinct `TIME_LIMIT_FEASIBLE` status with `Lmax = "-"`, while historical workbooks (`2016/results.xlsx`) record timeout rows with the best found value.
- Decision:
  - Normalize reporting so that a time-limit-feasible result is recorded with status `TIMEOUT` while still logging the best found `Lmax` value (and MIP gap when available).
  - The solution file itself keeps its structure: first line `TIME_LIMIT_FEASIBLE`, followed by `Lmax = ...`, optional `MIP Gap`, optional `Solve Time`, and the `Schedule:` block.
  - `Test/rewrite_existing_solutions.py` treats `TIME_LIMIT_FEASIBLE` as a terminal status so rewrites never strip the prefix.
- Rationale:
  - A time-limit incumbent is useful evidence (valid upper bound) but not a proven optimum; reporting it as `Lmax = "-"` under a separate status conflates parsing behavior with evidence value.
  - Aligns with the existing workbook convention that timeout rows still carry the best found value.
- Evidence:
  - `Test/runner_common.py`: `run_single_instance` returns `(lmax, "TIMEOUT", gap)`; `parse_solution_file` reads `Lmax` from `TIME_LIMIT_FEASIBLE` files and returns status `TIMEOUT`.
  - `Test/rewrite_existing_solutions.py`: `TERMINAL_STATUSES` extended with `TIME_LIMIT_FEASIBLE`.
- Impacted files/process:
  - Updated: `Test/runner_common.py`
  - Updated: `Test/rewrite_existing_solutions.py`
  - Updated: `docs/research/06_DECISION_LOG.md`
- Risk:
  - Low. Status string in new workbooks becomes `TIMEOUT` for time-limit feasible runs; consumers must not infer "no solution" from status alone when `Lmax` is present.
- Follow-up actions:
  - Verify on `2016/Ins/wtrd_pred50/S/50_05_005_100_75_1.GSP` that all four solvers report consistent `Lmax` where a proven optimum exists, and that a time-limited incumbent reports `TIMEOUT` with its `Lmax` value.
