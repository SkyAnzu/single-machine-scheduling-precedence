"""
run_instances_05_025_125_50_1.py

Run the special benchmark family `XX_05_025_125_50_1.GSP`
for all supported solvers.

Outputs:
  - Solutions: `2016/solutions_{solver}/{n}-{type}/`
  - Excel: `2016/results_{solver}_05_025_125_50_1.xlsx`
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

from runner_common import (
    AVAILABLE_SOLVERS,
    DATASET_SIZES,
    DEFAULT_SOLVERS,
    INSTANCE_TYPES,
    OUTPUT_DIR,
    dataset_sheet,
    instance_path,
    load_single_sheet_results,
    parse_solution_file,
    run_single_instance,
    save_single_sheet_results,
)


TIMEOUT = 300
SUBPROCESS_GRACE = 20
SPECIAL_SUFFIX = "05_025_125_50_1.GSP"


def main(solvers=None, instance_types=None):
    selected_solvers = list(solvers or DEFAULT_SOLVERS)
    selected_types = list(instance_types or INSTANCE_TYPES)
    script_path = Path(__file__).resolve()
    total_instances = len(DATASET_SIZES) * len(selected_types)

    print("=" * 70)
    print("Special Runner - XX_05_025_125_50_1.GSP")
    print("=" * 70)
    print(f"Sizes    : {', '.join(str(size) for size in DATASET_SIZES)}")
    print(f"Types    : {', '.join(selected_types)}")
    print(f"Solvers  : {', '.join(selected_solvers)}")
    print(f"Timeout  : {TIMEOUT}s per instance")
    print("=" * 70)

    for solver in selected_solvers:
        print(f"\n{'#' * 70}")
        print(f"# SOLVER: {solver.upper()}")
        print(f"{'#' * 70}\n")

        excel_file = OUTPUT_DIR / f"results_{solver}_05_025_125_50_1.xlsx"
        try:
            results = load_single_sheet_results(excel_file)
        except Exception as exc:
            print(f"    [WARNING] Could not read Excel file: {exc}")
            results = []

        completed = {row["instance"] for row in results} if results else set()
        if completed:
            print(f"    [RESUME] Found {len(completed)} completed instances")

        position = 0
        for size in DATASET_SIZES:
            filename = f"{size}_{SPECIAL_SUFFIX}"
            for instance_type in selected_types:
                position += 1
                key = dataset_sheet(size, instance_type)
                dataset_file = instance_path(size, instance_type, filename)
                solution_file = OUTPUT_DIR / f"solutions_{solver}" / key / f"{size}_{SPECIAL_SUFFIX}.txt"

                if key in completed:
                    print(f"  [{position}/{total_instances}] {key}/{filename} - SKIP (already completed)")
                    continue

                if not dataset_file.exists():
                    print(f"  [{position}/{total_instances}] {key}/{filename} - FILE NOT FOUND")
                    results.append({
                        "solver": solver,
                        "instance": key,
                        "n": size,
                        "type": instance_type,
                        "file": filename,
                        "Lmax": "-",
                        "status": "FILE_NOT_FOUND",
                        "time_s": 0,
                        "gap_%": None,
                    })
                    save_single_sheet_results(excel_file, results)
                    continue

                print(f"  [{position}/{total_instances}] {key}/{filename} ... ", end="", flush=True)

                process = subprocess.Popen(
                    [
                        sys.executable,
                        str(script_path),
                        "--single",
                        str(dataset_file),
                        str(solution_file),
                        solver,
                        str(TIMEOUT),
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                started_at = time.time()
                status = "FINISHED"
                try:
                    process.wait(timeout=TIMEOUT)
                    elapsed = time.time() - started_at
                except subprocess.TimeoutExpired:
                    status = "TIMEOUT"
                    elapsed = float(TIMEOUT)
                    try:
                        process.wait(timeout=SUBPROCESS_GRACE)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()

                time.sleep(0.1)
                parsed = parse_solution_file(solution_file, solver, status)
                if len(parsed) == 4:
                    lmax, status, gap, _ = parsed
                else:
                    lmax, status, gap = parsed

                if status == "TIMEOUT":
                    elapsed = float(TIMEOUT)

                gap_text = f"gap={gap:.2f}% | " if gap is not None else ""
                print(f"{status} | Lmax={lmax} | {gap_text}{elapsed:.2f}s")

                results.append({
                    "solver": solver,
                    "instance": key,
                    "n": size,
                    "type": instance_type,
                    "file": filename,
                    "Lmax": lmax,
                    "status": status,
                    "time_s": round(elapsed, 2),
                    "gap_%": round(gap, 2) if gap is not None else None,
                })
                save_single_sheet_results(excel_file, results)

        print(f"\n    -> Results saved: {excel_file}")
        print(f"       Total records: {len(results)}")

    print("\n" + "=" * 70)
    print("All done!")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) == 6 and sys.argv[1] == "--single":
        _, _, dataset_file, solution_file, solver, timeout = sys.argv
        run_single_instance(Path(dataset_file), Path(solution_file), solver, int(timeout))
    else:
        parser = argparse.ArgumentParser(
            description="Run the XX_05_025_125_50_1.GSP benchmark family",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python Test/run_instances_05_025_125_50_1.py
  python Test/run_instances_05_025_125_50_1.py --types S
  python Test/run_instances_05_025_125_50_1.py --types S L --solvers basicsat gurobi
            """,
        )

        parser.add_argument(
            "--solvers",
            nargs="+",
            choices=AVAILABLE_SOLVERS,
            default=None,
            help=f"Solvers to run (default: {', '.join(DEFAULT_SOLVERS)})",
        )
        parser.add_argument(
            "--types",
            nargs="+",
            choices=INSTANCE_TYPES,
            default=None,
            help="Instance types to run (default: S L)",
        )

        args = parser.parse_args()
        main(solvers=args.solvers, instance_types=args.types)
