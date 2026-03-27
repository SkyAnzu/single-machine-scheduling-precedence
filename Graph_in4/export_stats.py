"""
export_stats.py
===============
Parses every .GSP file under a given folder tree and writes an Excel workbook
with one sheet per sub-folder (e.g. wtrd_pred10/L, wtrd_pred30/S …).

Each row = one instance with columns:
  File | n | Edges | Layers |
  Weight min/max | Duration min/max |
  Ready date min/max | Due date min/max | Deadline min/max

Usage
-----
  python export_stats.py                                # uses default Ins folder
  python export_stats.py --folder "D:/path/to/Ins"
  python export_stats.py --folder "D:/path/to/Ins" --out "my_stats.xlsx"

Output
------
  <script_dir>/gsp_statistics.xlsx   (or path given with --out)
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple, Optional, TypedDict

import networkx as nx
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import (Font, PatternFill, Alignment, Border, Side,
                              GradientFill)
from openpyxl.utils import get_column_letter

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
SCRIPT_DIR   = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_INS  = PROJECT_ROOT / "2016" / "Ins"
DEFAULT_OUT  = SCRIPT_DIR / "gsp_statistics.xlsx"


# ---------------------------------------------------------------------------
# GSP data type
# ---------------------------------------------------------------------------
class GspData(TypedDict):
    n:           int
    weights:     List[int]
    durations:   List[int]
    due_dates:   List[int]
    ready_dates: List[int]
    deadlines:   List[int]
    edges:       List[Tuple[int, int]]


# ---------------------------------------------------------------------------
# Parser  (identical logic to visualize_gsp.py)
# ---------------------------------------------------------------------------

def _parse_number_line(lines: List[str], keyword: str) -> List[int]:
    for i, line in enumerate(lines):
        if keyword in line.lower():
            for j in range(i + 1, len(lines)):
                if lines[j].strip():
                    return list(map(int, lines[j].split()))
    return []


def parse_gsp(filepath: Path) -> GspData:
    with open(filepath, "r") as f:
        lines = [l.strip() for l in f.readlines()]

    # n
    n: Optional[int] = None
    for i, line in enumerate(lines):
        if line.lower().startswith("n"):
            for j in range(i + 1, len(lines)):
                if lines[j]:
                    n = int(lines[j])
                    break
            break
    if n is None:
        raise ValueError(f"Cannot find 'n' in {filepath}")

    weights     = _parse_number_line(lines, "weight:")
    durations   = _parse_number_line(lines, "duration:")
    due_dates   = _parse_number_line(lines, "due date:")
    ready_dates = _parse_number_line(lines, "ready date:")
    deadlines   = _parse_number_line(lines, "deadline:")

    # precedence
    pred_start: Optional[int] = None
    for i, line in enumerate(lines):
        if "precedence" in line.lower():
            pred_start = i + 1
            break
    if pred_start is None:
        raise ValueError(f"Cannot find 'precedence relations' in {filepath}")

    prec_lines: List[str] = []
    for line in lines[pred_start:]:
        if line:
            prec_lines.append(line)
        if len(prec_lines) == n:
            break

    edges: List[Tuple[int, int]] = []
    for i, line in enumerate(prec_lines):
        tokens = line.split()
        if not tokens:
            continue
        count      = int(tokens[0])
        successors = [int(t) for t in tokens[1: 1 + count]]
        job_id     = i + 1
        for succ in successors:
            edges.append((job_id, succ))

    return GspData(
        n=n, weights=weights, durations=durations,
        due_dates=due_dates, ready_dates=ready_dates,
        deadlines=deadlines, edges=edges,
    )


# ---------------------------------------------------------------------------
# Layer count helper
# ---------------------------------------------------------------------------

def count_layers(n: int, edges: List[Tuple[int, int]]) -> int:
    all_nodes = set(range(1, n + 1))
    for u, v in edges:
        all_nodes.add(u)
        all_nodes.add(v)
    G = nx.DiGraph()
    G.add_nodes_from(sorted(all_nodes))
    G.add_edges_from(edges)
    layer: dict = {}
    for node in nx.topological_sort(G):
        preds = list(G.predecessors(node))
        layer[node] = 0 if not preds else max(layer[p] for p in preds) + 1
    return max(layer.values()) + 1 if layer else 1


# ---------------------------------------------------------------------------
# Build one row dict from a parsed file
# ---------------------------------------------------------------------------

def _stat(values: List[int], key: str):
    """Return {key_min: …, key_max: …}; None when list is empty."""
    if not values:
        return {f"{key}_min": None, f"{key}_max": None}
    return {f"{key}_min": min(values), f"{key}_max": max(values)}


def file_to_row(gsp_path: Path, input_root: Path) -> dict:
    data   = parse_gsp(gsp_path)
    n      = data["n"]
    edges  = data["edges"]
    layers = count_layers(n, edges)

    try:
        rel_folder = str(gsp_path.parent.relative_to(input_root))
    except ValueError:
        rel_folder = gsp_path.parent.name

    row: dict = {
        "File":    gsp_path.stem,
        "Folder":  rel_folder,
        "n (jobs)":  n,
        "Edges":     len(edges),
        "Layers":    layers,
    }
    row.update(_stat(data["weights"],     "Weight"))
    row.update(_stat(data["durations"],   "Duration"))
    row.update(_stat(data["ready_dates"], "Ready_date"))
    row.update(_stat(data["due_dates"],   "Due_date"))
    row.update(_stat(data["deadlines"],   "Deadline"))
    return row


# ---------------------------------------------------------------------------
# Excel formatting helpers
# ---------------------------------------------------------------------------

HEADER_GROUPS = [
    # (header_label,        columns_in_group)
    ("Instance",            ["File", "Folder"]),
    ("Graph",               ["n (jobs)", "Edges", "Layers"]),
    ("Weight",              ["Weight_min", "Weight_max"]),
    ("Duration",            ["Duration_min", "Duration_max"]),
    ("Ready date",          ["Ready_date_min", "Ready_date_max"]),
    ("Due date",            ["Due_date_min", "Due_date_max"]),
    ("Deadline",            ["Deadline_min", "Deadline_max"]),
]

# Colours for group header cells (alternating)
GROUP_FILLS = [
    "2E75B6",  # dark blue    – Instance
    "70AD47",  # green        – Graph
    "ED7D31",  # orange       – Weight
    "4472C4",  # medium blue  – Duration
    "A9D18E",  # light green  – Ready date
    "F4B942",  # yellow       – Due date
    "C55A11",  # dark orange  – Deadline
]

SUBHEADER_FILLS = [
    "BDD7EE",  # light blue
    "E2EFDA",  # light green
    "FCE4D6",  # light orange
    "DAE3F3",  # light blue 2
    "E2EFDA",  # light green 2
    "FFF2CC",  # light yellow
    "F8CBAD",  # light orange 2
]


def _thin_border():
    thin = Side(style="thin", color="BFBFBF")
    return Border(left=thin, right=thin, top=thin, bottom=thin)


def _apply_header(ws, col_map: dict):
    """Write two header rows: group row (row 1) + column names (row 2)."""
    border = _thin_border()

    for g_idx, (group_label, cols) in enumerate(HEADER_GROUPS):
        col_indices = [col_map[c] for c in cols]
        c_start = min(col_indices)
        c_end   = max(col_indices)
        col_letter_start = get_column_letter(c_start)
        col_letter_end   = get_column_letter(c_end)

        # merge group header
        if c_start != c_end:
            ws.merge_cells(f"{col_letter_start}1:{col_letter_end}1")

        cell = ws[f"{col_letter_start}1"]
        cell.value     = group_label
        cell.font      = Font(bold=True, color="FFFFFF", size=10)
        cell.fill      = PatternFill("solid", fgColor=GROUP_FILLS[g_idx])
        cell.alignment = Alignment(horizontal="center", vertical="center",
                                   wrap_text=True)
        cell.border    = border

        # sub-headers (row 2)
        sub_fill = PatternFill("solid", fgColor=SUBHEADER_FILLS[g_idx])
        for col_name in cols:
            c = col_map[col_name]
            # friendly label: strip prefix (e.g. "Weight_min" -> "Min")
            parts = col_name.split("_")
            label = parts[-1].capitalize() if len(parts) > 1 else col_name
            sub_cell = ws.cell(row=2, column=c)
            sub_cell.value     = label
            sub_cell.font      = Font(bold=True, size=9)
            sub_cell.fill      = sub_fill
            sub_cell.alignment = Alignment(horizontal="center",
                                           vertical="center")
            sub_cell.border    = border


def _style_data_rows(ws, n_rows: int, col_map: dict):
    """Alternating row colours + borders for data rows (rows 3 … n_rows+2)."""
    border = _thin_border()
    fill_even = PatternFill("solid", fgColor="F2F2F2")

    for r in range(3, n_rows + 3):
        for col_name, c in col_map.items():
            cell = ws.cell(row=r, column=c)
            cell.border    = border
            cell.alignment = Alignment(horizontal="center", vertical="center")
            if r % 2 == 0:
                cell.fill = fill_even
        # left-align text columns
        for col_name in ("File", "Folder"):
            ws.cell(row=r, column=col_map[col_name]).alignment = Alignment(
                horizontal="left", vertical="center"
            )


def _set_column_widths(ws, col_map: dict, df: pd.DataFrame):
    """Auto-size columns based on content."""
    width_hints = {
        "File":           28,
        "Folder":         18,
        "n (jobs)":        8,
        "Edges":           8,
        "Layers":          8,
        "Weight_min":      9,
        "Weight_max":      9,
        "Duration_min":   11,
        "Duration_max":   11,
        "Ready_date_min": 13,
        "Ready_date_max": 13,
        "Due_date_min":   11,
        "Due_date_max":   11,
        "Deadline_min":   12,
        "Deadline_max":   12,
    }
    for col_name, c in col_map.items():
        ws.column_dimensions[get_column_letter(c)].width = (
            width_hints.get(col_name, 12)
        )
    ws.row_dimensions[1].height = 22
    ws.row_dimensions[2].height = 18


# ---------------------------------------------------------------------------
# Write workbook
# ---------------------------------------------------------------------------

COLUMNS_ORDER = [
    "File", "Folder",
    "n (jobs)", "Edges", "Layers",
    "Weight_min", "Weight_max",
    "Duration_min", "Duration_max",
    "Ready_date_min", "Ready_date_max",
    "Due_date_min", "Due_date_max",
    "Deadline_min", "Deadline_max",
]


def write_excel(rows: List[dict], out_path: Path):
    df = pd.DataFrame(rows, columns=COLUMNS_ORDER)

    # Sort by Folder then File
    df.sort_values(["Folder", "File"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # ---- one sheet per sub-folder + one "All" summary sheet ----
    sheet_data: dict = {"All": df}
    for folder, grp in df.groupby("Folder"):
        sheet_name = str(folder).replace("\\", "/").replace("/", "_")
        # Excel sheet name max 31 chars
        sheet_name = sheet_name[:31]
        sheet_data[sheet_name] = grp.reset_index(drop=True)

    # write raw data via pandas first (creates the file)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        for sheet_name, sheet_df in sheet_data.items():
            # write starting at row 3 (rows 1-2 are our custom headers)
            sheet_df.to_excel(writer, sheet_name=sheet_name,
                              index=False, header=False, startrow=2)

    # ---- now re-open and apply formatting ----
    wb = load_workbook(out_path)

    col_map = {col: idx + 1 for idx, col in enumerate(COLUMNS_ORDER)}

    for sheet_name, sheet_df in sheet_data.items():
        ws = wb[sheet_name]
        _apply_header(ws, col_map)
        _style_data_rows(ws, len(sheet_df), col_map)
        _set_column_widths(ws, col_map, sheet_df)
        ws.freeze_panes = "A3"   # freeze the two header rows

    # Put "All" sheet first
    if "All" in wb.sheetnames:
        wb.move_sheet("All", offset=-len(wb.sheetnames) + 1)

    wb.save(out_path)
    print(f"Saved  {out_path}  ({len(rows)} rows, {len(sheet_data)} sheets)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Export GSP instance statistics to Excel."
    )
    parser.add_argument("--folder", "-d", default=str(DEFAULT_INS),
                        help=f"Root folder to scan (default: {DEFAULT_INS})")
    parser.add_argument("--out", "-o", default=str(DEFAULT_OUT),
                        help=f"Output Excel path (default: {DEFAULT_OUT})")
    args = parser.parse_args()

    folder   = Path(args.folder).resolve()
    out_path = Path(args.out).resolve()

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

    total = len(gsp_files)
    print(f"Parsing {total} files …")

    rows = []
    errors = 0
    for i, gsp in enumerate(gsp_files, 1):
        try:
            rows.append(file_to_row(gsp, folder))
            if i % 200 == 0 or i == total:
                print(f"  [{i}/{total}] parsed", flush=True)
        except Exception as exc:
            print(f"  ERROR {gsp}: {exc}", file=sys.stderr)
            errors += 1

    if errors:
        print(f"  {errors} file(s) had errors and were skipped.")

    print(f"Writing Excel …")
    write_excel(rows, out_path)
    print("Done.")


if __name__ == "__main__":
    main()
