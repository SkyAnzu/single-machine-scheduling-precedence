# Dynamic `due + UB` Deadline Tightening Note

## Scope
- Topic: evaluate dynamic per-job deadline tightening `deadline'_j = min(deadline_j, due_j + UB)` for true `Lmax = max(C_j - d_j)` optimization.
- Dataset lane assumption: default `2016/Ins/` lane unless a generated-data diagnostic is explicitly requested.
- Objective assumption: active solver code uses true, unclamped `Lmax`; negative `Lmax` values are valid.
- Code was inspected, not modified.

## Current Encoding Semantics
- `Encoding/functions_seqcounter.py`: start variables `S`, activity variables `A`, cumulative start-order variables `L`; incremental optimization adds `L[(j, due_j + UB - p_j - 1)]` when inside the valid start range.
- `Encoding/functions_seqcardenc.py`: same objective-bound semantics as `seqcounter`; capacity uses PySAT `CardEnc.atmost`.
- `Encoding/functions_seqcardenc_ver2.py`: same objective-bound semantics as `seqcardenc`; adds source-ready anchor clause.
- `Encoding/functions_seqcardenc_ver3.py`: start-order `L` is still the objective-bound mechanism; activity is encoded from `L` instead of direct `S -> A` clauses.
- `Encoding/functions_seqcardenc_ver4_1.py`: pure start-order `L`; incremental optimization adds `L[(job, due_j + UB - p_j - 1)]`.
- `Encoding/functions_seqcardenc_ver4_2.py`: start-order `L` plus reverse-order `G`; incremental optimization still uses only `L[(job, due_j + UB - p_j - 1)]`.
- `Encoding/functions_seqcardenc_ver4_3.py`: completion-order `C`; incremental optimization adds `C[(job, due_j + UB - 1)]`.
- `Encoding/functions_pbenc.py`: same objective-bound semantics as `seqcounter`; capacity uses `PBEnc.atmost`.
- `Encoding/functions_basicsat.py`: no `L`; incremental optimization forbids each `S[(i,t)]` where `t + p_i - due_i >= UB`.

## Formula Equivalence

| Family | Current bound clause | Proposed `due + UB` view | Equivalent? | Notes |
|---|---|---|---|---|
| `seqcounter`, `seqcardenc`, `seqcardenc_ver2`, `seqcardenc_ver3`, `pbenc` | `L[j, due_j + UB - p_j - 1]` | require `start_j + p_j <= due_j + UB - 1` | yes | Current loop searches for a strictly better solution than current `UB`, so it enforces `Lmax < UB`, not `Lmax <= UB`. |
| `seqcardenc_ver4_1`, `seqcardenc_ver4_2` | `L[j, due_j + UB - p_j - 1]` | require `start_j + p_j <= due_j + UB - 1` | yes | Same strict-improvement semantics, but encoded directly over start-order variables. |
| `seqcardenc_ver4_3` | `C[j, due_j + UB - 1]` | require `completion_j <= due_j + UB - 1` | yes | This is already the direct completion-deadline form. |
| `basicsat` | forbid starts with `t + p_j - due_j >= UB` | allow only `t <= due_j + UB - p_j - 1` | yes | Equivalent by enumerating start literals instead of using an order literal. |

## Off-By-One Analysis
- True lateness for job `j` is `C_j - d_j`, with `C_j = start_j + p_j` under half-open processing interval `[start, start + p)`.
- The incremental loop starts from a feasible incumbent `UB` and asks for a strictly better schedule.
- Strict improvement means `C_j - d_j < UB` for every job.
- With integer time, `C_j <= d_j + UB - 1`.
- For start-order encodings, this becomes `start_j <= d_j + UB - p_j - 1`.
- Therefore the existing `latest_start = due_dates[j] + UB - durations[j] - 1` is the strict version of `deadline'_j = due_j + UB - 1`.
- A non-strict `deadline'_j = due_j + UB` would encode `Lmax <= UB`; by itself it would not force improvement and could repeat the same objective value.

## UB Sign Cases
- `UB > 0`: bound can still permit lateness; e.g. `UB = 3` requires `C_j <= d_j + 2` to find `Lmax <= 2` or better.
- `UB = 0`: strict improvement requires all jobs finish before their due date: `C_j <= d_j - 1`; this correctly searches for negative `Lmax`.
- `UB < 0`: strict improvement is still meaningful; for `UB = -2`, each job must satisfy `C_j <= d_j - 3` to find `Lmax <= -3` or better.
- If the computed bound is before a job's earliest possible start/completion, adding an empty clause is correct: no strictly better schedule can satisfy that job's lateness bound.
- Negative `UB` must not be clamped to zero anywhere in this path; `compute_max_lateness(..., clamp_zero=False)` is the required behavior.

