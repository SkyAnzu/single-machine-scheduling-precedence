from pathlib import Path
import sys

from pysat.card import CardEnc, EncType
from pysat.formula import CNF
from pysat.solvers import Solver


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.dataset import read_dataset
from common.schedule_utils import compute_max_lateness, format_solution_text, validate_schedule as shared_validate_schedule, window_tightening


def solve_SAT(n, durations, ready_dates, deadlines, successors, verbose=False):
    jobs = list(range(1, n + 1))
    horizon = max(deadlines.values())

    cnf = CNF()
    var_counter = 1

    S = {}
    A = {}
    L = {}
    valid_starts = {}

    for i in jobs:
        last_start = deadlines[i] - durations[i]
        if last_start < ready_dates[i]:
            if verbose:
                print(f"Job {i} impossible: last_start < ready ({last_start} < {ready_dates[i]})")
            return None, None, None, None, None, False

        valid_starts[i] = list(range(ready_dates[i], last_start + 1))
        for t in valid_starts[i]:
            S[(i, t)] = var_counter
            var_counter += 1

    for i in jobs:
        for t in range(ready_dates[i], deadlines[i]):
            A[(i, t)] = var_counter
            var_counter += 1

    if verbose:
        print(f"Created S variables: {len(S)}, A variables: {len(A)}. Next var id = {var_counter}")

    s_to_a_clauses = 0
    for i in jobs:
        for t0 in valid_starts[i]:
            s_lit = S[(i, t0)]
            for t in range(t0, t0 + durations[i]):
                if (i, t) in A:
                    cnf.append([-s_lit, A[(i, t)]])
                    s_to_a_clauses += 1

    if verbose:
        print("S->A clauses:", s_to_a_clauses)

    cap_clauses = 0
    for t in range(horizon):
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

    l_count = 0
    l_clauses = 0
    for j in jobs:
        times = valid_starts[j]
        if not times:
            continue
        t_min = times[0]
        t_max = times[-1]

        for t in range(t_min, t_max + 1):
            L[(j, t)] = var_counter
            var_counter += 1
            l_count += 1

        cnf.append([L[(j, t_max)]])
        cnf.append([-L[(j, t_min)], S[(j, t_min)]])
        l_clauses += 2

        for t in range(t_min, t_max + 1):
            cnf.append([L[(j, t)], -S[(j, t)]])
            l_clauses += 1

        for t in range(t_min + 1, t_max + 1):
            cnf.append([-S[(j, t)], -L[(j, t - 1)]])
            cnf.append([L[(j, t)], -L[(j, t - 1)]])
            cnf.append([-L[(j, t)], L[(j, t - 1)], S[(j, t)]])
            l_clauses += 3

    if verbose:
        print("L variables:", l_count)
        print("L clauses:", l_clauses)

    prec_clauses = 0
    for i in jobs:
        for j in successors.get(i, []):
            if not valid_starts[i] or not valid_starts[j]:
                continue
            t_min_j = valid_starts[j][0]
            t_max_j = valid_starts[j][-1]

            for t_i in valid_starts[i]:
                finish = t_i + durations[i] - 1
                if finish < t_min_j or finish > t_max_j:
                    continue
                cnf.append([-S[(i, t_i)], -L[(j, finish)]])
                prec_clauses += 1

    if verbose:
        print("Precedence clauses:", prec_clauses)
        print("Total clauses:", prec_clauses + l_clauses + cap_clauses + s_to_a_clauses)
        print("Total variables:", var_counter - 1)

    print("\n=== SOLVING (HARD CONSTRAINTS ONLY) ===")
    solver = Solver(name="g421", bootstrap_with=cnf)
    is_sat = solver.solve()

    if not is_sat:
        if verbose:
            print("UNSAT -- no feasible schedule.")
        return None, None, None, None, None, is_sat

    raw_model = solver.get_model()
    assert raw_model is not None, "Solver returned SAT but model is None"
    model = set(raw_model)

    schedule = {}
    for (i, t), vid in S.items():
        if vid in model:
            schedule[i] = t

    if verbose:
        print("Feasible schedule found")
    solver.delete()

    return cnf, schedule, valid_starts, S, L, is_sat


def validate_schedule(schedule, durations, ready_dates, deadlines, successors):
    _, violations = shared_validate_schedule(schedule, len(durations), durations, ready_dates, deadlines, successors)
    return violations


def compute_UB_Lmax(schedule, durations, due_dates):
    return compute_max_lateness(schedule, durations, due_dates, clamp_zero=False)


def incremental_SAT_Lmax(durations, due_dates, S, L, cnf, UB, sol_file, valid_starts, verbose=False):
    solver = Solver(name="g421", bootstrap_with=cnf)
    iteration_count = 0
    var_to_S = {v: (i, t) for (i, t), v in S.items()}

    print("\n=== SOLVING INCREMENTAL SAT ===")

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
            model = raw_model
            best_schedule = {}

            for var in model:
                if var > 0 and var in var_to_S:
                    i, t = var_to_S[var]
                    best_schedule[i] = t

            Lmax = compute_UB_Lmax(best_schedule, durations, due_dates)

            if verbose:
                print("New Lmax UB:", Lmax)
                if UB == Lmax:
                    print("Warning: UB not decreasing, possible bug.")

            UB = Lmax
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

    print("Incremental SAT finished.")
    print("Best Lmax UB found:", UB)
    if verbose:
        print(
            f"SAT stats — iterations: {iteration_count}, "
            f"conflicts: {stats.get('conflicts', 0)}, "
            f"decisions: {stats.get('decisions', 0)}, "
            f"propagations: {stats.get('propagations', 0)}, "
            f"restarts: {stats.get('restarts', 0)}"
        )
