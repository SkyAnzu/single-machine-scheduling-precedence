import argparse
import multiprocessing
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.project_paths import DATASET_SIZES, FILENAMES_DIR, INS_DIR, INSTANCE_TYPES
from Graph_in4.visualize_gsp import SCRIPT_DIR, _worker


OUTPUT_ROOT = SCRIPT_DIR / "graph_batch"


def load_filename_list(size: int, instance_type: str = None):
    if instance_type is not None:
        type_specific = FILENAMES_DIR / f"{size}-{instance_type}.txt"
        if type_specific.exists():
            filelist = type_specific
        else:
            filelist = FILENAMES_DIR / f"{size}.txt"
    else:
        filelist = FILENAMES_DIR / f"{size}.txt"
    if not filelist.exists():
        return None
    return [line.strip() for line in filelist.read_text(encoding="utf-8").splitlines() if line.strip()]


def instance_path(size: int, instance_type: str, filename: str) -> Path:
    return INS_DIR / f"wtrd_pred{size}" / instance_type / filename


def collect_tasks(selected_sizes, selected_types, limit_per_dataset=None):
    tasks = []

    for size in selected_sizes:
        for instance_type in selected_types:
            filenames = load_filename_list(size, instance_type)
            if filenames is None:
                print(f"[SKIP] size={size}, type={instance_type} - file list not found")
                continue

            dataset_name = f"{size}-{instance_type}"
            dataset_count = 0
            for filename in filenames:
                gsp_path = instance_path(size, instance_type, filename)
                if not gsp_path.exists():
                    print(f"  [MISS] {dataset_name}: {filename}")
                    continue

                tasks.append((gsp_path, INS_DIR, None, None, OUTPUT_ROOT))
                dataset_count += 1
                if limit_per_dataset is not None and dataset_count >= limit_per_dataset:
                    break

            print(f"[DATASET] {dataset_name}: {dataset_count} file(s)")

    unique_tasks = []
    seen = set()
    for gsp_path, input_root, _, _, output_root in tasks:
        key = str(gsp_path).lower()
        if key in seen:
            continue
        seen.add(key)
        unique_tasks.append((gsp_path, input_root, None, None, output_root))
    return unique_tasks


def main():
    parser = argparse.ArgumentParser(
        description="Visualize only the instances listed in Filenames/*.txt and save them under Graph_in4/graph_batch/."
    )
    parser.add_argument(
        "--sizes",
        nargs="+",
        type=int,
        choices=DATASET_SIZES,
        default=DATASET_SIZES,
        help="Dataset sizes to process (default: all available sizes).",
    )
    parser.add_argument(
        "--types",
        nargs="+",
        choices=INSTANCE_TYPES,
        default=INSTANCE_TYPES,
        help="Instance types to process (default: S L).",
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=max(1, multiprocessing.cpu_count() - 1),
        help="Parallel workers (default: CPU count - 1).",
    )
    parser.add_argument(
        "--limit-per-dataset",
        type=int,
        default=None,
        help="Only visualize the first N listed instances per dataset. Useful for smoke tests.",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Batch Visualizer - Filename Lists")
    print("=" * 70)
    print(f"Sizes    : {', '.join(str(size) for size in args.sizes)}")
    print(f"Types    : {', '.join(args.types)}")
    print(f"Output   : {OUTPUT_ROOT}")
    if args.limit_per_dataset is not None:
        print(f"Limit    : {args.limit_per_dataset} per dataset")
    print("=" * 70)

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    tasks = collect_tasks(args.sizes, args.types, limit_per_dataset=args.limit_per_dataset)
    if not tasks:
        print("No matching .GSP files found from Filenames lists.")
        return

    total = len(tasks)
    workers = min(max(1, args.workers), total)
    tasks = [
        (gsp_path, input_root, index, total, output_root)
        for index, (gsp_path, input_root, _, _, output_root) in enumerate(tasks, start=1)
    ]

    print(f"\nTotal files: {total}")
    print(f"Workers    : {workers}")

    if workers == 1:
        results = [_worker(task) for task in tasks]
    else:
        ctx = multiprocessing.get_context("spawn")
        with ctx.Pool(processes=workers) as pool:
            results = pool.map(_worker, tasks)

    success_count = sum(1 for result in results if result)
    print("\n" + "=" * 70)
    print(f"Done. Generated {success_count}/{total} graph image(s).")
    print("=" * 70)


if __name__ == "__main__":
    main()
