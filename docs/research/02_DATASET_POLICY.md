# Dataset Policy

## Purpose
Define dataset lanes, default usage, and integrity rules for fair and reproducible experiments.

## Dataset Lanes

### Tier A (default): Current 2016 Workspace Dataset
- Source lane used by default benchmark runners:
  - `2016/Ins/wtrd_pred{n}/{S|L}/...`
- Primary instance list source:
  - `Filenames/{10,20,30,40,50}.txt`
- This is the default lane for SAT family benchmarking and regression tracking.

### Tier B (exploratory): 2010/2014-Inspired Datasets
- Used for exploratory robustness checks and future expansion.
- Not part of default benchmark summaries unless explicitly stated.
- Any Tier B run must clearly label:
  - generation policy
  - parameter grid
  - random seed policy
  - compatibility mapping to repository format
- Current Tier B pilot lane path:
  - `Dataset_2010/Ins/wtrd_pred{n}/{S|L}/...`
  - `Dataset_2010/Filenames/{n}.txt`

### Tier B Pilot Scope (current)
- Objective: small pilot for monitoring behavior before large-scale generation.
- Current pilot size: 24 instances total.
- Size split: `n in {20, 40, 50}` with 8 instances per size.
- Current type split: `S` only.
- Deadline policy (2016-style mapping):
  - `deadline_i ~ U[d_i, d_i + phi * P]`, `P = sum(p_i)`.
  - Default pilot uses `phi = 1.25`.

## Required Input Format
All benchmark datasets used by repository runners must conform to `.GSP` parser expectations in `common/dataset.py`:
- `n`
- `weight`
- `duration`
- `due date`
- `ready date`
- `deadline`
- `precedence relations`

If a source dataset does not provide all required fields (for example, no explicit deadlines), a documented mapping policy must be defined before use.

## Data Integrity Checklist (General)
Before any benchmark summary:
1. Parser validity:
   - all files parse successfully with repository parser
2. Value sanity:
   - non-negative processing times
   - sensible time-window fields for the intended formulation
3. Graph sanity:
   - precedence structure is valid for the runner workflow
4. Instance list consistency:
   - benchmark run uses a clearly defined and reproducible file list
5. Lane separation:
   - Tier A and Tier B results are not mixed silently in one summary

## Reproducibility Requirements for Generated Data
For any generated or transformed dataset, record:
- generator script path and commit id
- random seeds
- parameter grid
- output directory layout
- any post-processing or filtering rules

## Reporting Rules
- Every result table must identify the dataset lane (Tier A or Tier B).
- Default performance claims should be made on Tier A unless explicitly marked otherwise.
- If anomalies are detected, record them in `docs/research/06_DECISION_LOG.md` before final claims.
