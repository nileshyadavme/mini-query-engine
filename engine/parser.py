"""
parser.py
---------
Parses a SQL-like query string into a structured dict.

Supported syntax:
    SELECT col1, col2 FROM table
    SELECT * FROM table
    SELECT col FROM table WHERE col OP value
    SELECT col FROM table ORDER BY col ASC|DESC
    SELECT col FROM table GROUP BY col
    SELECT col FROM table WHERE col OP value ORDER BY col ASC|DESC

Operators in WHERE: =  !=  >  <  >=  <=
"""

import re

SUPPORTED_OPS = (">=", "<=", "!=", ">", "<", "=")


def parse(query):
    """
    Parse a SQL query string into a structured dict.

    Returns
    -------
    dict with keys:
        select   : list of column names, or ['*']
        from     : table name (maps to <table>.csv in data/)
        where    : dict {column, op, value} or None
        order_by : column name or None
        order_dir: 'ASC' or 'DESC'
        group_by : column name or None
    """
    raw = query.strip()
    upper = raw.upper()

    _validate_keywords(upper)

    result = {
        "select":    _parse_select(raw, upper),
        "from":      _parse_from(raw, upper),
        "where":     _parse_where(raw, upper),
        "order_by":  None,
        "order_dir": "ASC",
        "group_by":  _parse_group_by(raw, upper),
    }

    order = _parse_order_by(raw, upper)
    if order:
        result["order_by"]  = order["column"]
        result["order_dir"] = order["direction"]

    return result


# ── private helpers ───────────────────────────────────────────────────────────

def _validate_keywords(upper):
    if not upper.startswith("SELECT"):
        raise SyntaxError("Query must start with SELECT")
    if "FROM" not in upper:
        raise SyntaxError("Query must contain FROM")


def _parse_select(raw, upper):
    from_pos = upper.index("FROM")
    select_raw = raw[6:from_pos].strip()
    if not select_raw:
        raise SyntaxError("No columns specified after SELECT")

    if select_raw.strip() == "*":
        return ["*"]

    cols = [c.strip().lower() for c in select_raw.split(",")]
    if any(c == "" for c in cols):
        raise SyntaxError("Empty column name in SELECT clause")
    return cols


def _parse_from(raw, upper):
    from_pos = upper.index("FROM") + 4
    # Everything after FROM up to the next keyword
    rest = raw[from_pos:].strip()
    token = re.split(r"\s+", rest)[0]
    if not token:
        raise SyntaxError("No table name after FROM")
    return token.lower()


def _parse_where(raw, upper):
    if "WHERE" not in upper:
        return None

    where_start = upper.index("WHERE") + 5

    # WHERE clause ends at ORDER BY or GROUP BY or end of string
    end = len(raw)
    for kw in ("ORDER BY", "GROUP BY"):
        if kw in upper[where_start:]:
            pos = upper.index(kw, where_start)
            end = min(end, pos)

    clause = raw[where_start:end].strip()
    if not clause:
        raise SyntaxError("Empty WHERE clause")

    return _parse_condition(clause)


def _parse_condition(clause):
    """
    Parse a single WHERE condition: column OP value
    Operators checked longest-first to avoid '>' matching '>='
    """
    for op in SUPPORTED_OPS:
        if op in clause:
            parts = clause.split(op, 1)
            if len(parts) != 2:
                continue
            col   = parts[0].strip().lower()
            value = parts[1].strip().strip("'\"")
            if col and value:
                return {"column": col, "op": op, "value": _infer_value_type(value)}

    raise SyntaxError(
        f"Cannot parse WHERE condition: '{clause}'. "
        f"Supported operators: {', '.join(SUPPORTED_OPS)}"
    )


def _parse_order_by(raw, upper):
    if "ORDER BY" not in upper:
        return None

    ob_start = upper.index("ORDER BY") + 8
    rest = raw[ob_start:].strip()

    # ORDER BY ends at GROUP BY or end of string
    if "GROUP BY" in upper[ob_start:]:
        gb_pos = upper.index("GROUP BY", ob_start)
        rest = raw[ob_start:gb_pos].strip()

    tokens = rest.split()
    if not tokens:
        raise SyntaxError("Empty ORDER BY clause")

    col = tokens[0].lower()
    direction = "DESC" if len(tokens) > 1 and tokens[1].upper() == "DESC" else "ASC"
    return {"column": col, "direction": direction}


def _parse_group_by(raw, upper):
    if "GROUP BY" not in upper:
        return None

    gb_start = upper.index("GROUP BY") + 8
    rest = raw[gb_start:].strip()
    token = re.split(r"\s+", rest)[0].lower()
    if not token:
        raise SyntaxError("Empty GROUP BY clause")
    return token


def _infer_value_type(value):
    """Try int → float → str."""
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value
