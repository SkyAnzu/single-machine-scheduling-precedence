import argparse
import tempfile
import time
from pathlib import Path

from runner_common import AVAILABLE_SOLVERS, parse_solution_file, run_single_instance


def main():
    parser = argparse.ArgumentParser(
        description="Run one instance without writing persistent solution or Excel outputs."
    )
    parser.add_argument("instance", help="Path to the .GSP instance file")
    parser.add_argument(
        "--solver",
        required=True,
        choices=AVAILABLE_SOLVERS,
        help="Solver to run",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Per-instance timeout in seconds (default: 300)",
    )

    args = parser.parse_args()
    instance_path = Path(args.instance).resolve()

    if not instance_path.exists():
        raise FileNotFoundError(f"Instance file not found: {instance_path}")

    with tempfile.TemporaryDirectory(prefix="smsp_run_") as temp_dir:
        temp_solution = Path(temp_dir) / f"{instance_path.name}.txt"

        started_at = time.time()
        run_single_instance(instance_path, temp_solution, args.solver, args.timeout)
        elapsed = time.time() - started_at

        lmax, status, gap = parse_solution_file(temp_solution, args.solver, "FINISHED")

    print("=" * 70)
    print("Single Instance Run")
    print("=" * 70)
    print(f"Instance : {instance_path}")
    print(f"Solver   : {args.solver}")
    print(f"Timeout  : {args.timeout}s")
    print(f"Status   : {status}")
    print(f"Lmax     : {lmax}")
    if gap is not None:
        print(f"Gap      : {gap:.2f}%")
    print(f"Time     : {elapsed:.2f}s")
    print("Output   : no persistent solution or Excel file written")
    print("=" * 70)


if __name__ == "__main__":
    main()
