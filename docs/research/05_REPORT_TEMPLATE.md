# Internal Benchmark Report Template

## 1. Run Metadata
- Date:
- Author:
- Repository commit:
- Dataset lane:
- Filelist source:
- Timeout profile:
- Preprocessing path:
- Solver set:
- Objective semantics checked:
- Commands:

## 2. Scope of This Report
- Comparison target:
- Reference solver/version:
- Candidate solver/version:
- Instance scope:
- Report type:
  - clean objective comparison / implementation diagnostic / generated-lane demo

## 3. Objective-Semantics Note
- Reference objective behavior:
- Candidate objective behavior:
- Are the compared values directly comparable? yes / no
- If no, what is still being compared fairly?

## 4. Status / Feasibility Summary

### 4.1 Shared-instance status comparison
| Category | Count |
|---|---:|
| Shared instances |  |
| Same status |  |
| Different status |  |
| Missing / unparseable |  |

### 4.2 Status divergence details
| Instance | Reference status | Candidate status | Notes |
|---|---|---|---|
|  |  |  |  |

## 5. Objective Summary
Only fill this section for objective-aligned comparisons.

### 5.1 Shared comparable finished instances
| Category | Count |
|---|---:|
| Shared comparable `FINISHED` instances |  |
| Same objective value |  |
| Different objective value |  |

### 5.2 Objective divergence details
| Instance | Reference value | Candidate value | Delta | Notes |
|---|---:|---:|---:|---|
|  |  |  |  |  |

## 6. Runtime Summary
| Metric | Reference | Candidate |
|---|---:|---:|
| Solved count |  |  |
| Timeout count |  |  |
| Mean time on comparable set |  |  |
| Median time on comparable set |  |  |

### 6.1 Paired runtime view
| Category | Count |
|---|---:|
| Candidate faster |  |
| Candidate slower |  |
| Equal time |  |

## 7. Hard-Case Divergence Table
| Instance | Reference status/time/value | Candidate status/time/value | Delta | Notes |
|---|---|---|---|---|
|  |  |  |  |  |

## 8. SAT / Solver Internal Summary
Fill when collected.

| Metric | Reference | Candidate | Comment |
|---|---:|---:|---|
| conflicts |  |  |  |
| decisions |  |  |  |
| propagations |  |  |  |
| restarts |  |  |  |
| MIP gap (if relevant) |  |  |  |

## 9. Interpretation
- Main findings:
- Likely explanation:
- Risks / caveats:
- Dataset-lane caveats:
- Objective-semantics caveats:

## 10. Recommendation
- Decision: keep / reject / iterate
- Follow-up experiment:
- Required documentation updates:

## 11. Evidence Index
- Workbook paths:
- Solution directories:
- Logs / console captures:
- Graph or dataset diagnostics:
