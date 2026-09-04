from functions_seqcardenc_ver5 import (
    compute_UB_Lmax,
    count_hard_cnf as _count_hard_cnf,
    incremental_SAT_Lmax,
    read_dataset,
    solve_SAT as _solve_SAT,
    window_tightening,
)


def count_hard_cnf(n, durations, ready_dates, deadlines, successors):
    return _count_hard_cnf(
        n,
        durations,
        ready_dates,
        deadlines,
        successors,
        include_source_ready_anchor=False,
    )


def solve_SAT(n, durations, ready_dates, deadlines, successors, verbose=False, sat_solver_name="g421"):
    return _solve_SAT(
        n,
        durations,
        ready_dates,
        deadlines,
        successors,
        verbose=verbose,
        sat_solver_name=sat_solver_name,
        include_source_ready_anchor=False,
    )
