"""
Solve the Single Machine Scheduling Problem with Precedence Constraints using
IBM CPLEX MP through DOcplex.

This module is intentionally present even when CPLEX is not installed. Missing
Python packages or CPLEX runtime/license issues are returned as explicit solver
statuses so batch runs can record the environment limitation.
"""

from pathlib import Path
import os
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.dataset import read_dataset
from common.schedule_utils import window_tightening


def solve_with_cplex_mp(n, durations, ready_dates, due_dates, deadlines, successors, time_limit=300):
    try:
        from docplex.mp.model import Model
    except ImportError:
        return None, "STATUS_MISSING_DOCPLEX_MP", False, 0, None

    jobs = range(1, n + 1)
    for job in jobs:
        if deadlines[job] - durations[job] < ready_dates[job]:
            return None, "INFEASIBLE", False, 0, None

    try:
        model = Model(name="SingleMachineScheduling_CPLEX_MP", log_output=False)
        model.parameters.timelimit = time_limit
        model.parameters.threads = max(1, (os.cpu_count() or 2) // 2)

        horizon = max(deadlines.values()) + max(durations.values())
        starts = {
            job: model.integer_var(
                lb=ready_dates[job],
                ub=deadlines[job] - durations[job],
                name=f"S_{job}",
            )
            for job in jobs
        }
        lmax = model.integer_var(lb=-model.infinity, name="Lmax")

        for job in jobs:
            model.add_constraint(lmax >= starts[job] + durations[job] - due_dates[job], ctname=f"lmax_{job}")

        for job in jobs:
            for successor in successors.get(job, []):
                model.add_constraint(starts[job] + durations[job] <= starts[successor], ctname=f"prec_{job}_{successor}")

        pairs = [(i, j) for i in jobs for j in range(i + 1, n + 1)]
        before = model.binary_var_dict(pairs, name="before")
        for i, j in pairs:
            model.add_constraint(starts[i] + durations[i] <= starts[j] + horizon * (1 - before[i, j]), ctname=f"disj1_{i}_{j}")
            model.add_constraint(starts[j] + durations[j] <= starts[i] + horizon * before[i, j], ctname=f"disj2_{i}_{j}")

        model.minimize(lmax)
        solution = model.solve(log_output=False)
        solve_time = float(getattr(model.solve_details, "time", 0) or 0)

        if solution is not None:
            schedule = {job: int(round(solution.get_value(starts[job]))) for job in jobs}
            objective = int(round(solution.get_value(lmax)))
            gap = getattr(model.solve_details, "mip_relative_gap", None)
            gap_percent = None if gap is None else float(gap) * 100
            status_name = str(getattr(model.solve_details, "status", "")).lower()
            if gap_percent is not None and gap_percent > 0:
                return schedule, objective, "TIME_LIMIT_FEASIBLE", solve_time, gap_percent
            if "time" in status_name and gap_percent is None:
                return schedule, objective, "TIME_LIMIT_FEASIBLE", solve_time, None
            return schedule, objective, True, solve_time, 0.0

        status_name = str(getattr(model.solve_details, "status", "STATUS_NO_SOLUTION"))
        if "infeasible" in status_name.lower():
            return None, "INFEASIBLE", False, solve_time, None
        if "time" in status_name.lower():
            return None, "TIMEOUT", False, solve_time, None
        return None, f"STATUS_{status_name.replace(' ', '_').upper()}", False, solve_time, None
    except Exception as exc:
        status = type(exc).__name__.upper()
        return None, f"STATUS_CPLEX_MP_{status}", False, 0, None


def solve_MIP(n, durations, ready_dates, due_dates, deadlines, successors, time_limit=300):
    return solve_with_cplex_mp(n, durations, ready_dates, due_dates, deadlines, successors, time_limit)
