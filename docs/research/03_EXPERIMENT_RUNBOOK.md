# Experiment Runbook

## Purpose
Provide a reproducible procedure for running experiments in this repository.

## Environment Baseline
- Platform: local repository workspace
- Python environment: `.venv`
- Dependencies: `requirements.txt`
- Optional local baseline: `gurobi` with a local `gurobi.lic`

## Core Paths
- Main batch runner: `Test/run_batch_from_filelist.py`
- Special benchmark runner: `Test/run_instances_05_025_125_50_1.py`
- Single-instance diagnostic runner: `Test/run_single_instance.py`
- Generated demo runner: `Test/run_batch_dataset_2010.py`
- Generated demo creator: `Test/generate_dataset_2010_pilot.py`

## Default vs Explicit Solver Selection
- `common/project_paths.py` defines `DEFAULT_SOLVERS = ["seqcounter", "gurobi"]`
- That default is a convenience setting, not a research protocol
- For benchmark work, pass `--solvers` explicitly

## Timeout Profiles

### Profile A: Default 2016 Lane
- Per-instance timeout: 300 seconds
- Applied by:
  - `Test/run_batch_from_filelist.py`
  - `Test/run_instances_05_025_125_50_1.py`

### Profile B: Generated Demo Lane
- Default per-instance timeout: 60 seconds
- Applied by `Test/run_batch_dataset_2010.py`
- Override is allowed via `--timeout`, but the report must record it

## Pre-Run Checklist
Before comparing solver versions, confirm:
1. same dataset lane
2. same authoritative filelists
3. same preprocessing path (`window_tightening` through `Test/runner_common.py`)
4. same timeout profile
5. same machine context
6. same objective semantics and code state

## Standard Command Patterns

### SAT-family benchmark on the default 2016 lane
```bash
.venv\Scripts\python Test\run_batch_from_filelist.py --types S L --solvers seqcardenc seqcardenc_ver2 seqcardenc_ver3
```

### Expanded solver sweep on the default 2016 lane
```bash
.venv\Scripts\python Test\run_batch_from_filelist.py --types S L --solvers seqcounter seqcardenc seqcardenc_ver2 seqcardenc_ver3 basicsat pbenc gurobi
```

### Special benchmark family `XX_05_025_125_50_1.GSP`
```bash
.venv\Scripts\python Test\run_instances_05_025_125_50_1.py --types S L --solvers seqcardenc_ver2 seqcardenc_ver3 gurobi
```

### Single-instance diagnostic run
```bash
.venv\Scripts\python Test\run_single_instance.py "2016\Ins\wtrd_pred10\S\10_05_005_100_25_1.GSP" --solver seqcardenc_ver3 --timeout 120
```

### Generate the `Dataset_2010` demo lane
```bash
.venv\Scripts\python Test\generate_dataset_2010_pilot.py
```

### Run the `Dataset_2010` demo lane
```bash
.venv\Scripts\python Test\run_batch_dataset_2010.py --types S --solvers seqcardenc_ver2 --sizes 20 40 50 --timeout 60
```

### Graph and dataset diagnostics
```bash
.venv\Scripts\python Graph_in4\visualize_gsp.py --file "2016\Ins\wtrd_pred10\S\10_05_005_100_25_1.GSP"
.venv\Scripts\python Graph_in4\visualize_gsp.py --folder "2016\Ins" --workers 4
.venv\Scripts\python Graph_in4\visualize_batch_from_filelist.py --sizes 10 20 --types S L --workers 4
.venv\Scripts\python Graph_in4\export_stats.py --folder "2016\Ins" --out "Graph_in4\gsp_statistics.xlsx"
```

## Output Expectations

### Default 2016 lane
- workbook: `2016/results_{solver}.xlsx`
- solutions: `2016/solutions_{solver}/{n}-{type}/...`
- solution files giữ schedule chi tiết để phục vụ audit sau run
- SAT stats không được coi là artifact batch mặc định
- `time_s` trong workbook là subprocess wall time, không phải pure solver-search time
- `TIME_LIMIT_FEASIBLE` means Gurobi found an incumbent at the time limit with nonzero MIP gap; workbook `Lmax` is `-` and `gap_%` carries the gap

### Special benchmark family
- workbook: `2016/results_{solver}_05_025_125_50_1.xlsx`

### Single-instance diagnostic
- no persistent workbook
- no persistent solution file
- temporary files only
- SAT stats được ưu tiên hiển thị ở mode này khi solver cung cấp được

### Generated demo lane
- workbook: `Dataset_2010/results_{solver}.xlsx`
- solutions: `Dataset_2010/solutions_{solver}/{n}-{type}/...`
- `time_s` trong workbook là subprocess wall time

## Post-Run Checklist
After a run:
1. record the exact command line
2. note the dataset lane and filelist source
3. record the timeout profile
4. identify the solver set
5. mark whether the compared solvers share the same objective semantics
6. save supporting workbook paths and any logs used in the analysis

## Important Interpretation Rule
The current active solver set is objective-aligned to true `Lmax = max(C_j - d_j)`, but historical result files may predate that alignment. Treat mixed-code-state results as diagnostics unless the objective semantics and code revision are documented.
