from pysat.solvers import Solver

from common.dataset import read_dataset
from common.schedule_utils import (
    compute_max_lateness,
    format_solution_text,
    validate_schedule as shared_validate_schedule,
    window_tightening,
)
from functions_seqcardenc_ver5 import _build_hard_cnf


def count_hard_cnf(n, durations, ready_dates, deadlines, successors, include_source_ready_anchor=True):
    """Count the same hard CNF as ver5 without solving."""
    _, _, _, _, build_stats, _ = _build_hard_cnf(
        n,
        durations,
        ready_dates,
        deadlines,
        successors,
        contradiction_on_impossible=True,
        include_source_ready_anchor=include_source_ready_anchor,
    )
    return build_stats["total_variables"], build_stats["total_clauses"]


def solve_SAT(
    n,
    durations,
    ready_dates,
    deadlines,
    successors,
    verbose=False,
    sat_solver_name="g421",
    include_source_ready_anchor=True,
):
    """Solve feasibility and return the live solver for objective tightening."""
    cnf, valid_starts, S, L, _, build_status = _build_hard_cnf(
        n,
        durations,
        ready_dates,
        deadlines,
        successors,
        verbose=verbose,
        include_source_ready_anchor=include_source_ready_anchor,
    )
    if not build_status:
        return None, None, None, None, None, False, None

    print("\n=== SOLVING (HARD CONSTRAINTS ONLY) ===")
    if verbose:
        print("SAT backend:", sat_solver_name)
    solver = Solver(name=sat_solver_name, bootstrap_with=cnf)
    is_sat = solver.solve()

    if not is_sat:
        if verbose:
            print("UNSAT -- no feasible schedule.")
        solver.delete()
        return None, None, None, None, None, is_sat, None

    raw_model = solver.get_model()
    assert raw_model is not None, "Solver returned SAT but model is None"
    model = set(raw_model)

    schedule = {}
    for (i, t), vid in S.items():
        if vid in model:
            schedule[i] = t

    if verbose:
        print("Feasible schedule found")

    return cnf, schedule, valid_starts, S, L, is_sat, solver


def validate_schedule(schedule, durations, ready_dates, deadlines, successors):
    _, violations = shared_validate_schedule(
        schedule,
        len(durations),
        durations,
        ready_dates,
        deadlines,
        successors,
    )
    return violations


def compute_UB_Lmax(schedule, durations, due_dates):
    return compute_max_lateness(schedule, durations, due_dates, clamp_zero=False)


def incremental_SAT_Lmax(
    durations,
    due_dates,
    S,
    L,
    solver,
    UB,
    sol_file,
    valid_starts,
    verbose=False,
):
    """Tighten the objective using the live solver from solve_SAT."""
    iteration_count = 0
    var_to_S = {v: (i, t) for (i, t), v in S.items()}

    print("\n=== SOLVING INCREMENTAL SAT (SINGLE SOLVER) ===")

    while True:
        iteration_count += 1
        if verbose:
            print("\n==============================")
            print("Trying with Lmax UB =", UB)
            print("Iteration:", iteration_count)

        for j in range(1, len(durations) + 1):
            latest_start = due_dates[j] + UB - durations[j] - 1
            if latest_start < valid_starts[j][0]:
                solver.add_clause([])
            elif latest_start < valid_starts[j][-1]:
                solver.add_clause([L[(j, latest_start)]])

        if solver.solve():
            if verbose:
                print("SAT")
            raw_model = solver.get_model()
            assert raw_model is not None, "Solver returned SAT but model is None"
            best_schedule = {}

            for var in raw_model:
                if var > 0 and var in var_to_S:
                    i, t = var_to_S[var]
                    best_schedule[i] = t

            lmax = compute_UB_Lmax(best_schedule, durations, due_dates)

            if verbose:
                print("New Lmax UB:", lmax)
                if UB == lmax:
                    print("Warning: UB not decreasing, possible bug.")

            UB = lmax
            with open(sol_file, "w", encoding="utf-8") as handle:
                handle.write(format_solution_text(best_schedule, durations, due_dates, UB))
                handle.flush()
        else:
            if verbose:
                print("UNSAT")
            break

    stats = solver.accum_stats()
    solver.delete()

    if verbose:
        with open(sol_file, "a", encoding="utf-8") as handle:
            handle.write(
                f"STATS "
                f"conflicts={stats.get('conflicts', 0)} "
                f"decisions={stats.get('decisions', 0)} "
                f"propagations={stats.get('propagations', 0)} "
                f"restarts={stats.get('restarts', 0)}\n"
            )
        print(
            f"SAT stats — iterations: {iteration_count}, "
            f"conflicts: {stats.get('conflicts', 0)}, "
            f"decisions: {stats.get('decisions', 0)}, "
            f"propagations: {stats.get('propagations', 0)}, "
            f"restarts: {stats.get('restarts', 0)}"
        )

    print("Incremental SAT finished.")
    print("Best Lmax UB found:", UB)
    return UB
