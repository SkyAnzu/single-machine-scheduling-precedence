"""
LamPham SAT encoding for single-machine scheduling with precedence constraints.

The hard encoding follows the supplied implementation: S start variables, A
activity variables, L prefix variables, sequential-cardinality capacity, and
L-based precedence clauses. The surrounding timeout and output handling is
adapted to the repository runner.
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


def _solve_limited(solver, timeout):
    if timeout is None:
        return solver.solve()
    if timeout <= 0:
        return None

    interrupt_timer = threading.Timer(timeout, solver.interrupt)
    interrupt_timer.daemon = True
    interrupt_timer.start()
    try:
        return solver.solve_limited(expect_interrupt=True)
    finally:
        interrupt_timer.cancel()
        if hasattr(solver, "clear_interrupt"):
            solver.clear_interrupt()


def solve_SAT(
    n,
    durations,
    ready_dates,
    deadlines,
    successors,
    verbose=False,
    sat_solver_name="g421",
    timeout=None,
):
    """Build and solve the supplied S+A+L LamPham feasibility encoding."""
    jobs = list(range(1, n + 1))
    horizon = max(deadlines.values())
    started_at = time.time()

    def timed_out():
        return timeout is not None and time.time() - started_at >= timeout

    cnf = CNF()
    var_counter = 1
    S = {}
    A = {}
    L = {}
    valid_starts = {}

    # Create S variables over the valid start windows.
    for i in jobs:
        if timed_out():
            return None, None, None, None, None, "TIMEOUT"
        last_start = deadlines[i] - durations[i]
        if last_start < ready_dates[i]:
            if verbose:
                print(f"Job {i} impossible: last_start < ready ({last_start} < {ready_dates[i]})")
            return None, None, None, None, None, False

        valid_starts[i] = list(range(ready_dates[i], last_start + 1))
        for t in valid_starts[i]:
            if timed_out():
                return None, None, None, None, None, "TIMEOUT"
            S[(i, t)] = var_counter
            var_counter += 1

    # Create A variables over the activity horizon.
    for i in jobs:
        for t in range(ready_dates[i], deadlines[i]):
            if timed_out():
                return None, None, None, None, None, "TIMEOUT"
            A[(i, t)] = var_counter
            var_counter += 1

    if verbose:
        print(f"Created S variables: {len(S)}, A variables: {len(A)}. Next var id = {var_counter}")

    # Activation: S(i,t0) -> A(i,t) for every processing slot covered by t0.
    s_to_a_clauses = 0
    for i in jobs:
        p_i = durations[i]
        for t0 in valid_starts[i]:
            if timed_out():
                return None, None, None, None, None, "TIMEOUT"
            s_lit = S[(i, t0)]
            for t in range(t0, t0 + p_i):
                if timed_out():
                    return None, None, None, None, None, "TIMEOUT"
                if (i, t) in A:
                    cnf.append([-s_lit, A[(i, t)]])
                    s_to_a_clauses += 1

    if verbose:
        print("S->A clauses:", s_to_a_clauses)

    # Capacity: at most one active job at each time point.
    cap_clauses = 0
    for t in range(horizon):
        if timed_out():
            return None, None, None, None, None, "TIMEOUT"
        active_vars = [A[(i, t)] for i in jobs if (i, t) in A]
        if len(active_vars) > 1:
            enc = CardEnc.atmost(
                lits=active_vars,
                bound=1,
                encoding=EncType.seqcounter,
                top_id=var_counter - 1,
            )
            cnf.extend(enc.clauses)
            cap_clauses += len(enc.clauses)
            var_counter = enc.nv + 1

    if verbose:
        print(f"Capacity clauses: {cap_clauses}. Next var id = {var_counter}")

    # L prefix variables. This also enforces one start time per job.
    l_count = 0
    l_clauses = 0
    for j in jobs:
        times = valid_starts[j]
        if not times:
            continue
        t_min = times[0]
        t_max = times[-1]

        for t in range(t_min, t_max + 1):
            if timed_out():
                return None, None, None, None, None, "TIMEOUT"
            L[(j, t)] = var_counter
            var_counter += 1
            l_count += 1

        cnf.append([L[(j, t_max)]])
        cnf.append([-L[(j, t_min)], S[(j, t_min)]])
        l_clauses += 2

        for t in range(t_min, t_max + 1):
            if timed_out():
                return None, None, None, None, None, "TIMEOUT"
            cnf.append([L[(j, t)], -S[(j, t)]])
            l_clauses += 1

        for t in range(t_min + 1, t_max + 1):
            if timed_out():
                return None, None, None, None, None, "TIMEOUT"
            cnf.append([-S[(j, t)], -L[(j, t - 1)]])
            cnf.append([L[(j, t)], -L[(j, t - 1)]])
            cnf.append([-L[(j, t)], L[(j, t - 1)], S[(j, t)]])
            l_clauses += 3

    if verbose:
        print("L variables:", l_count)
        print("L clauses:", l_clauses)

    # Precedence: forbid an immediate successor prefix state that starts too early.
    prec_clauses = 0
    for i in jobs:
        for j in successors.get(i, []):
            if timed_out():
                return None, None, None, None, None, "TIMEOUT"
            if not valid_starts[i] or not valid_starts[j]:
                continue
            t_min_j = valid_starts[j][0]
            t_max_j = valid_starts[j][-1]
            p_i = durations[i]

            for t_i in valid_starts[i]:
                if timed_out():
                    return None, None, None, None, None, "TIMEOUT"
                finish = t_i + p_i - 1
                if finish < t_min_j or finish > t_max_j:
                    continue
                cnf.append([-S[(i, t_i)], -L[(j, finish)]])
                prec_clauses += 1

    if verbose:
        print("Precedence clauses:", prec_clauses)
        print("Total clauses:", prec_clauses + l_clauses + cap_clauses + s_to_a_clauses)
        print("Total variables:", var_counter - 1)

    if timed_out():
        return None, None, None, None, None, "TIMEOUT"

    if verbose:
        print("\n=== SOLVING (HARD CONSTRAINTS ONLY) ===")
        print("SAT backend:", sat_solver_name)
    solver = Solver(name=sat_solver_name, bootstrap_with=cnf)
    remaining = None if timeout is None else timeout - (time.time() - started_at)
    is_sat = _solve_limited(solver, remaining)

    if is_sat is None:
        solver.delete()
        return None, None, None, None, None, "TIMEOUT"
    if not is_sat:
        solver.delete()
        if verbose:
            print("UNSAT -- no feasible schedule.")
        return None, None, None, None, None, False

    model = set(solver.get_model())
    schedule = {
        i: t
        for (i, t), variable in S.items()
        if variable in model
    }
    solver.delete()
    if verbose:
        print("Feasible schedule found")
    return cnf, schedule, valid_starts, S, L, True


def compute_UB_Lmax(schedule, durations, due_dates):
    return compute_max_lateness(schedule, durations, due_dates, clamp_zero=False)


def incremental_SAT_Lmax(
    durations,
    due_dates,
    S,
    L,
    cnf,
    UB,
    sol_file,
    valid_starts,
    verbose=False,
    sat_solver_name="g421",
    timeout=300,
):
    """Run the supplied L-based incremental optimization with a 300s default."""
    solver = Solver(name=sat_solver_name, bootstrap_with=cnf)
    var_to_S = {variable: (i, t) for (i, t), variable in S.items()}
    best_schedule = {}
    best_lmax = UB
    started_at = time.time()
    iteration_count = 0
    timed_out = False

    if verbose:
        print("\n=== SOLVING INCREMENTAL SAT ===")
        print("SAT backend:", sat_solver_name)

    while True:
        if time.time() - started_at >= timeout:
            timed_out = True
            break

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

        remaining = timeout - (time.time() - started_at)
        if remaining <= 0:
            timed_out = True
            break
        result = _solve_limited(solver, remaining)
        if result is None:
            timed_out = True
            break
        if not result:
            if verbose:
                print("UNSAT")
            break

        model = solver.get_model()
        best_schedule = {
            i: t
            for variable in model
            if variable > 0 and variable in var_to_S
            for i, t in [var_to_S[variable]]
        }
        current_lmax = compute_UB_Lmax(best_schedule, durations, due_dates)
        if verbose:
            print("SAT")
            print("New Lmax UB:", current_lmax)
            if UB == current_lmax:
                print("Warning: UB not decreasing, possible bug.")

        UB = current_lmax
        best_lmax = current_lmax
        with open(sol_file, "w", encoding="utf-8") as handle:
            handle.write(format_solution_text(best_schedule, durations, due_dates, UB))

    stats = solver.accum_stats()
    solver.delete()

    if best_schedule:
        with open(sol_file, "w", encoding="utf-8") as handle:
            handle.write(format_solution_text(best_schedule, durations, due_dates, best_lmax))
    if verbose:
        with open(sol_file, "a", encoding="utf-8") as handle:
            handle.write(
                f"STATS conflicts={stats.get('conflicts', 0)} "
                f"decisions={stats.get('decisions', 0)} "
                f"propagations={stats.get('propagations', 0)} "
                f"restarts={stats.get('restarts', 0)}\n"
            )
        print("Incremental SAT finished.")
        print("Best Lmax UB found:", best_lmax)

    return best_lmax, best_schedule, timed_out
