"""
main.py
-------
Public API for the Mini Query Engine.

Usage
-----
    from main import QueryEngine

    engine = QueryEngine()
    results = engine.query("SELECT name, age FROM users WHERE age > 25 ORDER BY age DESC")
    for row in results:
        print(row)

Or run directly for an interactive REPL:
    python main.py
"""

import os
from loader import load_csv
from engine.parser import parse
from engine.executor import execute


class QueryEngine:
    """
    Runs SQL-like queries against CSV files in a data directory.

    Parameters
    ----------
    data_dir : str
        Path to the folder containing .csv files.
        Table name in FROM maps to <data_dir>/<table>.csv
    """

    def __init__(self, data_dir="data"):
        self.data_dir = data_dir

    def query(self, sql):
        """
        Execute a SQL-like query string.

        Parameters
        ----------
        sql : str — the query to run

        Returns
        -------
        list of dicts — each dict is one result row

        Raises
        ------
        SyntaxError  — malformed query
        FileNotFoundError — table CSV not found
        KeyError     — column not found
        """
        parsed = parse(sql)
        filepath = os.path.join(self.data_dir, f"{parsed['from']}.csv")
        rows = load_csv(filepath)
        return execute(parsed, rows)

    def tables(self):
        """List available tables (CSV files) in the data directory."""
        if not os.path.exists(self.data_dir):
            return []
        return [
            f[:-4] for f in os.listdir(self.data_dir)
            if f.endswith(".csv")
        ]


# ── REPL ─────────────────────────────────────────────────────────────────────

def _print_results(rows):
    if not rows:
        print("  (no rows returned)")
        return

    headers = list(rows[0].keys())
    col_widths = {h: max(len(h), max(len(str(r.get(h, ""))) for r in rows))
                  for h in headers}

    divider = "+-" + "-+-".join("-" * col_widths[h] for h in headers) + "-+"
    header_row = "| " + " | ".join(h.ljust(col_widths[h]) for h in headers) + " |"

    print(divider)
    print(header_row)
    print(divider)
    for row in rows:
        line = "| " + " | ".join(
            str(row.get(h, "")).ljust(col_widths[h]) for h in headers
        ) + " |"
        print(line)
    print(divider)
    print(f"  {len(rows)} row(s)\n")


def main():
    engine = QueryEngine()

    print("\nMini Query Engine")
    print("=" * 40)
    tables = engine.tables()
    if tables:
        print(f"Tables: {', '.join(tables)}")
    else:
        print("No CSV files found in data/")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            sql = input("sql> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not sql:
            continue
        if sql.lower() == "exit":
            print("Exiting.")
            break

        try:
            results = engine.query(sql)
            _print_results(results)
        except (SyntaxError, FileNotFoundError, KeyError, ValueError) as e:
            print(f"  Error: {e}\n")


if __name__ == "__main__":
    main()
