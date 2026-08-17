# E-Star Variants Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three SAT encoding variants that strengthen precedence propagation with BFS-derived endpoint edges without switching to full transitive closure.

**Architecture:** Reuse the current `seqcardenc_ver2` and `seqcardenc_ver5` structures, and isolate the new graph logic in shared helpers under `common/schedule_utils.py`. The `e` variants only change which precedence edges are fed into the existing SAT clauses: `ver2e` and `ver5e` use source-to-sink edges, while `ver5e_1` uses all-ancestors-to-sink edges.

**Tech Stack:** Python, PySAT (`CNF`, `Solver`, `CardEnc`), existing SMSP runners.

---

### Task 1: Add shared BFS endpoint-edge helpers

**Files:**
- Modify: `common/schedule_utils.py`

- [ ] Add a reusable predecessor-builder for the precedence DAG.
- [ ] Add a BFS distance helper that works on either `successors` or `predecessors` adjacency maps.
- [ ] Add a helper for the source-to-sink strategy used by `seqcardenc_ver2e` and `seqcardenc_ver5e`.
- [ ] Add a helper for the all-ancestors-to-sink strategy used by `seqcardenc_ver5e_1`.
- [ ] Add a helper that merges extra endpoint edges back into a `successors` dictionary without duplicates.

### Task 2: Add `seqcardenc_ver2e`

**Files:**
- Create: `Encoding/functions_seqcardenc_ver2e.py`

- [ ] Copy `Encoding/functions_seqcardenc_ver2.py` as the base.
- [ ] Import the shared BFS endpoint-edge helpers.
- [ ] Compute source-to-sink extra edges and merge them into an `extended_successors` map.
- [ ] Keep `A` variables, `S -> A`, `CardEnc.atmost`, `L`, source-ready anchoring, and incremental `Lmax` unchanged.
- [ ] Replace the precedence loop to iterate over `extended_successors`.
- [ ] Print `|E|`, `|E_endpoint|`, and `|E + E_endpoint|` in verbose mode.

### Task 3: Add `seqcardenc_ver5e` and `seqcardenc_ver5e_1`

**Files:**
- Create: `Encoding/functions_seqcardenc_ver5e.py`
- Create: `Encoding/functions_seqcardenc_ver5e_1.py`

- [ ] Copy `Encoding/functions_seqcardenc_ver5.py` as the base for both files.
- [ ] In `ver5e`, use the source-to-sink BFS helper.
- [ ] In `ver5e_1`, use the all-ancestors-to-sink BFS helper.
- [ ] Keep pairwise `S/L` no-overlap, boundary-aware `L` helpers, source-ready anchoring, and incremental `Lmax` unchanged.
- [ ] Replace the precedence loop to iterate over the extended edge set.
- [ ] Print the endpoint strategy label and edge counts in verbose mode.

### Task 4: Register the new solvers

**Files:**
- Modify: `common/project_paths.py`
- Modify: `Test/runner_common.py`

- [ ] Add `seqcardenc_ver2e`, `seqcardenc_ver5e`, and `seqcardenc_ver5e_1` to `AVAILABLE_SOLVERS`.
- [ ] Add runner dispatch branches that import the new encoding modules like the existing SAT variants.

### Task 5: Verify objective consistency on a precedence-heavy small instance

**Files:**
- Runtime only

- [ ] Run one small `10-S` instance with `seqcardenc_ver2` and `seqcardenc_ver2e`.
- [ ] Run the same instance with `seqcardenc_ver5`, `seqcardenc_ver5e`, and `seqcardenc_ver5e_1`.
- [ ] Confirm all runs finish with consistent status and `Lmax` values.
- [ ] Check verbose output to make sure the new variants actually add endpoint edges on the chosen instance.
