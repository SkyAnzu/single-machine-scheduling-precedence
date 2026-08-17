# Seqcardenc Ver5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a new SAT encoding variant `seqcardenc_ver5` that removes `A` variables and machine-capacity cardinality constraints, replacing them with pairwise `S/L` no-overlap clauses.

**Architecture:** Copy `seqcardenc_ver2` as the base because it already has `S`, `L`, source-ready anchoring, precedence on `S/L`, and `L`-based incremental optimization. Remove `A`-variable generation and `CardEnc` capacity encoding, then add pairwise no-overlap clauses over unordered job pairs `i < j` using simplified `L` literals with explicit out-of-domain handling.

**Tech Stack:** Python, PySAT (`CNF`, `Solver`), existing SMSP runner utilities.

---

### Task 1: Add the new encoding file

**Files:**
- Create: `Encoding/functions_seqcardenc_ver5.py`

- [ ] Copy the structure of `Encoding/functions_seqcardenc_ver2.py`.
- [ ] Keep `read_dataset`, `window_tightening`, `compute_UB_Lmax`, `incremental_SAT_Lmax`, precedence clauses, and source-ready anchoring.
- [ ] Remove `A` creation, `S -> A` clauses, and `CardEnc.atmost` capacity constraints.
- [ ] Add helper logic for `L[j,u]` outside the feasible start domain, returning `True`, `False`, or an integer literal.
- [ ] Add pairwise no-overlap clauses for unordered job pairs `i < j` and every `t` in `valid_starts[i]`:

```text
not S[i,t] OR L[j, t-p_j] OR not L[j, t+p_i-1]
```

- [ ] Simplify each candidate clause before appending:
  - `True` means drop the whole clause.
  - `False` means omit that literal.
  - integer means append the SAT literal.

### Task 2: Register the new solver

**Files:**
- Modify: `common/project_paths.py`
- Modify: `Test/runner_common.py`

- [ ] Add `seqcardenc_ver5` to `AVAILABLE_SOLVERS`.
- [ ] Add a new dispatch branch in `run_single_instance()` so the runner imports `functions_seqcardenc_ver5` like the existing SAT variants.

### Task 3: Verify the implementation on a small instance

**Files:**
- Runtime only

- [ ] Run `seqcardenc_ver2` on one small `2016/Ins/wtrd_pred10/S/*.GSP` instance.
- [ ] Run `seqcardenc_ver5` on the same instance.
- [ ] Confirm both produce a finished run with a parseable `Lmax`.
- [ ] Compare the resulting `Lmax` values to make sure the new encoding stays objective-consistent on the spot check.

### Task 4: Final review

**Files:**
- Review diffs only

- [ ] Check the new file for variable-ID handling consistency and make sure boolean simplification does not confuse `True`/`False` with integer SAT literals.
- [ ] Summarize remaining risks: clause growth for dense pairwise constraints and the fact that broader benchmarking is still needed.
