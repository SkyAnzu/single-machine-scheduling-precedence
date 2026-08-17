import sys
import re
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    pd = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.project_paths import (
    AVAILABLE_SOLVERS,
    DATASET_SIZES,
    DEFAULT_SOLVERS,
    FILENAMES_DIR,
    INS_DIR,
    INSTANCE_TYPES,
    OUTPUT_DIR,
    configure_runtime_environment,
)
from common.schedule_utils import compute_job_lateness, format_solution_text

configure_runtime_environment()


DIRECT_OPTIMIZATION_SOLVERS = {"gurobi", "cpsat", "cplex_cp", "cplex_mp"}


def dataset_sheet(size: int, instance_type: str) -> str:
    return f"{size}-{instance_type}"


def build_sheet_names(instance_types=None):
    selected_types = list(instance_types or INSTANCE_TYPES)
    return [dataset_sheet(size, instance_type) for size in DATASET_SIZES for instance_type in selected_types]


def filenames_path(size: int, instance_type: str = None) -> Path:
    if instance_type is not None:
        type_specific = FILENAMES_DIR / f"{size}-{instance_type}.txt"
        if type_specific.exists():
            return type_specific
    return FILENAMES_DIR / f"{size}.txt"


def load_filename_list(size: int, instance_type: str = None):
    filelist = filenames_path(size, instance_type)
    if not filelist.exists():
        return None
    return [line.strip() for line in filelist.read_text(encoding="utf-8").splitlines() if line.strip()]


def instance_path(size: int, instance_type: str, filename: str) -> Path:
    return INS_DIR / f"wtrd_pred{size}" / instance_type / filename


def load_results_from_excel(excel_file: Path, sheet_names):
    if pd is None:
        raise ImportError("pandas is required to read Excel result workbooks")

    all_results = {sheet_name: [] for sheet_name in sheet_names}
    if not excel_file.exists():
        return all_results

    with pd.ExcelFile(excel_file) as workbook:
        for sheet_name in workbook.sheet_names:
            if sheet_name in all_results:
                df = pd.read_excel(workbook, sheet_name=sheet_name)
                all_results[sheet_name] = df.to_dict("records")

    return all_results


def save_results_to_excel(excel_file: Path, all_results, sheet_names):
    if pd is None:
        raise ImportError("pandas is required to write Excel result workbooks")

    excel_file.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        for sheet_name in sheet_names:
            rows = all_results.get(sheet_name, [])
            if rows:
                pd.DataFrame(rows).to_excel(writer, sheet_name=sheet_name, index=False)


def load_single_sheet_results(excel_file: Path):
    if pd is None:
        raise ImportError("pandas is required to read Excel result workbooks")

    if not excel_file.exists():
        return []

    workbook = pd.ExcelFile(excel_file)
    if not workbook.sheet_names:
        return []

    return pd.read_excel(workbook, sheet_name=workbook.sheet_names[0]).to_dict("records")


def save_single_sheet_results(excel_file: Path, rows, sheet_name="instances"):
    if pd is None:
        raise ImportError("pandas is required to write Excel result workbooks")

    excel_file.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, sheet_name=sheet_name, index=False)


