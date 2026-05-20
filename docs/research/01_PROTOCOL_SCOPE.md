# Internal Research Protocol Scope

## Purpose
Define the current research scope for this repository.

This workspace combines:
- Liu 2010 as the main objective reference for maximum lateness reasoning.
- Davari et al. 2016 as the practical source of the `.GSP`-style data fields and the default workspace lane under `2016/Ins/`.

## Problem View Used in This Repository
The current repository studies single-machine scheduling with:
- precedence constraints
- release dates / ready times
- due dates
- deadlines / time windows

The default runner workflow uses 2016-format instances, while many experiments interpret the objective in a Liu-2010-inspired `Lmax` setting.

## Main Research Questions
1. Within the `seqcardenc` family, which encoding variant gives the best trade-off between feasibility behavior, runtime, and SAT internal signals?
2. Under identical filelists, preprocessing and timeouts, where do hard-case regressions appear?
3. How do SAT encodings compare with a `gurobi` MIP baseline when objective semantics are aligned?
4. How does the generated `Dataset_2010` demo lane behave as a diagnostic lane, without promoting it to the default benchmark lane?

## In Scope
- Comparisons inside `seqcardenc`, `seqcardenc_ver2`, `seqcardenc_ver3`, and future `seqcardenc_*`
- Default benchmark lane under `2016/Ins/`
- Generated demo lane `Dataset_2010/` for exploratory diagnostics
- Status consistency, objective consistency, runtime, and SAT internals
- Reproducible command lines and timeout profiles

## Objective-Semantics Rule
At the current workspace state, the active solver set uses true Liu-style maximum lateness:
- `Lmax = max(C_j - d_j)`
- `Lmax` may be negative

Current aligned solver set:
- `seqcounter`
- `seqcardenc`
- `seqcardenc_ver2`
- `seqcardenc_ver3`
- `pbenc`
- `basicsat`
- `gurobi`

Therefore:
- cross-solver objective comparisons are allowed only after status consistency and parser behavior are checked
- when reporting results, state the compared solver set and objective semantics
- historical workbooks produced before the alignment must not be mixed with new results without labeling the code state

## Out of Scope
- Treating the 2016 paper objective (`sum w_j T_j`) as if it were already implemented in the current SAT lane
- Mixing `Dataset_2010/` demo results into the default 2016 benchmark summary without explicit labeling
- Making performance claims from clause count alone
- Cross-machine speed claims without a controlled environment
- Assuming folder contents are the benchmark set when filelists say otherwise

## Required Deliverables Per Benchmark Cycle
1. Run metadata:
   - dataset lane
   - filelist source
   - preprocessing path
   - timeout profile
   - solver set
   - machine context
2. Correctness summary:
   - status consistency
   - objective consistency inside an objective-aligned set
3. Runtime summary:
   - solved / timeout counts
   - paired runtime comparison when relevant
4. Hard-case divergence table
5. SAT internal summary when collected
6. Evidence-based conclusion

## Operational Baseline
- Default input lane: `2016/Ins/`
- Filelist authority: `Filenames/{size}-{type}.txt` when present, otherwise `Filenames/{size}.txt`
- Main runner stack: `Test/runner_common.py` plus batch / single-instance scripts
- Primary SAT family under evaluation: `seqcardenc*`
- Optional external baseline: `gurobi`
