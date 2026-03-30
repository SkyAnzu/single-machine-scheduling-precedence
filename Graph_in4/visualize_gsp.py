"""
visualize_gsp.py
================
Reads .GSP scheduling instance files and draws the precedence constraint
graph with nodes arranged into topological layers (root jobs at top).

Output PNGs mirror the input sub-folder structure inside a central  graph/
directory that lives next to this script.

Usage
-----
  # Single file
  python Graph_in4/visualize_gsp.py --file "path/to/file.GSP"

  # Batch – every .GSP under a folder tree (uses multiprocessing)
  python Graph_in4/visualize_gsp.py --folder "path/to/Ins"
  python Graph_in4/visualize_gsp.py --folder "2016/Ins" --workers 8

Requirements
------------
  pip install networkx        (matplotlib already expected)
"""

import argparse
import sys
import multiprocessing
from pathlib import Path
from collections import defaultdict
from typing import Optional, List, Tuple, Dict, Any, TypedDict


class GspData(TypedDict):
    n:           int
    weights:     List[int]
    durations:   List[int]
    due_dates:   List[int]
    ready_dates: List[int]
    deadlines:   List[int]
    edges:       List[Tuple[int, int]]

import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec

# ---------------------------------------------------------------------------
# Root output directory: <script_dir>/graph/
# ---------------------------------------------------------------------------
SCRIPT_DIR  = Path(__file__).parent.resolve()
OUTPUT_ROOT = SCRIPT_DIR / "graph"


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _parse_number_line(lines, keyword):
    """Return list[int] on the next non-empty line after the line containing
    `keyword` (case-insensitive)."""
    for i, line in enumerate(lines):
        if keyword in line.lower():
            for j in range(i + 1, len(lines)):
                if lines[j].strip():
                    return list(map(int, lines[j].split()))
    return []


def parse_gsp(filepath: Path) -> GspData:
    """
    Parse a .GSP file.

    Returns a dict with keys:
        n            int
        weights      list[int]
        durations    list[int]
        due_dates    list[int]
        ready_dates  list[int]
        deadlines    list[int]
        edges        list[(int,int)]  predecessor -> successor
    """
    with open(filepath, "r") as f:
        lines = [l.strip() for l in f.readlines()]

    # ---- n ----
    n = None
    for i, line in enumerate(lines):
        if line.lower().startswith("n"):
            for j in range(i + 1, len(lines)):
                if lines[j]:
                    n = int(lines[j])
                    break
            break
    if n is None:
        raise ValueError(f"Cannot find 'n' in {filepath}")

    # ---- numeric fields ----
    weights     = _parse_number_line(lines, "weight:")
    durations   = _parse_number_line(lines, "duration:")
    due_dates   = _parse_number_line(lines, "due date:")
    ready_dates = _parse_number_line(lines, "ready date:")
    deadlines   = _parse_number_line(lines, "deadline:")

    # ---- precedence block ----
    pred_start = None
    for i, line in enumerate(lines):
        if "precedence" in line.lower():
            pred_start = i + 1
            break
    if pred_start is None:
        raise ValueError(f"Cannot find 'precedence relations' in {filepath}")

    prec_lines = []
    for line in lines[pred_start:]:
        if line:
            prec_lines.append(line)
        if len(prec_lines) == n:
            break

    edges = []
    for i, line in enumerate(prec_lines):
        tokens = line.split()
        if not tokens:
            continue
        count      = int(tokens[0])
        successors = [int(t) for t in tokens[1: 1 + count] if int(t) <= n]
        job_id     = i + 1
        for succ in successors:
            edges.append((job_id, succ))

    return GspData(
        n           = n,
        weights     = weights,
        durations   = durations,
        due_dates   = due_dates,
        ready_dates = ready_dates,
        deadlines   = deadlines,
        edges       = edges,
    )


# ---------------------------------------------------------------------------
# Layer assignment (longest-path layers)
# ---------------------------------------------------------------------------

def compute_layers(n: int, edges):
    """
    Returns (G, layer_dict) where layer_dict maps node -> int layer index.
    Layer 0 = roots (no predecessors).
    """
    G = nx.DiGraph()
    G.add_nodes_from(range(1, n + 1))
    G.add_edges_from(edges)

    layer = {}
    for node in nx.topological_sort(G):
        preds = list(G.predecessors(node))
        layer[node] = 0 if not preds else max(layer[p] for p in preds) + 1

    return G, layer


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------

