# Internal Benchmark Report Template

## 1. Run Metadata
- Date:
- Author:
- Repository commit:
- Dataset lane: Tier A / Tier B
- Timeout profile:
- Solver set:
- Commands:

## 2. Scope of This Report
- Comparison target:
- Reference solver/version:
- Candidate solver/version:
- Instance scope:

## 3. Correctness Summary

### 3.1 Status Consistency (shared instances)
| Category | Count |
|---|---:|
| Shared instances |  |
| Same status |  |
| Different status |  |

### 3.2 Objective Consistency (shared `FINISHED`)
| Category | Count |
|---|---:|
| Shared `FINISHED` instances |  |
| Same `Lmax` |  |
| Different `Lmax` |  |

## 4. Runtime Summary
| Metric | Reference | Candidate |
|---|---:|---:|
| Solved count |  |  |
| Timeout count |  |  |
| Mean time (shared `FINISHED`) |  |  |
| Median time (shared `FINISHED`) |  |  |

### 4.1 Paired Delta View
| Category | Count |
|---|---:|
| Candidate faster |  |
| Candidate slower |  |
| Equal time |  |

## 5. Hard-Case Regression Table
Use this table for high-impact regressions.

| Instance | Reference status/time/Lmax | Candidate status/time/Lmax | Delta | Notes |
|---|---|---|---|---|
|  |  |  |  |  |

## 6. SAT Internal Summary (if collected)
| Metric | Reference | Candidate | Comment |
|---|---:|---:|---|
| decisions |  |  |  |
| conflicts |  |  |  |
| propagations |  |  |  |

## 7. Clause/Encoding Diagnostics (optional)
| Metric | Reference | Candidate | Comment |
|---|---:|---:|---|
| variables |  |  |  |
| clauses |  |  |  |
| binary clauses |  |  |  |
| ternary clauses |  |  |  |

## 8. Interpretation
- Key observations:
- Likely mechanism:
- Risk assessment:

## 9. Recommendation
- Decision: keep / reject / iterate.
- Required follow-up:

## 10. Evidence Index
- Result workbook paths:
- Logs/artifacts:
- Scripts/commands used:
