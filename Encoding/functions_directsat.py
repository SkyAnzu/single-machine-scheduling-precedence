"""
functions_directsat.py

Direct SAT encoding for single-machine scheduling.

Key properties:
- Uses only start variables S[i,t]
- Enforces machine capacity by direct pairwise no-overlap clauses
- Enforces precedence by direct pairwise forbidden start pairs
- Uses basicsat-style incremental optimization by forbidding bad starts
"""

from pathlib import Path
import sys
import threading
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF
from pysat.solvers import Solver


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.dataset import read_dataset
from common.schedule_utils import compute_max_lateness, format_solution_text, window_tightening


def _build_hard_cnf(
    n,
    durations,
    ready_dates,
    deadlines,
    successors,
    verbose=False,
    timeout=None,
    contradiction_on_impossible=False,
    start_time=None,
):
    """Build the hard CNF using the same encoding path used by the solver."""
    jobs = list(range(1, n + 1))
    cnf = CNF()
    var_counter = 1
    S = {}
    valid_starts = {}
    if start_time is None:
        start_time = time.time()

    def has_timed_out():
        return timeout is not None and (time.time() - start_time) >= timeout

    for i in jobs:
        if has_timed_out():
            return cnf, valid_starts, S, None, "TIMEOUT", {}
        last_start = deadlines[i] - durations[i]
        if last_start < ready_dates[i]:
            if verbose:
                print(f"Job {i} impossible: last_start < ready")
            if contradiction_on_impossible:
                valid_starts[i] = []
                continue
            return None, None, None, None, False, {}

        valid_starts[i] = list(range(ready_dates[i], last_start + 1))
        for t in valid_starts[i]:
            S[(i, t)] = var_counter
            var_counter += 1

    if verbose:
        print(f"Created {len(S)} S variables")

    exactly_one_clauses = 0

    for i in jobs:
        if has_timed_out():
            return cnf, valid_starts, S, None, "TIMEOUT", {}
        start_vars = [S[(i, t)] for t in valid_starts[i]]
        if not start_vars:
            if contradiction_on_impossible:
                cnf.append([])
                exactly_one_clauses += 1
            continue

        enc = CardEnc.equals(
            lits=start_vars,
            bound=1,
            encoding=EncType.seqcounter,
            top_id=var_counter - 1,
        )
        cnf.extend(enc.clauses)
        exactly_one_clauses += len(enc.clauses)
        var_counter = enc.nv + 1

    overlap_clauses = 0

    for index, i in enumerate(jobs):
        for j in jobs[index + 1 :]:
            if has_timed_out():
                return cnf, valid_starts, S, None, "TIMEOUT", {}
            if not valid_starts[i] or not valid_starts[j]:
                continue
            for t_i in valid_starts[i]:
                if has_timed_out():
                    return cnf, valid_starts, S, None, "TIMEOUT", {}
                end_i = t_i + durations[i]
                for t_j in valid_starts[j]:
                    if has_timed_out():
                        return cnf, valid_starts, S, None, "TIMEOUT", {}
                    if t_i < t_j + durations[j] and t_j < end_i:
                        cnf.append([-S[(i, t_i)], -S[(j, t_j)]])
                        overlap_clauses += 1

    precedence_clauses = 0

    for i in jobs:
        for j in successors.get(i, []):
            if has_timed_out():
                return cnf, valid_starts, S, None, "TIMEOUT", {}
            if j > n or not valid_starts[i] or not valid_starts[j]:
                continue
            for t_i in valid_starts[i]:
                if has_timed_out():
                    return cnf, valid_starts, S, None, "TIMEOUT", {}
                finish_i = t_i + durations[i]
                for t_j in valid_starts[j]:
                    if has_timed_out():
                        return cnf, valid_starts, S, None, "TIMEOUT", {}
                    if t_j < finish_i:
                        cnf.append([-S[(i, t_i)], -S[(j, t_j)]])
                        precedence_clauses += 1

    build_stats = {
        "exactly_one_clauses": exactly_one_clauses,
        "overlap_clauses": overlap_clauses,
        "precedence_clauses": precedence_clauses,
        "total_clauses": len(cnf.clauses),
        "total_variables": var_counter - 1,
    }

    if verbose:
        print(f"Exactly-one-start clauses: {exactly_one_clauses}")
        print(f"Direct no-overlap clauses: {overlap_clauses}")
        print(f"Precedence clauses: {precedence_clauses}")
        print(f"Total clauses: {len(cnf.clauses)}")
        print(f"Total variables: {var_counter - 1}")

    return cnf, valid_starts, S, build_stats, True, {}


def count_hard_cnf(n, durations, ready_dates, deadlines, successors):
    """Count hard-constraint CNF variables and clauses without solving."""
    _, _, _, build_stats, _, _ = _build_hard_cnf(
        n,
        durations,
        ready_dates,
        deadlines,
        successors,
        contradiction_on_impossible=True,
    )
    return build_stats["total_variables"], build_stats["total_clauses"]


def solve_SAT(
    n,
    durations,
    ready_dates,
    due_dates,
    deadlines,
    successors,
    verbose=False,
    sat_solver_name="g421",
    timeout=None,
):
    """Build and solve the direct S-only SAT feasibility model."""
    sat_started_at = time.time()
    cnf, valid_starts, S, _, build_status, timeout_stats = _build_hard_cnf(
        n,
        durations,
        ready_dates,
        deadlines,
        successors,
        verbose=verbose,
        timeout=timeout,
        start_time=sat_started_at,
    )
    if build_status == "TIMEOUT":
        return cnf, None, valid_starts, S, None, "TIMEOUT", timeout_stats
    if not build_status:
        return None, None, None, None, None, False, {}

    if verbose:
        print("SAT backend:", sat_solver_name)

    solver = Solver(name=sat_solver_name, bootstrap_with=cnf)
    if timeout is not None and (time.time() - sat_started_at) >= timeout:
        stats = solver.accum_stats()
        solver.delete()
        return cnf, None, valid_starts, S, None, "TIMEOUT", stats

    if timeout is None:
        result = solver.solve()
    else:
        remaining = timeout - (time.time() - sat_started_at)
        if remaining <= 0:
            stats = solver.accum_stats()
            solver.delete()
            return cnf, None, valid_starts, S, None, "TIMEOUT", stats
        interrupt_timer = threading.Timer(remaining, solver.interrupt)
        interrupt_timer.daemon = True
        interrupt_timer.start()
        try:
            result = solver.solve_limited(expect_interrupt=True)
        finally:
            interrupt_timer.cancel()
            if hasattr(solver, "clear_interrupt"):
                solver.clear_interrupt()

    if result is None:
        stats = solver.accum_stats()
        solver.delete()
        return cnf, None, valid_starts, S, None, "TIMEOUT", stats

    if not result:
        solver.delete()
        return None, None, None, None, None, False, {}

    model = solver.get_model()
    solver.delete()

    schedule = {}
    for (i, t), var_id in S.items():
        if model[var_id - 1] > 0:
            schedule[i] = t

    initial_lmax = compute_UB_Lmax(schedule, durations, due_dates)
    return cnf, schedule, valid_starts, S, initial_lmax, True, {}


def compute_UB_Lmax(schedule, durations, due_dates):
    """Compute true maximum lateness from a concrete schedule."""
    return compute_max_lateness(schedule, durations, due_dates, clamp_zero=False)


def incremental_SAT_Lmax(
    durations,
    due_dates,
    S_dict,
    placeholder,
    cnf,
    UB,
    sol_file,
    valid_starts,
    timeout=300,
    elapsed_offset=0.0,
    verbose=False,
    sat_solver_name="g421",
):
    """Basicsat-style incremental optimization for the S-only direct encoding."""
    del placeholder, valid_starts

    start_time = time.time()
    solver = Solver(name=sat_solver_name, bootstrap_with=cnf)
    iteration_count = 0
    var_to_S = {v: (i, t) for (i, t), v in S_dict.items()}
    best_schedule = {}
    best_lmax = UB
    timed_out = False

    if verbose:
        print("\n=== SOLVING INCREMENTAL DIRECT SAT ===")
        print("SAT backend:", sat_solver_name)

    while True:
        elapsed = time.time() - start_time
        if elapsed >= timeout:
            timed_out = True
            if verbose:
                print(f"Timeout after {elapsed:.1f}s at iteration {iteration_count}")
            break

        iteration_count += 1
        if verbose:
            print("\n==============================")
            print(f"Iteration {iteration_count}: Trying UB = {UB}")

        timed_out_during_tightening = False
        for (i, t), var in S_dict.items():
            if (time.time() - start_time) >= timeout:
                timed_out = True
                timed_out_during_tightening = True
                if verbose:
                    print(f"Timeout during tightening at iteration {iteration_count}")
                break
            lateness = t + durations[i] - due_dates[i]
            if lateness >= UB:
                solver.add_clause([-var])

        if timed_out_during_tightening:
            break

        remaining = timeout - (time.time() - start_time)
        if remaining <= 0:
            timed_out = True
            if verbose:
                print(f"Timeout before solve at iteration {iteration_count}")
            break

        interrupt_timer = threading.Timer(remaining, solver.interrupt)
        interrupt_timer.daemon = True
        interrupt_timer.start()
        try:
            result = solver.solve_limited(expect_interrupt=True)
        finally:
            interrupt_timer.cancel()
            if hasattr(solver, "clear_interrupt"):
                solver.clear_interrupt()

        if result is None:
            timed_out = True
            if verbose:
                print(f"Timeout during solve at iteration {iteration_count}")
            break

        if result:
            if verbose:
                print("SAT - found solution")

            model = solver.get_model()
            best_schedule = {}
            for var in model:
                if var > 0 and var in var_to_S:
                    i, t = var_to_S[var]
                    best_schedule[i] = t

            lmax = compute_UB_Lmax(best_schedule, durations, due_dates)
            if verbose:
                print(f"New Lmax: {lmax}")
                if UB == lmax:
                    print("Warning: UB not decreasing")

            UB = lmax
            best_lmax = lmax

            with open(sol_file, "w", encoding="utf-8") as handle:
                handle.write(format_solution_text(best_schedule, durations, due_dates, UB))
                handle.flush()
        else:
            if verbose:
                print("UNSAT - cannot improve further")
            break

    stats = solver.accum_stats()
    solver.delete()

    if best_schedule:
        with open(sol_file, "w", encoding="utf-8") as handle:
            handle.write(format_solution_text(best_schedule, durations, due_dates, best_lmax))
            handle.flush()

    if verbose:
        with open(sol_file, "a", encoding="utf-8") as handle:
            handle.write(
                f"STATS "
                f"conflicts={stats.get('conflicts', 0)} "
                f"decisions={stats.get('decisions', 0)} "
                f"propagations={stats.get('propagations', 0)} "
                f"restarts={stats.get('restarts', 0)}\n"
            )
        print("\nIncremental SAT finished.")
        print(f"Best Lmax found: {best_lmax}")

    solve_time = elapsed_offset + (time.time() - start_time)
    return best_lmax, best_schedule, solve_time, timed_out