def run_single_instance(instance_file: Path, solution_file: Path, solver: str, timeout: int, verbose: bool = False):
    solution_file.parent.mkdir(parents=True, exist_ok=True)
    sat_solver_name = "g421"
    supports_backend_override = False

    if solver in DIRECT_OPTIMIZATION_SOLVERS:
        if solver == "gurobi":
            from functions_gurobi import read_dataset, solve_MIP, window_tightening
        elif solver == "cpsat":
            from functions_cpsat import read_dataset, solve_MIP, window_tightening
        elif solver == "cplex_cp":
            from functions_cplex_cp import read_dataset, solve_MIP, window_tightening
        else:
            from functions_cplex_mp import read_dataset, solve_MIP, window_tightening

        n, durations, ready_dates, due_dates, deadlines, successors = read_dataset(instance_file)
        new_ready_dates, new_deadlines = window_tightening(n, ready_dates, durations, deadlines, successors)

        schedule, lmax, is_sat, solve_time, gap = solve_MIP(
            n,
            durations,
            new_ready_dates,
            due_dates,
            new_deadlines,
            successors,
            time_limit=timeout,
        )

        if verbose:
            print("Direct optimization solver selected: no CNF clause statistics available.")

        if is_sat == "TIME_LIMIT_FEASIBLE":
            solution_file.write_text(
                "TIME_LIMIT_FEASIBLE\n"
                + format_solution_text(schedule, durations, due_dates, lmax, solve_time=solve_time, gap=gap),
                encoding="utf-8",
            )
            return lmax, "TIMEOUT", gap

        if not is_sat:
            status_msg = lmax if isinstance(lmax, str) else "UNSAT"
            solution_file.write_text(f"{status_msg}\n", encoding="utf-8")
            return "-", status_msg, None

        solution_file.write_text(
            format_solution_text(schedule, durations, due_dates, lmax, solve_time=solve_time, gap=gap),
            encoding="utf-8",
        )

        return lmax, "FINISHED", gap

    if solver == "pbenc":
        from functions_pbenc import compute_UB_Lmax, incremental_SAT_Lmax, read_dataset, solve_SAT, window_tightening
    elif solver == "basicsat":
        from functions_basicsat import compute_UB_Lmax, incremental_SAT_Lmax, read_dataset, solve_SAT, window_tightening
    elif solver == "seqcardenc":
        from functions_seqcardenc import compute_UB_Lmax, incremental_SAT_Lmax, read_dataset, solve_SAT, window_tightening
    elif solver == "seqcardenc_ver2":
        from functions_seqcardenc_ver2 import compute_UB_Lmax, incremental_SAT_Lmax, read_dataset, solve_SAT, window_tightening
    elif solver == "seqcardenc_ver2e":
        from functions_seqcardenc_ver2e import compute_UB_Lmax, incremental_SAT_Lmax, read_dataset, solve_SAT, window_tightening
    elif solver == "seqcardenc_ver3":
        from functions_seqcardenc_ver3 import compute_UB_Lmax, incremental_SAT_Lmax, read_dataset, solve_SAT, window_tightening
    elif solver == "seqcardenc_ver5":
        from functions_seqcardenc_ver5 import compute_UB_Lmax, incremental_SAT_Lmax, read_dataset, solve_SAT, window_tightening
        supports_backend_override = True
    elif solver == "seqcardenc_ver5_cadical300":
        from functions_seqcardenc_ver5 import compute_UB_Lmax, incremental_SAT_Lmax, read_dataset, solve_SAT, window_tightening
        sat_solver_name = "cadical300"
        supports_backend_override = True
    elif solver == "seqcardenc_ver5e":
        from functions_seqcardenc_ver5e import compute_UB_Lmax, incremental_SAT_Lmax, read_dataset, solve_SAT, window_tightening
        supports_backend_override = True
    elif solver == "seqcardenc_ver5e_cadical300":
        from functions_seqcardenc_ver5e import compute_UB_Lmax, incremental_SAT_Lmax, read_dataset, solve_SAT, window_tightening
        sat_solver_name = "cadical300"
        supports_backend_override = True
    elif solver == "seqcardenc_ver5e_1":
        from functions_seqcardenc_ver5e_1 import compute_UB_Lmax, incremental_SAT_Lmax, read_dataset, solve_SAT, window_tightening
        supports_backend_override = True
    elif solver == "seqcardenc_ver5e_1_cadical300":
        from functions_seqcardenc_ver5e_1 import compute_UB_Lmax, incremental_SAT_Lmax, read_dataset, solve_SAT, window_tightening
        sat_solver_name = "cadical300"
        supports_backend_override = True
    elif solver == "seqcardenc_ver4_1":
        from functions_seqcardenc_ver4_1 import compute_UB_Lmax, incremental_SAT_Lmax, read_dataset, solve_SAT, window_tightening
    elif solver == "seqcardenc_ver4_2":
        from functions_seqcardenc_ver4_2 import compute_UB_Lmax, incremental_SAT_Lmax, read_dataset, solve_SAT, window_tightening
    elif solver == "seqcardenc_ver4_3":
        from functions_seqcardenc_ver4_3 import compute_UB_Lmax, incremental_SAT_Lmax, read_dataset, solve_SAT, window_tightening
    else:
        from functions_seqcounter import compute_UB_Lmax, incremental_SAT_Lmax, read_dataset, solve_SAT, window_tightening

    n, durations, ready_dates, due_dates, deadlines, successors = read_dataset(instance_file)
    new_ready_dates, new_deadlines = window_tightening(n, ready_dates, durations, deadlines, successors)

    if solver == "basicsat":
        cnf, schedule, valid_starts, s_vars, initial_lmax, is_sat = solve_SAT(
            n,
            durations,
            new_ready_dates,
            due_dates,
            new_deadlines,
            successors,
            verbose=verbose,
        )
    elif supports_backend_override:
        cnf, schedule, valid_starts, s_vars, l_vars, is_sat = solve_SAT(
            n,
            durations,
            new_ready_dates,
            new_deadlines,
            successors,
            verbose=verbose,
            sat_solver_name=sat_solver_name,
        )
    else:
        cnf, schedule, valid_starts, s_vars, l_vars, is_sat = solve_SAT(
            n,
            durations,
            new_ready_dates,
            new_deadlines,
            successors,
            verbose=verbose,
        )

    if not is_sat:
        solution_file.write_text("UNSAT\n", encoding="utf-8")
        return "-", "UNSAT", None

    upper_bound = compute_UB_Lmax(schedule, durations, due_dates)
    solution_file.write_text(
        format_solution_text(schedule, durations, due_dates, upper_bound),
        encoding="utf-8",
    )

    if solver == "basicsat":
        incremental_SAT_Lmax(
            durations,
            due_dates,
            s_vars,
            initial_lmax,
            cnf,
            upper_bound,
            str(solution_file),
            valid_starts,
            timeout=timeout,
            verbose=verbose,
        )
    elif supports_backend_override:
        incremental_SAT_Lmax(
            durations,
            due_dates,
            s_vars,
            l_vars,
            cnf,
            upper_bound,
            str(solution_file),
            valid_starts,
            verbose=verbose,
            sat_solver_name=sat_solver_name,
        )
    else:
        incremental_SAT_Lmax(
            durations,
            due_dates,
            s_vars,
            l_vars,
            cnf,
            upper_bound,
            str(solution_file),
            valid_starts,
            verbose=verbose,
        )

    try:
        first_line = solution_file.read_text(encoding="utf-8").splitlines()[0]
        match = re.search(r"Lmax\s*=\s*(-?\d+)", first_line)
        lmax = int(match.group(1)) if match else upper_bound
    except Exception:
        lmax = upper_bound

    return lmax, "FINISHED", None


