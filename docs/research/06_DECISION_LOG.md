# Decision Log

Use this file to record protocol-affecting decisions.

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