## Rebuild vs Incremental Clauses
- Current SAT-family implementations add permanent clauses to one solver instance across iterations.
- This is sound because every new `UB` is lower or equal to the previous incumbent and the strict-improvement constraints are monotonically tighter.
- Rebuilding CNF each iteration is not required for correctness and would add overhead.
- Assumption literals could support cleaner per-iteration experiments, but they are not the smallest first implementation path.
- The smallest safe path is to keep permanent clauses and only adjust how the bound literal is computed if a new variant is introduced.

## Propagation Assessment
- If implemented as `deadline'_j = due_j + UB - 1` and then converted to the same `L` or `C` unit clauses, propagation strength is identical to the current objective-bound clauses.
- For start-order families, rebuilding `valid_starts` with tightened deadlines each iteration would shrink variable domains only if the CNF is rebuilt; that is a different, more expensive design.
- For `ver4_3`, the completion-order variable already matches the true objective expression and is the cleanest semantic baseline.
- A `due + UB` rewrite alone should be treated as a clarity/refactoring experiment, not a guaranteed performance improvement.

## Recommended Prototype
- First prototype candidate: `seqcardenc_ver4_3`, because its `C[j,t]` variables represent the exact completion bound `C_j <= d_j + UB - 1`.
- Alternative prototype candidate: `seqcardenc_ver3`, because it is the current comparison baseline in `Test/run_compare_seqcardenc_v3_v4.py`.
- Do not change all families at once; objective regressions would be harder to isolate.
- If implementing, create a new variant rather than mutating a benchmarked solver name, for example `Encoding/functions_seqcardenc_ver4_4.py` or a clearly named experimental branch.

## Minimal Implementation Plan
- Add a small helper in exactly one candidate file first, not a shared helper across all encodings.
- For `ver4_3`, compute `latest_completion = due_dates[job] + UB - 1` and add `C[(job, latest_completion)]` when it is inside `valid_completions[job]`.
- For start-order variants, compute `tight_deadline = due_dates[job] + UB - 1`, then `latest_start = tight_deadline - durations[job]`.
- Preserve the current empty-clause behavior when the bound is before the earliest valid start/completion.
- Preserve true `Lmax` recomputation from extracted schedules after every SAT result.

## Benchmark Checklist
- Use the default filelist authority: `Filenames/{size}-{type}.txt` when present, otherwise `Filenames/{size}.txt`.
- Use the same preprocessing path: `window_tightening` in `Test/runner_common.py` before calling `solve_SAT`.
- Use the same timeout profile across baseline and candidate.
- Compare against at least `seqcardenc_ver3` and `seqcardenc_ver4_3` before making any claim.
- Required status checks: same `FINISHED`, `TIMEOUT`, `UNSAT`, `ERROR`, or `TIME_LIMIT_FEASIBLE` behavior on shared instances.
- Required objective checks: same true `Lmax` on shared `FINISHED` instances, allowing negative values.
- Required runtime checks: `time_s`, solved/timeout counts, paired runtime deltas, and hard-case divergences.
- Supporting checks: SAT stats from `STATS conflicts=... decisions=... propagations=... restarts=...` when verbose collection is enabled.
- Do not claim improvement from clause count alone.

## Concrete Verification Commands
- Smoke one type and short timeout: `python Test/run_compare_seqcardenc_v3_v4.py --types S --timeout 60`
- Default lane batch for selected aligned solvers: `python Test/run_batch_from_filelist.py --types S --solvers seqcardenc_ver3 seqcardenc_ver4_3`
- If a new variant is added, first extend `Test/runner_common.py` and a comparison runner intentionally; do not mix its results with historical workbooks without recording the code state.

## Recommendation
- Treat `due + UB` as a semantic clarification of the current strict objective-bound logic, not as a new optimization by itself.
- Use `due_j + UB - 1`, not `due_j + UB`, when the loop is searching for a strictly better incumbent.
- If the research goal is performance, prototype on `ver4_3` or `ver3` and measure status/objective consistency before runtime.
