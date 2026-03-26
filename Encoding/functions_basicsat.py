"""
functions_basicsat.py

Basic SAT encoding for Single Machine Scheduling.

Key differences from seqcounter:
- Uses PySAT CardEnc instead of a manual sequential counter
- Does not use the dual-purpose L variable used in seqcounter
- Uses only two variable families: S (start) and A (active)
- Includes window-tightening preprocessing for performance
- Uses incremental optimization by forbidding start times that violate the current UB
"""

from pysat.formula import CNF
from pysat.solvers import Solver
from pysat.card import CardEnc, EncType
import signal
import time
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.dataset import read_dataset
from common.schedule_utils import compute_max_lateness, window_tightening


class TimeoutError(Exception):
    """Exception raised when solver times out"""
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("Solver timeout")


# ============================================================
# Basic SAT Encoding
# ============================================================

def solve_SAT(n, durations, ready_dates, due_dates, deadlines, successors, verbose=False):
    """
    Basic SAT encoding to find a feasible solution.
    
    Variables:
    - S[i,t]: job i starts at time t
    - A[i,t]: job i is active at time t
    
    Returns:
        cnf: CNF formula
        schedule: dict {job: start_time}
        valid_starts: dict {job: list of valid start times}
        S: dict {(job, time): var_id}
        initial_Lmax: maximum lateness of initial solution
        is_sat: True if a solution exists
    """
    
    jobs = list(range(1, n+1))
    T_max = max(deadlines.values())
    
    cnf = CNF()
    var_counter = 1
    
    # Dictionaries
    S = {}  # S[i,t]: job i starts at time t
    A = {}  # A[i,t]: job i is active at time t
    valid_starts = {}
    
    # ============================================================
    # 1) CREATE S and A variables
    # ============================================================
    for i in jobs:
        last_start = deadlines[i] - durations[i]
        if last_start < ready_dates[i]:
            if verbose:
                print(f"Job {i} impossible: last_start < ready")
            return None, None, None, None, None, False
        
        valid_starts[i] = list(range(ready_dates[i], last_start + 1))
        for t in valid_starts[i]:
            S[(i,t)] = var_counter
            var_counter += 1
    
    for i in jobs:
        for t in range(ready_dates[i], deadlines[i]):
            A[(i,t)] = var_counter
            var_counter += 1
    
    if verbose:
        print(f"Created {len(S)} S variables, {len(A)} A variables")
    
    # ============================================================
    # 2) S -> A: If job starts at t, it's active in [t, t+duration)
    # ============================================================
    for i in jobs:
        for t0 in valid_starts[i]:
            s_lit = S[(i,t0)]
            for t in range(t0, t0 + durations[i]):
                if (i,t) in A:
                    cnf.append([-s_lit, A[(i,t)]])
    
    # ============================================================
    # 3) Single Machine: At most 1 job active at each time (CardEnc)
    # ============================================================
    for t in range(T_max):
        active_vars = [A[(i,t)] for i in jobs if (i,t) in A]
        if len(active_vars) > 1:
            enc = CardEnc.atmost(lits=active_vars, bound=1,
                                encoding=EncType.seqcounter,
                                top_id=var_counter-1)
            cnf.extend(enc.clauses)
            var_counter = enc.nv + 1
    
    # ============================================================
    # 4) Each Job Once: Each job starts exactly once (CardEnc)
    # ============================================================
    for i in jobs:
        start_vars = [S[(i,t)] for t in valid_starts[i]]
        if start_vars:
            enc = CardEnc.equals(lits=start_vars, bound=1,
                                encoding=EncType.seqcounter,
                                top_id=var_counter-1)
            cnf.extend(enc.clauses)
            var_counter = enc.nv + 1
    
    # ============================================================
    # 5) Precedence: Job i must finish before job j starts
    # ============================================================
    for i in jobs:
        for j in successors[i]:
            if j > n:
                continue
            for t_i in valid_starts[i]:
                for t_j in valid_starts[j]:
                    if t_i + durations[i] > t_j:
                        # Cannot have both S[i,t_i] and S[j,t_j]
                        cnf.append([-S[(i,t_i)], -S[(j,t_j)]])
    
    if verbose:
        print(f"Total clauses: {len(cnf.clauses)}")
    
    # ============================================================
    # 6) Solve to find feasible solution
    # ============================================================
    solver = Solver(name='g4', bootstrap_with=cnf)
    
    if not solver.solve():
        solver.delete()
        return None, None, None, None, None, False
    
    model = solver.get_model()
    solver.delete()
    
    # Extract schedule from S variables
    schedule = {}
    for (i, t), var_id in S.items():
        if model[var_id - 1] > 0:  # S[i,t] = true
            schedule[i] = t
    
    # Compute initial Lmax
    initial_Lmax = compute_UB_Lmax(schedule, durations, due_dates)
    
    return cnf, schedule, valid_starts, S, initial_Lmax, True


