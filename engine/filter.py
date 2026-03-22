"""
filter.py
---------
Evaluates a parsed WHERE condition against a single row dict.

Type coercion:
    Both sides are cast to float if possible so that numeric
    comparisons work correctly on CSV data (all strings by default).
    e.g.  '9' < '25' is True as strings but False — numeric is correct.
"""

OPS = {
    "=":  lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">":  lambda a, b: a >  b,
    "<":  lambda a, b: a <  b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
}


def evaluate(row, condition):
    """
    Return True if the row satisfies the condition dict.

    Parameters
    ----------
    row       : dict   — one CSV row with typed values
    condition : dict   — {column, op, value} from parser

    Raises
    ------
    KeyError  if the column does not exist in the row
    """
    col   = condition["column"]
    op    = condition["op"]
    value = condition["value"]

    if col not in row:
        raise KeyError(
            f"Column '{col}' not found. "
            f"Available columns: {', '.join(row.keys())}"
        )

    row_val = row[col]

    # Coerce to comparable types
    row_val, value = _coerce(row_val, value)

    op_fn = OPS.get(op)
    if op_fn is None:
        raise ValueError(f"Unsupported operator: '{op}'")

    try:
        return op_fn(row_val, value)
    except TypeError:
        # Mixed types (e.g. None vs int) — treat as not matching
        return False


def _coerce(a, b):
    """
    Try to cast both values to float for numeric comparison.
    Falls back to str comparison if either side is non-numeric.
    """
    try:
        return float(a), float(b)
    except (TypeError, ValueError):
        return str(a).lower(), str(b).lower()