def draw_graph(G: nx.DiGraph, layer: Dict[int, int], data: GspData, title: str,
               output_path: Path):
    """Draw the layered graph with a statistics panel and save as PNG."""

    horizontal_spacing = 1.7

    def job_value(values: List[int], node: int) -> Any:
        index = node - 1
        return values[index] if 0 <= index < len(values) else "N/A"

    n_layers    = max(layer.values()) + 1
    layer_nodes = defaultdict(list)
    for node, lyr in layer.items():
        layer_nodes[lyr].append(node)

    # ---- node positions (centred per layer, top-to-bottom) ----
    pos = {}
    for lyr, nodes in layer_nodes.items():
        nodes_sorted = sorted(nodes)
        total = len(nodes_sorted)
        for rank, node in enumerate(nodes_sorted):
            pos[node] = ((rank - (total - 1) / 2.0) * horizontal_spacing, -lyr)

    # ---- figure sizing ----
    max_width = max(len(v) for v in layer_nodes.values())
    fig_w = max(24, max_width * 2.8 + 8)
    fig_h = max(10, n_layers  * 1.7)

    fig = plt.figure(figsize=(fig_w, fig_h))
    gs  = gridspec.GridSpec(1, 2, width_ratios=[3, 1], figure=fig,
                            wspace=0.05)

    ax_graph = fig.add_subplot(gs[0])
    ax_stats = fig.add_subplot(gs[1])

    fig.suptitle(title, fontsize=11, fontweight="bold", y=0.99)

    # ======== GRAPH PANEL ========
    ax_graph.axis("off")

    # layer background bands
    x_vals = [x for x, _ in pos.values()]
    x_min  = min(x_vals) - 1.0
    for lyr in range(n_layers):
        if not layer_nodes[lyr]:
            continue
        y_c = -lyr
        ax_graph.axhspan(
            y_c - 0.48, y_c + 0.48,
            alpha=0.07,
            color="#4a90d9" if lyr % 2 == 0 else "#e07b3f",
            zorder=0,
        )
        ax_graph.text(
            x_min, y_c,
            f"Layer {lyr + 1}",
            fontsize=7.5, color="#555", va="center", style="italic",
        )

    # edges
    nx.draw_networkx_edges(
        G, pos, ax=ax_graph,
        edge_color="#888888", arrows=True,
        arrowstyle="-|>", arrowsize=16, width=1.1,
        connectionstyle="arc3,rad=0.05",
        min_source_margin=16, min_target_margin=16,
    )

    # node colours
    max_lyr     = max(layer.values())
    node_colors = []
    for node in G.nodes():
        lyr = layer[node]
        if lyr == 0:
            node_colors.append("#2ecc71")    # green  – root
        elif lyr == max_lyr:
            node_colors.append("#e74c3c")    # red    – leaf
        else:
            node_colors.append("#3498db")    # blue   – middle

    nx.draw_networkx_nodes(
        G, pos, ax=ax_graph,
        node_color=node_colors, node_size=650,
        linewidths=1.4, edgecolors="#222",
    )
    nx.draw_networkx_labels(
        G, pos,
        labels={node: f"J{node}" for node in G.nodes()},
        ax=ax_graph, font_size=7.5,
        font_color="white", font_weight="bold",
    )

    for node in G.nodes():
        x, y = pos[node]
        annotation = (
            f"ready={job_value(data['ready_dates'], node)}\n"
            f"due={job_value(data['due_dates'], node)}\n"
            f"deadline={job_value(data['deadlines'], node)}"
        )
        ax_graph.annotate(
            annotation,
            (x, y),
            textcoords="offset points",
            xytext=(24, 0),
            ha="left",
            va="center",
            fontsize=6.4,
            annotation_clip=False,
            bbox=dict(
                boxstyle="round,pad=0.25",
                facecolor="#fffbe6",
                edgecolor="#c7b96d",
                linewidth=0.8,
                alpha=0.95,
            ),
        )

    x_max = max(x_vals) + 3.8
    ax_graph.set_xlim(x_min - 0.6, x_max)
    ax_graph.set_ylim(-n_layers + 0.3, 1.0)

    ax_graph.legend(
        handles=[
            mpatches.Patch(color="#2ecc71", label="Root (no predecessors)"),
            mpatches.Patch(color="#3498db", label="Intermediate"),
            mpatches.Patch(color="#e74c3c", label="Leaf (no successors)"),
        ],
        loc="lower right", fontsize=8, framealpha=0.85,
    )

    # ======== STATS PANEL ========
    ax_stats.axis("off")

    n           = data["n"]
    n_edges     = G.number_of_edges()

    def fmt(values):
        if not values:
            return "  min = N/A\n  max = N/A"
        return f"  min = {min(values)}\n  max = {max(values)}"

    stats_str = (
        "━" * 26 + "\n"
        " INSTANCE STATISTICS\n"
        + "━" * 26 + "\n"
        f"\n  Declared jobs (n):  {n}"
        f"\n  Precedence edges:   {n_edges}"
        f"\n  DAG layers:         {n_layers}"
        "\n\n" + "─" * 26 + "\n"
        " Weight\n"  + fmt(data["weights"])
        + "\n\n" + "─" * 26 + "\n"
        " Duration\n" + fmt(data["durations"])
        + "\n\n" + "─" * 26 + "\n"
        " Ready date\n" + fmt(data["ready_dates"])
        + "\n\n" + "─" * 26 + "\n"
        " Due date\n"  + fmt(data["due_dates"])
        + "\n\n" + "─" * 26 + "\n"
        " Deadline\n"  + fmt(data["deadlines"])
        + "\n\n" + "━" * 26
    )

    ax_stats.text(
        0.05, 0.97, stats_str,
        transform=ax_stats.transAxes,
        fontsize=8.5,
        verticalalignment="top",
        fontfamily="monospace",
        bbox=dict(boxstyle="round,pad=0.7", facecolor="#f7f7f7",
                  edgecolor="#bbbbbb", linewidth=1.2),
    )

    # ======== SAVE ========
    plt.tight_layout(rect=(0, 0, 1, 0.98))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Output path helper
