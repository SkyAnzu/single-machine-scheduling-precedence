# Experiment Runbook

## Purpose
Provide a reproducible operational procedure for running benchmark experiments.

## Environment Baseline
- Platform: repository local environment.
- Python environment: `.venv` in repository root.
- Dependencies: `requirements.txt`.
- Optional baseline solver: `gurobi` with local license file.

## Core Runner Paths
- Batch runner: `Test/run_batch_from_filelist.py`
- Special benchmark runner: `Test/run_instances_05_025_125_50_1.py`
- Single instance runner: `Test/run_single_instance.py`

## Solver Set Policy

### Mandatory SAT family set
- `seqcardenc`
- `seqcardenc_ver2`
- `seqcardenc_ver3`
- any new `seqcardenc_*` under evaluation

### Optional external baseline
- `gurobi`

## Timeout Profiles

### Profile T-A (default 2016 lane)
- Per-instance timeout: 300 seconds.

### Profile T-B (exploratory lane)
- Per-instance timeout may differ by exploratory dataset characteristics.
- Any non-default timeout must be explicitly declared in run metadata.
- Current `Dataset_2010` pilot default: 60 seconds per instance (aligned with Liu 2010 setting).

## Fair-Comparison Checklist
Before comparing two solver versions, confirm:
1. Same instance list.
2. Same preprocessing workflow.
3. Same timeout profile.
4. Same machine context.
5. Same output parsing policy.

## Standard Command Patterns

### SAT family benchmark on default lane
```bash
.venv\Scripts\python Test\run_batch_from_filelist.py --types S L --solvers seqcardenc seqcardenc_ver2 seqcardenc_ver3
```

### Tier B pilot generation (Dataset_2010)
```bash
.venv\Scripts\python Test\generate_dataset_2010_pilot.py
```

### Tier B pilot benchmark run (Dataset_2010 lane)
```bash
.venv\Scripts\python Test\run_batch_dataset_2010.py --types S --solvers seqcardenc_ver2 --sizes 20 40 50 --timeout 60
```

### Optional cross-paradigm baseline run
```bash
.venv\Scripts\python Test\run_batch_from_filelist.py --types S L --solvers seqcardenc_ver2 gurobi
```

### Single-instance diagnostic check
```bash
.venv\Scripts\python Test\run_single_instance.py "2016\Ins\wtrd_pred10\S\10_05_005_100_25_1.GSP" --solver seqcardenc_ver3 --timeout 120
```

## Output Expectations
- Solver result workbooks under `2016/results_*.xlsx`.
- Solution text files under `2016/solutions_{solver}/...` when using batch runners.
- Single-instance runner writes temporary outputs only.
- Tier B pilot outputs:
  - `Dataset_2010/results_{solver}.xlsx`
  - `Dataset_2010/solutions_{solver}/{n}-{type}/...`

## Lane Separation Rule
- Timed benchmark lane and diagnostic lane should be separated when diagnostics add overhead.
- Do not mix diagnostic-heavy runs into the main runtime summary without explicit labeling.

## Minimum Run Metadata to Record
- date/time
- solver set
- dataset lane
- timeout profile
- command line used
- workspace commit hash (recommended)