def parse_solution_file(solution_file: Path, solver: str, default_status: str):
    if not solution_file.exists():
        return "-", "ERROR" if default_status == "FINISHED" else default_status, None, {}

    try:
        lines = solution_file.read_text(encoding="utf-8").splitlines()
        if not lines:
            return "-", "ERROR" if default_status == "FINISHED" else default_status, None, {}

        # Parse STATS line (appended at end of file by SAT solvers)
        sat_stats = {}
        for line in lines:
            if line.strip().startswith("STATS"):
                for token in line.strip().split()[1:]:
                    if "=" in token:
                        k, v = token.split("=", 1)
                        try:
                            sat_stats[k] = int(v)
                        except ValueError:
                            sat_stats[k] = v

        first_line = lines[0].strip()
        if first_line.startswith("Lmax"):
            match = re.search(r"Lmax\s*=\s*(-?\d+)", first_line)
            if not match:
                return "-", "ERROR" if default_status == "FINISHED" else default_status, None, sat_stats
            lmax = int(match.group(1))
            gap = None
            if solver in DIRECT_OPTIMIZATION_SOLVERS and len(lines) > 1:
                second_line = lines[1].strip()
                if second_line.startswith("MIP Gap"):
                    gap = float(second_line.split("=", 1)[1].strip().rstrip("%"))
            return lmax, default_status, gap, sat_stats

        if first_line == "UNSAT":
            return "-", "UNSAT", None, sat_stats
        if first_line == "TIMEOUT":
            return "-", "TIMEOUT", None, sat_stats
        if first_line == "TIME_LIMIT_FEASIBLE":
            lmax = None
            gap = None
            for line in lines[1:]:
                stripped = line.strip()
                lmax_match = re.search(r"Lmax\s*=\s*(-?\d+)", stripped)
                if lmax_match and lmax is None:
                    lmax = int(lmax_match.group(1))
                if stripped.startswith("MIP Gap") and gap is None:
                    gap = float(stripped.split("=", 1)[1].strip().rstrip("%"))
            return "-" if lmax is None else lmax, "TIMEOUT", gap, sat_stats
        if first_line == "INFEASIBLE":
            return "-", "INFEASIBLE", None, sat_stats
        if first_line.startswith("STATUS_"):
            return "-", first_line, None, sat_stats
    except Exception:
        return "-", "ERROR" if default_status == "FINISHED" else default_status, None, {}

    return "-", "ERROR" if default_status == "FINISHED" else default_status, None, {}
