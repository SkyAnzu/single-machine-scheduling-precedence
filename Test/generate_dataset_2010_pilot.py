"""
Generate Liu-2010-style datasets in repository .GSP format.

Output layout:
  Dataset_2010/
    Ins/wtrd_pred{n}/S/*.GSP
    Filenames/{n}.txt

Pilot scope (default):
  - n in {20, 40, 50}
  - 8 instances per n (24 total)
  - release-date spread Rmax in {25, 50}
  - due-date divisor k in {5, 10}
  - precedence density D in {0.2, 0.6}
  - deadline generation follows 2016-style formula:
      deadline_i ~ U[d_i, d_i + phi * P],  P = sum(p_i)
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_ROOT = PROJECT_ROOT / "Dataset_2010"
INS_ROOT = DATASET_ROOT / "Ins"
FILENAMES_ROOT = DATASET_ROOT / "Filenames"


@dataclass(frozen=True)
class InstanceConfig:
    n: int
    rmax: int
    due_divisor: int
    density: float
    phi: float
    rep: int


def precedence_probability(target_density: float, distance_minus_one: int) -> float:
    """
    Liu-2010 uses Hall-Posner style probability to better control edge density.

    P_ij = D * (1-D)^(j-i-1) / (1 - D * (1 - (1-D)^(j-i-1)))
    """

    if target_density <= 0.0:
        return 0.0
    if target_density >= 1.0:
        return 1.0

    numerator = target_density * ((1.0 - target_density) ** distance_minus_one)
    denominator = 1.0 - target_density * (1.0 - ((1.0 - target_density) ** distance_minus_one))
    if denominator <= 0.0:
        return 1.0
    value = numerator / denominator
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def build_instance(config: InstanceConfig, rng: random.Random):
    n = config.n

    weights = [1] * n
    durations = [rng.randint(1, 50) for _ in range(n)]

    ready_dates = [0] * n
    for index in range(1, n):
        ready_dates[index] = ready_dates[index - 1] + rng.randint(1, config.rmax)

    max_due_offset = max(1, (50 * n) // config.due_divisor)
    due_dates = [
        ready_dates[index] + durations[index] + rng.randint(1, max_due_offset)
        for index in range(n)
    ]

    total_processing = sum(durations)
    deadline_extension = max(1, int(round(config.phi * total_processing)))
    deadlines = [
        rng.randint(due_dates[index], due_dates[index] + deadline_extension)
        for index in range(n)
    ]

    successors = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            distance_minus_one = j - i - 1
            probability = precedence_probability(config.density, distance_minus_one)
            if rng.random() < probability:
                successors[i].append(j + 1)

    return weights, durations, due_dates, ready_dates, deadlines, successors


def format_values(values):
    return "\t".join(str(value) for value in values)


def write_gsp_file(path: Path, n: int, weights, durations, due_dates, ready_dates, deadlines, successors):
    lines = [
        "n",
        str(n),
        "",
        "weight:",
        format_values(weights),
        "",
        "duration:",
        format_values(durations),
        "",
        "due date:",
        format_values(due_dates),
        "",
        "ready date:",
        format_values(ready_dates),
        "",
        "deadline:",
        format_values(deadlines),
        "",
        "precedence relations:",
        "",
    ]

    dummy_successor = n + 1
    for succs in successors:
        if succs:
            line = f"{len(succs)}\t" + " ".join(str(job) for job in succs)
        else:
            line = f"1\t{dummy_successor}"
        lines.append(line)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_filename(config: InstanceConfig) -> str:
    density_code = int(round(config.density * 100))
    phi_code = int(round(config.phi * 100))
    return (
        f"{config.n}_liu_r{config.rmax:02d}_k{config.due_divisor:02d}"
        f"_d{density_code:02d}_phi{phi_code:03d}_{config.rep}.GSP"
    )


def generate_configs(sizes, rmax_values, due_divisors, density_values, replications, phi):
    configs = []
    for n in sizes:
        for rmax in rmax_values:
            for due_divisor in due_divisors:
                for density in density_values:
                    for rep in range(1, replications + 1):
                        configs.append(
                            InstanceConfig(
                                n=n,
                                rmax=rmax,
                                due_divisor=due_divisor,
                                density=density,
                                phi=phi,
                                rep=rep,
                            )
                        )
    return configs


def main():
    parser = argparse.ArgumentParser(description="Generate Dataset_2010 pilot instances")
    parser.add_argument("--seed", type=int, default=20260424, help="Random seed for reproducibility")
    parser.add_argument(
        "--sizes",
        nargs="+",
        type=int,
        default=[20, 40, 50],
        help="Instance sizes to generate (default: 20 40 50)",
    )
    parser.add_argument(
        "--replications",
        type=int,
        default=1,
        help="Replications per parameter combination (default: 1)",
    )
    parser.add_argument(
        "--rmax-values",
        nargs="+",
        type=int,
        default=[25, 50],
        help="Release-date spread values (default: 25 50)",
    )
    parser.add_argument(
        "--due-divisors",
        nargs="+",
        type=int,
        default=[5, 10],
        help="Due-date divisors k in max offset 50*n/k (default: 5 10)",
    )
    parser.add_argument(
        "--densities",
        nargs="+",
        type=float,
        default=[0.2, 0.6],
        help="Precedence target densities D (default: 0.2 0.6)",
    )
    parser.add_argument(
        "--phi",
        type=float,
        default=1.25,
        help="Deadline extension coefficient in deadline_i ~ U[d_i, d_i + phi*P]",
    )
    parser.add_argument(
        "--profile",
        choices=["pilot", "full"],
        default="pilot",
        help="Use pilot defaults or Liu-style full grid defaults",
    )
    args = parser.parse_args()

    if args.profile == "full":
        if args.sizes == [20, 40, 50]:
            args.sizes = [20, 40, 60, 80, 100, 200, 400, 600, 800, 1000]
        if args.replications == 1:
            args.replications = 10
        if args.rmax_values == [25, 50]:
            args.rmax_values = [25, 50, 75]
        if args.due_divisors == [5, 10]:
            args.due_divisors = [1, 2, 5, 10, 20]
        if args.densities == [0.2, 0.6]:
            args.densities = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

    rng = random.Random(args.seed)
    configs = generate_configs(
        args.sizes,
        args.rmax_values,
        args.due_divisors,
        args.densities,
        args.replications,
        args.phi,
    )

    filenames_by_size = {size: [] for size in args.sizes}
    total_written = 0

    for config in configs:
        filename = build_filename(config)
        gsp_path = INS_ROOT / f"wtrd_pred{config.n}" / "S" / filename

        weights, durations, due_dates, ready_dates, deadlines, successors = build_instance(config, rng)
        write_gsp_file(
            gsp_path,
            config.n,
            weights,
            durations,
            due_dates,
            ready_dates,
            deadlines,
            successors,
        )

        filenames_by_size[config.n].append(filename)
        total_written += 1

    FILENAMES_ROOT.mkdir(parents=True, exist_ok=True)
    for size in args.sizes:
        size_filelist = FILENAMES_ROOT / f"{size}.txt"
        sorted_names = sorted(filenames_by_size.get(size, []))
        size_filelist.write_text("\n".join(sorted_names) + ("\n" if sorted_names else ""), encoding="utf-8")

    print("=" * 70)
    print("Dataset_2010 pilot generation complete")
    print("=" * 70)
    print(f"Seed         : {args.seed}")
    print(f"Sizes        : {', '.join(str(size) for size in args.sizes)}")
    print(f"Rmax values  : {', '.join(str(value) for value in args.rmax_values)}")
    print(f"Due divisors : {', '.join(str(value) for value in args.due_divisors)}")
    print(f"Densities    : {', '.join(str(value) for value in args.densities)}")
    print(f"Replications : {args.replications}")
    print(f"Phi          : {args.phi}")
    print(f"Total files  : {total_written}")
    for size in args.sizes:
        count = len(filenames_by_size.get(size, []))
        print(f"  - n={size}: {count} file(s)")
    print(f"Output root  : {DATASET_ROOT}")
    print("=" * 70)


if __name__ == "__main__":
    main()