# ---------------------------------------------------------------------------

def make_output_path(gsp_path: Path, input_root: Optional[Path] = None,
                     output_root: Optional[Path] = None) -> Path:
    """
    Mirror input_root sub-folder structure under OUTPUT_ROOT.

    input_root = .../Ins
    gsp_path   = .../Ins/wtrd_pred30/L/30_00_005_100_75_4.GSP
    output     = <script>/graph/wtrd_pred30/L/30_00_005_100_75_4.png
    """
    if input_root is None:
        for parent in gsp_path.parents:
            if parent.name.lower() == "ins":
                input_root = parent
                break

    target_root = output_root or OUTPUT_ROOT

    stem = gsp_path.stem
    if input_root is not None:
        try:
            rel = gsp_path.parent.relative_to(input_root)
        except ValueError:
            rel = Path(gsp_path.parent.name)
        return target_root / rel / f"{stem}.png"
    return target_root / f"{stem}.png"


# ---------------------------------------------------------------------------
# Worker (top-level so it's picklable for multiprocessing)
# ---------------------------------------------------------------------------

def process_file(gsp_path: Path, input_root: Optional[Path] = None,
                 index: Optional[int] = None, total: Optional[int] = None,
                 output_root: Optional[Path] = None):
    prefix = f"[{index}/{total}] " if index is not None else ""
    try:
        data         = parse_gsp(gsp_path)
        n_jobs: int  = int(data["n"])
        edges: List[Tuple[int,int]] = list(data["edges"])
        G, layer     = compute_layers(n_jobs, edges)
        out          = make_output_path(gsp_path, input_root, output_root=output_root)
        n_layers     = max(layer.values()) + 1
        title        = (f"{gsp_path.name}  —  "
                         f"n={data['n']},  "
                         f"{len(edges)} edges,  "
                        f"{n_layers} layers")
        draw_graph(G, layer, data, title, out)
        print(f"{prefix}Saved  {out}", flush=True)
        return True
    except Exception as exc:
        print(f"{prefix}ERROR  {gsp_path}: {exc}", file=sys.stderr, flush=True)
        return False


def _worker(args):
    """Unpack tuple -> process_file.  Required for Pool.map pickling."""
    return process_file(*args)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Visualise .GSP scheduling instances as layered DAG images."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file",   "-f", metavar="FILE",
                       help="Path to a single .GSP file.")
    group.add_argument("--folder", "-d", metavar="FOLDER",
                       help="Folder to search recursively for .GSP files.")
    parser.add_argument(
        "--workers", "-w", type=int,
        default=max(1, multiprocessing.cpu_count() - 1),
        help="Parallel workers for batch mode (default: CPU count - 1).",
    )
    args = parser.parse_args()

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    # ---- single file ----
    if args.file:
        gsp = Path(args.file).resolve()
        if not gsp.is_file():
            print(f"ERROR: file not found: {gsp}", file=sys.stderr)
            sys.exit(1)
        process_file(gsp)
        print("Done.")
        return

    # ---- batch folder ----
    folder = Path(args.folder).resolve()
    if not folder.is_dir():
        print(f"ERROR: folder not found: {folder}", file=sys.stderr)
        sys.exit(1)

    gsp_files = sorted(folder.rglob("*.GSP"), key=lambda p: str(p).lower())
    seen, unique = set(), []
    for f in gsp_files:
        key = str(f).lower()
        if key not in seen:
            seen.add(key)
            unique.append(f)
    gsp_files = unique

    if not gsp_files:
        print(f"No .GSP files found under {folder}")
        sys.exit(0)

    total   = len(gsp_files)
    workers = min(args.workers, total)
    print(f"Found {total} .GSP file(s) — using {workers} worker(s).")

    tasks = [(gsp, folder, i + 1, total) for i, gsp in enumerate(gsp_files)]

    if workers == 1:
        for t in tasks:
            _worker(t)
    else:
        ctx = multiprocessing.get_context("spawn")
        with ctx.Pool(processes=workers) as pool:
            pool.map(_worker, tasks)

    print("Done.")


if __name__ == "__main__":
    main()
