"""
functions_gurobi.py

Solve the Single Machine Scheduling Problem with Precedence Constraints using Gurobi MIP.

Formulation:
- Decision variables: S[i] = start time of job i
- Objective: Minimize Lmax = max_i (S[i] + duration[i] - due_date[i])
- Constraints:
  1. Time windows: ready_date[i] <= S[i] <= deadline[i] - duration[i]
  2. Precedence: S[i] + duration[i] <= S[j] for all i -> j
  3. No overlap: disjunctive constraints for every pair (i, j)
"""

import os
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.dataset import read_dataset
from common.schedule_utils import window_tightening

# Set Gurobi license file path (WLS license)
_license_file = PROJECT_ROOT / "gurobi.lic"
if _license_file.exists():
    os.environ['GRB_LICENSE_FILE'] = str(_license_file)

import gurobipy as gp
from gurobipy import GRB


def solve_with_gurobi(n, durations, ready_dates, due_dates, deadlines, successors, time_limit=300):
    """
    Solve the problem using Gurobi MIP.
    
    Returns:
        schedule: dict {job_id: start_time}
        lmax: maximum lateness
        is_sat: True if a feasible schedule is found
        solve_time: solve time in seconds
        gap: MIP gap (%)
    """
    
    try:
        # Create model
        model = gp.Model("SingleMachineScheduling")
        
        # Disable solver log output
        model.setParam('OutputFlag', 0)
        
        # Set time limit
        model.setParam('TimeLimit', time_limit)
        
        # Disable dual reductions to distinguish INFEASIBLE vs UNBOUNDED
        # Without this, Gurobi may return STATUS_4 (INF_OR_UNBD) instead of clear INFEASIBLE
        model.setParam('DualReductions', 0)
        
        # Limit threads to avoid overheating CPU (use half of available cores)
        import os
        num_threads = max(1, os.cpu_count() // 2)
        model.setParam('Threads', num_threads)
        
        # Compute the scheduling horizon
        M = max(deadlines.values()) + max(durations.values())
        
        # ============================================================
        # Variables
        # ============================================================
        
        # S[i] = start time of job i
        S = model.addVars(range(1, n+1), vtype=GRB.INTEGER, name="S", lb=0, ub=M)
        
        # Lmax = maximum lateness
        Lmax = model.addVar(vtype=GRB.INTEGER, name="Lmax", lb=-GRB.INFINITY)
        
        # Binary variables for disjunctive constraints: y[i, j] = 1 if job i finishes before job j
        pairs = [(i, j) for i in range(1, n+1) for j in range(i+1, n+1)]
        y = model.addVars(pairs, vtype=GRB.BINARY, name="y")
        
        # ============================================================
        # Objective: Minimize Lmax
        # ============================================================
        model.setObjective(Lmax, GRB.MINIMIZE)
        
        # ============================================================
        # Constraints
        # ============================================================
        
        # C1: Time windows
        for i in range(1, n+1):
            model.addConstr(S[i] >= ready_dates[i], name=f"ready_{i}")
            model.addConstr(S[i] + durations[i] <= deadlines[i], name=f"deadline_{i}")
        
        # C2: Lmax definition
        for i in range(1, n+1):
            lateness = S[i] + durations[i] - due_dates[i]
            model.addConstr(Lmax >= lateness, name=f"lmax_{i}")
        
        # C3: Precedence constraints
        for i in range(1, n+1):
            for j in successors[i]:
                model.addConstr(
                    S[i] + durations[i] <= S[j],
                    name=f"prec_{i}_{j}"
                )
        
        # C4: Disjunctive constraints (no overlap)
        # For each pair of jobs (i, j), one of the following must hold:
        #   - Job i finishes before job j starts: S[i] + duration[i] <= S[j]
        #   - Job j finishes before job i starts: S[j] + duration[j] <= S[i]
        for (i, j) in pairs:
            # If y[i, j] = 1: job i is before job j
            model.addConstr(
                S[i] + durations[i] <= S[j] + M * (1 - y[i,j]),
                name=f"disj1_{i}_{j}"
            )
            # If y[i, j] = 0: job j is before job i
            model.addConstr(
                S[j] + durations[j] <= S[i] + M * y[i,j],
                name=f"disj2_{i}_{j}"
            )
        
        # ============================================================
        # Solve
        # ============================================================
        model.optimize()
        
        # ============================================================
        # Extract solution
        # ============================================================
        solve_time = model.Runtime
        
        # Case 1: Optimal solution found
        if model.status == GRB.OPTIMAL:
            schedule = {i: int(S[i].X) for i in range(1, n+1)}
            lmax = int(Lmax.X)
            return schedule, lmax, True, solve_time, 0.0
        
        # Case 2: Time limit reached
        elif model.status == GRB.TIME_LIMIT:
            if model.SolCount > 0:
                # At least one feasible solution was found, but it may be suboptimal
                schedule = {i: int(S[i].X) for i in range(1, n+1)}
                lmax = int(Lmax.X)
                gap = model.MIPGap * 100  # convert to percentage
                return schedule, lmax, True, solve_time, gap
            else:
                # Timeout occurred before any solution was found
                # Return a special status so the runner can detect TIMEOUT
                return None, "TIMEOUT", False, solve_time, None
        
        # Case 3: Infeasible
        elif model.status == GRB.INFEASIBLE:
            return None, "INFEASIBLE", False, solve_time, None
        
        # Case 4: Other statuses (unbounded, etc.)
        else:
            return None, f"STATUS_{model.status}", False, solve_time, None
        
    except gp.GurobiError as e:
        print(f"Gurobi Error: {e}")
        return None, None, False, 0, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None, False, 0, None


def solve_MIP(n, durations, ready_dates, due_dates, deadlines, successors, time_limit=300):
    """
    Wrapper function matching the SAT solver interface for easier integration.
    
    Returns:
        schedule: dict {job_id: start_time}
        lmax: maximum lateness
        is_sat: True if a feasible schedule is found
        solve_time: solve time
        gap: MIP gap (%)
    """
    return solve_with_gurobi(n, durations, ready_dates, due_dates, deadlines, successors, time_limit)