# ============================================================
# Upper Bound Computation
# ============================================================

def compute_UB_Lmax(schedule, durations, due_dates):
    """Compute Lmax from a schedule."""
    return compute_max_lateness(schedule, durations, due_dates, clamp_zero=False)


# ============================================================
# Incremental Optimization
# ============================================================

def incremental_SAT_Lmax(durations, due_dates, S_dict, placeholder, cnf, UB, sol_file, valid_starts, timeout=600, verbose=False):
    """
    Incremental optimization - based on reference implementation.
    
    Strategy: 
    - For each iteration with current UB:
      - Forbid all S[i,t] where lateness(i,t) >= UB
      - Solve SAT
      - If SAT: compute actual Lmax from solution, use as new UB
      - If UNSAT: done (cannot improve further)
    """
    
    start_time = time.time()
    solver = Solver(name='g4', bootstrap_with=cnf)
    iteration_count = 0
    var_to_S = {v: (i, t) for (i, t), v in S_dict.items()}
    best_schedule = {}
    best_Lmax = UB  # Track best Lmax found
    
    if verbose:
        print("\n=== SOLVING INCREMENTAL SAT ===")
    
    while UB > 0:
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed >= timeout:
            if verbose:
                print(f"Timeout after {elapsed:.1f}s at iteration {iteration_count}")
            break
        
        iteration_count += 1
        if verbose:
            print(f"\n==============================")
            print(f"Iteration {iteration_count}: Trying UB = {UB}")
        
        # Add constraint: forbid S[i,t] that would cause lateness >= UB
        # lateness(i,t) = (t + duration[i]) - due_date[i]
        # If lateness(i,t) >= UB, forbid S[i,t]
        for (i, t), var in S_dict.items():
            lateness = t + durations[i] - due_dates[i]
            if lateness >= UB:
                solver.add_clause([-var])
        
        # Try to solve with remaining time budget
        if solver.solve():
            if verbose:
                print("SAT - found solution")
            
            model = solver.get_model()
            best_schedule = {}
            Lmax = 0
            
            # Extract schedule from model
            for var_id in range(1, len(S_dict) + 1):
                if var_id <= len(model) and model[var_id - 1] > 0:
                    if var_id in var_to_S:
                        i, t = var_to_S[var_id]
                        lateness = t + durations[i] - due_dates[i]
                        Lmax = max(Lmax, lateness)
                        best_schedule[i] = t
            
            if verbose:
                print(f"New Lmax: {Lmax}")
                if UB == Lmax:
                    print("Warning: UB not decreasing")
            
            # Update UB to actual Lmax found
            UB = Lmax
            best_Lmax = Lmax
            
            # Write intermediate solution
            with open(sol_file, "w", encoding="utf-8") as f:
                elapsed = time.time() - start_time
                f.write(f"Lmax = {UB}\n")
                f.write(f"Solve Time = {elapsed:.2f}s\n")
                f.write("Schedule:\n")
                for i, start in sorted(best_schedule.items(), key=lambda x: x[1]):
                    f.write(f"  Job {i}: start = {start}, end = {start + durations[i]}\n")
                f.flush()
        else:
            if verbose:
                print("UNSAT - cannot improve further")
            break
    
    solver.delete()
    
    # Write final solution (in case timeout was hit)
    if best_schedule:
        elapsed = time.time() - start_time
        with open(sol_file, "w", encoding="utf-8") as f:
            f.write(f"Lmax = {best_Lmax}\n")
            f.write(f"Solve Time = {elapsed:.2f}s\n")
            f.write("Schedule:\n")
            for i, start in sorted(best_schedule.items(), key=lambda x: x[1]):
                f.write(f"  Job {i}: start = {start}, end = {start + durations[i]}\n")
            f.flush()
    
    if verbose:
        print(f"\nIncremental SAT finished.")
        print(f"Best Lmax found: {best_Lmax}")
    
    solve_time = time.time() - start_time
    return best_Lmax, best_schedule, solve_time
