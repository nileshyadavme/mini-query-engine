"""
executor.py
-----------
Takes a parsed query dict and a list of rows, runs the full pipeline:

    Load → Filter → Group → Sort → Project

Each stage is independent and can be tested in isolation.
"""

from engine.filter import evaluate
from engine.aggregator import group_and_count


def execute(parsed, rows):
    """
    Run the parsed query against the provided rows.

    Pipeline
    --------
    1. Filter  — apply WHERE condition
    2. Group   — apply GROUP BY + COUNT (returns early if present)
    3. Sort    — apply ORDER BY
    4. Project — apply SELECT (pick columns)

    Parameters
    ----------
    parsed : dict   — output of parser.parse()
    rows   : list   — list of dicts from loader.load_csv()

    Returns
    -------
    list of dicts
    """
    # 1. Filter
    if parsed["where"]:
        rows = [r for r in rows if evaluate(r, parsed["where"])]

    # 2. Group By — returns aggregated rows, skip sort/project after
    if parsed["group_by"]:
        return group_and_count(rows, parsed["group_by"])

    # 3. Sort
    if parsed["order_by"]:
        rows = _sort(rows, parsed["order_by"], parsed["order_dir"])

    # 4. Project
    if parsed["select"] != ["*"]:
        rows = _project(rows, parsed["select"])

    return rows


# ── private helpers ───────────────────────────────────────────────────────────

def _sort(rows, col, direction):
    """
    Sort rows by col.
    None values are pushed to the end regardless of direction.
    Numeric and string values are handled separately to avoid
    TypeError on mixed-type comparisons.
    """
    reverse = direction == "DESC"

    def sort_key(row):
        val = row.get(col)
        # Push None to the end
        if val is None:
            return (1, 0, "")
        if isinstance(val, (int, float)):
            return (0, val, "")
        return (0, 0, str(val).lower())

    return sorted(rows, key=sort_key, reverse=reverse)


def _project(rows, columns):
    """
    Return only the requested columns.
    Raises KeyError if a column doesn't exist in the first row.
    """
    if not rows:
        return []

    available = set(rows[0].keys())
    missing = [c for c in columns if c not in available]
    if missing:
        raise KeyError(
            f"Column(s) not found: {', '.join(missing)}. "
            f"Available: {', '.join(sorted(available))}"
        )

    return [{col: row[col] for col in columns} for row in rows]
