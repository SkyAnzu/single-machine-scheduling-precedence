# Dataset Policy

## Purpose
Define dataset lanes, input authority, and reproducibility rules for this repository.

## Dataset Lanes

### Tier A: Default 2016 Workspace Lane
- Root path: `2016/Ins/`
- Folder layout: `2016/Ins/wtrd_pred{10,20,30,40,50}/{S|L}/`
- Authoritative instance lists: `Filenames/{size}-{type}.txt` when present, otherwise `Filenames/{size}.txt`
- This is the default lane for benchmark summaries and regression tracking.

### Tier B: Generated 2010 Demo Lane
- Root path: `Dataset_2010/Ins/`
- Authoritative instance lists: `Dataset_2010/Filenames/{20,40,50}.txt`
- Current usage: demo / pilot generation, exploratory diagnostics, stress checks
- Current generator: `Test/generate_dataset_2010_pilot.py`
- This lane is not the default benchmark lane.

## Why Two Lanes Exist
- The 2016 lane gives the repository its working `.GSP` structure and the currently used benchmark inputs.
- The 2010 demo lane exists because the research question also references Liu 2010 and needs a controllable generated lane for exploration.
- The two lanes must remain distinguishable in every report.

## Filelist Authority Rule
Batch execution is defined by filelists, not by folder enumeration.

This means:
- main 2016 runs first look for `Filenames/{size}-{type}.txt`, then fall back to `Filenames/{size}.txt`
- for example, `Filenames/10-L.txt` defines the current `10-L` batch list, while `10-S` falls back to `Filenames/10.txt`
- generated demo runs follow `Dataset_2010/Filenames/*.txt`
- extra `.GSP` files present in a folder are not automatically part of the benchmark
- if folder contents and filelists differ, treat the filelists as authoritative until a documented change says otherwise

## Required Input Format
All runner-compatible datasets must match the `.GSP` expectations used in `common/dataset.py`:
- `n`
- `weight`
- `duration`
- `due date`
- `ready date`
- `deadline`
- `precedence relations`

## Weight-Field Note
The `weight` field is retained for format compatibility with the 2016-style input structure.
Current `Lmax`-oriented workflows do not use the weight values in the objective.

## Current Generated-Lane Note
`Dataset_2010/` is currently a demo/pilot lane. The workspace may contain generated files that are not all listed in the current filelists. Reports and runners must still follow the filelists unless the generation policy and benchmark scope are re-frozen.

## Data Integrity Checklist
Before reporting results:
1. Parser validity:
   - all used files parse with the repository parser
2. Filelist integrity:
   - the exact filelists used are known and archived
3. Value sanity:
   - processing times are non-negative
   - ready dates, due dates and deadlines are numerically sensible for the intended experiment
4. Graph sanity:
   - precedence structure is acyclic for the runner workflow
5. Lane separation:
   - Tier A and Tier B results are not silently merged
6. Objective annotation:
   - the report states whether the compared solvers share the same objective semantics

## Reproducibility Requirements for Generated Data
For any generated lane or transformed dataset, record:
- generator script path
- commit hash or workspace snapshot
- random seed
- parameter grid
- output root
- authoritative filelists
- any filtering or pruning applied after generation

## Reporting Rules
- Every result table must state the dataset lane.
- Default repository claims should be based on Tier A unless explicitly stated otherwise.
- Demo / pilot results from `Dataset_2010/` must be labeled as exploratory.
- Any filelist / folder mismatch that affects interpretation should be recorded in `docs/research/06_DECISION_LOG.md`.
