"""
run_batch_dataset_2010.py

Run batch experiments on Dataset_2010 lane.

Mapping:
  - `Dataset_2010/Filenames/20.txt` -> `Dataset_2010/Ins/wtrd_pred20/{S|L}/<filename>`
  - `Dataset_2010/Filenames/40.txt` -> `Dataset_2010/Ins/wtrd_pred40/{S|L}/<filename>`
  - `Dataset_2010/Filenames/50.txt` -> `Dataset_2010/Ins/wtrd_pred50/{S|L}/<filename>`

Outputs:
  - Solutions: `Dataset_2010/solutions_{solver}/{n}-{type}/`
  - Excel: `Dataset_2010/results_{solver}.xlsx`
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

from runner_common import (
    AVAILABLE_SOLVERS,
    DEFAULT_SOLVERS,
    INSTANCE_TYPES,
    load_results_from_excel,
    parse_solution_file,
    run_single_instance,
    save_results_to_excel,
)


TIMEOUT = 60
SUBPROCESS_GRACE = 20
DEFAULT_SIZES = [20, 40, 50]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_ROOT = PROJECT_ROOT / "Dataset_2010"
FILENAMES_DIR = DATASET_ROOT / "Filenames"
INS_DIR = DATASET_ROOT / "Ins"
OUTPUT_DIR = DATASET_ROOT


def dataset_sheet(size: int, instance_type: str) -> str:
    return f"{size}-{instance_type}"


def build_sheet_names(sizes, instance_types):
    return [dataset_sheet(size, instance_type) for size in sizes for instance_type in instance_types]


def filenames_path(size: int) -> Path:
    return FILENAMES_DIR / f"{size}.txt"


def load_filename_list(size: int):
    filelist = filenames_path(size)
    if not filelist.exists():
        return None
    return [line.strip() for line in filelist.read_text(encoding="utf-8").splitlines() if line.strip()]


def instance_path(size: int, instance_type: str, filename: str) -> Path:
    return INS_DIR / f"wtrd_pred{size}" / instance_type / filename


def main(solvers=None, instance_types=None, sizes=None, timeout=TIMEOUT):
    selected_solvers = list(solvers or DEFAULT_SOLVERS)
    selected_types = list(instance_types or INSTANCE_TYPES)
    selected_sizes = list(sizes or DEFAULT_SIZES)
    sheets = build_sheet_names(selected_sizes, selected_types)

    print("=" * 70)
    print("Batch Runner - Dataset_2010 Lane")
    print("=" * 70)
    print(f"Dataset  : {DATASET_ROOT}")
    print(f"Sizes    : {', '.join(str(size) for size in selected_sizes)}")
    print(f"Types    : {', '.join(selected_types)}")
    print(f"Solvers  : {', '.join(selected_solvers)}")
    print(f"Timeout  : {timeout}s per instance")
    print("=" * 70)

    script_path = Path(__file__).resolve()

    for solver in selected_solvers:
        print(f"\n{'#' * 70}")
        print(f"# SOLVER: {solver.upper()}")
        print(f"{'#' * 70}\n")

        excel_file = OUTPUT_DIR / f"results_{solver}.xlsx"
        all_results = {sheet: [] for sheet in sheets}
        if excel_file.exists():
            print(f"    [RESUME] Loading existing results from {excel_file.name}")
            try:
                all_results = load_results_from_excel(excel_file, sheets)
                for sheet in sheets:
                    if all_results[sheet]:
                        print(f"      - Sheet '{sheet}': {len(all_results[sheet])} records")
            except Exception as exc:
                print(f"    [WARNING] Could not read Excel file: {exc}")

        for size in selected_sizes:
            instances = load_filename_list(size)
            if instances is None:
                print(f"[SKIP] size={size} - file list not found at {filenames_path(size)}")
                continue

            for instance_type in selected_types:
                sheet = dataset_sheet(size, instance_type)
                print(f"\n>>> Dataset: {sheet} - {len(instances)} instances")

                solution_dir = OUTPUT_DIR / f"solutions_{solver}" / sheet
                completed = {row["filename"] for row in all_results[sheet]} if all_results[sheet] else set()
                if completed:
                    print(f"    [RESUME] Found {len(completed)} completed instances")

                for index, filename in enumerate(instances, 1):
                    dataset_file = instance_path(size, instance_type, filename)
                    solution_file = solution_dir / f"{filename}.txt"

                    if filename in completed:
                        print(f"  [{index}/{len(instances)}] {filename} - SKIP (already completed)")
                        continue

                    if not dataset_file.exists():
                        print(f"  [{index}/{len(instances)}] {filename} - FILE NOT FOUND")
                        all_results[sheet].append(
                            {
                                "solver": solver,
                                "dataset": sheet,
                                "filename": filename,
                                "n": size,
                                "type": instance_type,
                                "Lmax": "-",
                                "status": "FILE_NOT_FOUND",
                                "time_s": 0,
                                "gap_%": None,
                            }
                        )
                        save_results_to_excel(excel_file, all_results, sheets)
                        continue

                    print(f"  [{index}/{len(instances)}] {filename} ... ", end="", flush=True)

                    process = subprocess.Popen(
                        [
                            sys.executable,
                            str(script_path),
                            "--single",
                            str(dataset_file),
                            str(solution_file),
                            solver,
                            str(timeout),
                        ],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )

                    started_at = time.time()
                    status = "FINISHED"
                    try:
                        process.wait(timeout=timeout)
                        elapsed = time.time() - started_at
                    except subprocess.TimeoutExpired:
                        status = "TIMEOUT"
                        elapsed = float(timeout)
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
                        elapsed = float(timeout)

                    gap_text = f"gap={gap:.2f}% | " if gap is not None else ""
                    print(f"{status} | Lmax={lmax} | {gap_text}{elapsed:.2f}s")

                    all_results[sheet].append(
                        {
                            "solver": solver,
                            "dataset": sheet,
                            "filename": filename,
                            "n": size,
                            "type": instance_type,
                            "Lmax": lmax,
                            "status": status,
                            "time_s": round(elapsed, 2),
                            "gap_%": round(gap, 2) if gap is not None else None,
                        }
                    )
                    save_results_to_excel(excel_file, all_results, sheets)

        print(f"\n    -> Results saved: {excel_file}")
        total_records = sum(len(all_results[sheet]) for sheet in sheets)
        print(f"       Total records: {total_records}")

    print("\n" + "=" * 70)
    print("All done!")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) == 6 and sys.argv[1] == "--single":
        _, _, dataset_file, solution_file, solver, timeout = sys.argv
        run_single_instance(Path(dataset_file), Path(solution_file), solver, int(timeout))
    else:
        parser = argparse.ArgumentParser(
            description="Run batch experiments on Dataset_2010 lane",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python Test/run_batch_dataset_2010.py
  python Test/run_batch_dataset_2010.py --types S
  python Test/run_batch_dataset_2010.py --types S --solvers seqcardenc_ver2
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
            default=["S"],
            help="Instance types to run (default: S)",
        )
        parser.add_argument(
            "--sizes",
            nargs="+",
            type=int,
            default=DEFAULT_SIZES,
            help="Instance sizes to run (default: 20 40 50)",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=TIMEOUT,
            help=f"Per-instance timeout in seconds (default: {TIMEOUT})",
        )

        args = parser.parse_args()
        main(solvers=args.solvers, instance_types=args.types, sizes=args.sizes, timeout=args.timeout)
