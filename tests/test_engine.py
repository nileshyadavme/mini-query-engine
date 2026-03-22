"""
tests/test_engine.py
--------------------
Test suite for the Mini Query Engine.
Covers: parser, filter, aggregator, executor, loader, and end-to-end queries.

Run with:
    python -m pytest tests/ -v
or:
    python tests/test_engine.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.parser import parse
from engine.filter import evaluate
from engine.aggregator import group_and_count
from engine.executor import execute
from loader import load_csv, _infer_type
from main import QueryEngine

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

results = {"passed": 0, "failed": 0}


def check(label, condition, got=None, expected=None):
    if condition:
        print(f"  [{PASS}] {label}")
        results["passed"] += 1
    else:
        print(f"  [{FAIL}] {label}")
        if got is not None or expected is not None:
            print(f"          got:      {got}")
            print(f"          expected: {expected}")
        results["failed"] += 1


def check_raises(label, exc_type, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
        print(f"  [{FAIL}] {label}  (no exception raised)")
        results["failed"] += 1
    except exc_type:
        print(f"  [{PASS}] {label}")
        results["passed"] += 1
    except Exception as e:
        print(f"  [{FAIL}] {label}  (wrong exception: {type(e).__name__}: {e})")
        results["failed"] += 1


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — Type Inference
# ─────────────────────────────────────────────────────────────────────────────
def test_type_inference():
    print("\n── Type Inference ──────────────────────────────")
    check("integer string",      _infer_type("42")    == 42)
    check("negative integer",    _infer_type("-7")    == -7)
    check("float string",        _infer_type("3.14")  == 3.14)
    check("plain string",        _infer_type("hello") == "hello")
    check("empty string → None", _infer_type("")      is None)
    check("zero",                _infer_type("0")     == 0)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — Parser
# ─────────────────────────────────────────────────────────────────────────────
def test_parser():
    print("\n── Parser ──────────────────────────────────────")

    p = parse("SELECT * FROM users")
    check("SELECT * FROM",        p["select"] == ["*"] and p["from"] == "users")

    p = parse("SELECT name, age FROM users")
    check("SELECT cols FROM",     p["select"] == ["name", "age"])

    p = parse("SELECT * FROM users WHERE age > 25")
    check("WHERE >",              p["where"] == {"column": "age", "op": ">", "value": 25})

    p = parse("SELECT * FROM users WHERE city = 'Mumbai'")
    check("WHERE = string",       p["where"]["value"] == "Mumbai")

    p = parse("SELECT * FROM users ORDER BY age DESC")
    check("ORDER BY DESC",        p["order_by"] == "age" and p["order_dir"] == "DESC")

    p = parse("SELECT * FROM users ORDER BY name ASC")
    check("ORDER BY ASC",         p["order_dir"] == "ASC")

    p = parse("SELECT * FROM users GROUP BY department")
    check("GROUP BY",             p["group_by"] == "department")

    p = parse("SELECT name FROM users WHERE age >= 30 ORDER BY age DESC")
    check("WHERE + ORDER BY combined",
          p["where"]["op"] == ">=" and p["order_by"] == "age" and p["order_dir"] == "DESC")

    p = parse("SELECT * FROM users WHERE salary != 62000")
    check("WHERE !=",             p["where"]["op"] == "!=")

    p = parse("SELECT * FROM users WHERE rating <= 4.0")
    check("WHERE <= float",       p["where"]["value"] == 4.0)

    # Case insensitivity
    p = parse("select * from users where age > 20 order by age asc")
    check("lowercase keywords",   p["from"] == "users" and p["order_dir"] == "ASC")

    # Error cases
    check_raises("missing FROM",         SyntaxError, parse, "SELECT * users")
    check_raises("missing SELECT",       SyntaxError, parse, "FROM users")
    check_raises("empty WHERE",          SyntaxError, parse, "SELECT * FROM users WHERE")
    check_raises("invalid WHERE op",     SyntaxError, parse, "SELECT * FROM users WHERE age BETWEEN 1 AND 5")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — Filter
# ─────────────────────────────────────────────────────────────────────────────
def test_filter():
    print("\n── Filter ──────────────────────────────────────")
    row = {"name": "Alice", "age": 30, "city": "Mumbai", "salary": 85000.0}

    check("age > 25 (true)",      evaluate(row, {"column": "age",  "op": ">",  "value": 25}))
    check("age > 30 (false)",    not evaluate(row, {"column": "age",  "op": ">",  "value": 30}))
    check("age >= 30 (true)",     evaluate(row, {"column": "age",  "op": ">=", "value": 30}))
    check("age = 30 (true)",      evaluate(row, {"column": "age",  "op": "=",  "value": 30}))
    check("age != 99 (true)",     evaluate(row, {"column": "age",  "op": "!=", "value": 99}))
    check("salary < 90000 (true)",evaluate(row, {"column": "salary","op": "<", "value": 90000}))
    check("city = Mumbai (true)", evaluate(row, {"column": "city", "op": "=",  "value": "Mumbai"}))
    check("city != Delhi (true)", evaluate(row, {"column": "city", "op": "!=", "value": "Delhi"}))

    # Numeric string comparison — key correctness test
    row2 = {"age": 9}
    check("9 < 25 numeric (true, not string)",
          evaluate(row2, {"column": "age", "op": "<", "value": 25}))

    check_raises("missing column", KeyError, evaluate, row, {"column": "zzz", "op": "=", "value": 1})


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — Aggregator
# ─────────────────────────────────────────────────────────────────────────────
def test_aggregator():
    print("\n── Aggregator ──────────────────────────────────")
    rows = [
        {"dept": "Eng", "name": "Alice"},
        {"dept": "Eng", "name": "Bob"},
        {"dept": "HR",  "name": "Carol"},
        {"dept": "Eng", "name": "Dave"},
        {"dept": "HR",  "name": "Eve"},
    ]

    result = group_and_count(rows, "dept")
    counts = {r["dept"]: r["count"] for r in result}

    check("Eng count = 3",        counts.get("Eng") == 3)
    check("HR count = 2",         counts.get("HR")  == 2)
    check("sorted by count desc", result[0]["dept"] == "Eng")
    check("returns 2 groups",     len(result) == 2)
    check("empty rows → empty",   group_and_count([], "dept") == [])
    check_raises("bad column",    KeyError, group_and_count, rows, "zzz")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — Executor
# ─────────────────────────────────────────────────────────────────────────────
def test_executor():
    print("\n── Executor ────────────────────────────────────")
    rows = [
        {"name": "Alice", "age": 30, "dept": "Eng",  "salary": 85000},
        {"name": "Bob",   "age": 25, "dept": "Mktg", "salary": 62000},
        {"name": "Carol", "age": 35, "dept": "Eng",  "salary": 95000},
        {"name": "Dave",  "age": 22, "dept": "Mktg", "salary": 48000},
        {"name": "Eve",   "age": 33, "dept": "Eng",  "salary": 88000},
    ]

    # WHERE only
    parsed = parse("SELECT * FROM t WHERE age > 28")
    out = execute(parsed, rows)
    check("WHERE age > 28 → 3 rows",  len(out) == 3)
    check("all ages > 28",            all(r["age"] > 28 for r in out))

    # ORDER BY ASC
    parsed = parse("SELECT * FROM t ORDER BY age ASC")
    out = execute(parsed, rows)
    ages = [r["age"] for r in out]
    check("ORDER BY age ASC",         ages == sorted(ages))

    # ORDER BY DESC
    parsed = parse("SELECT * FROM t ORDER BY salary DESC")
    out = execute(parsed, rows)
    salaries = [r["salary"] for r in out]
    check("ORDER BY salary DESC",     salaries == sorted(salaries, reverse=True))

    # SELECT specific cols
    parsed = parse("SELECT name, salary FROM t")
    out = execute(parsed, rows)
    check("SELECT projects cols",     set(out[0].keys()) == {"name", "salary"})

    # GROUP BY
    parsed = parse("SELECT * FROM t GROUP BY dept")
    out = execute(parsed, rows)
    counts = {r["dept"]: r["count"] for r in out}
    check("GROUP BY dept, Eng=3",     counts.get("Eng") == 3)
    check("GROUP BY dept, Mktg=2",    counts.get("Mktg") == 2)

    # WHERE + ORDER BY combined
    parsed = parse("SELECT name, salary FROM t WHERE age > 25 ORDER BY salary DESC")
    out = execute(parsed, rows)
    check("WHERE + ORDER BY rows",    len(out) == 3)
    check("WHERE + ORDER BY sorted",  out[0]["salary"] >= out[-1]["salary"])

    # Empty result
    parsed = parse("SELECT * FROM t WHERE age > 100")
    out = execute(parsed, rows)
    check("WHERE no match → empty",   out == [])

    # Bad column in SELECT
    parsed = parse("SELECT zzz FROM t")
    check_raises("bad SELECT col",    KeyError, execute, parsed, rows)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — CSV Loader
# ─────────────────────────────────────────────────────────────────────────────
def test_loader():
    print("\n── Loader ──────────────────────────────────────")
    rows = load_csv("data/users.csv")

    check("loads 10 rows",            len(rows) == 10)
    check("age is int",               isinstance(rows[0]["age"], int))
    check("salary is int",            isinstance(rows[0]["salary"], int))
    check("name is str",              isinstance(rows[0]["name"], str))
    check("keys are lowercase",       all(k == k.lower() for k in rows[0].keys()))
    check_raises("missing file",      FileNotFoundError, load_csv, "data/nope.csv")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7 — End-to-End (QueryEngine on real CSVs)
# ─────────────────────────────────────────────────────────────────────────────
def test_end_to_end():
    print("\n── End-to-End ──────────────────────────────────")
    engine = QueryEngine(data_dir="data")

    # SELECT *
    r = engine.query("SELECT * FROM users")
    check("SELECT * users → 10 rows",   len(r) == 10)

    # WHERE numeric
    r = engine.query("SELECT * FROM users WHERE age > 30")
    check("age > 30 → 4 rows",          len(r) == 4)
    check("all ages > 30",              all(row["age"] > 30 for row in r))

    # WHERE string equality
    r = engine.query("SELECT * FROM users WHERE city = 'Mumbai'")
    check("city = Mumbai → 3 rows",     len(r) == 3)

    # SELECT cols + WHERE
    r = engine.query("SELECT name, salary FROM users WHERE department = 'Engineering'")
    check("Eng dept → 4 rows",          len(r) == 4)
    check("only name+salary cols",      set(r[0].keys()) == {"name", "salary"})

    # ORDER BY DESC
    r = engine.query("SELECT name, salary FROM users ORDER BY salary DESC")
    salaries = [row["salary"] for row in r]
    check("salary ORDER BY DESC",       salaries == sorted(salaries, reverse=True))

    # ORDER BY ASC
    r = engine.query("SELECT * FROM users ORDER BY age ASC")
    ages = [row["age"] for row in r]
    check("age ORDER BY ASC",           ages == sorted(ages))

    # GROUP BY
    r = engine.query("SELECT * FROM users GROUP BY department")
    departments = {row["department"] for row in r}
    check("GROUP BY dept → 4 groups",   len(r) == 4)
    check("Eng appears in groups",      "Engineering" in departments)

    # WHERE + ORDER BY
    r = engine.query("SELECT name, salary FROM users WHERE age >= 30 ORDER BY salary DESC")
    check("age>=30 + salary desc",      len(r) > 0)
    if len(r) > 1:
        check("result is sorted",       r[0]["salary"] >= r[1]["salary"])

    # products table
    r = engine.query("SELECT * FROM products WHERE price > 10000")
    check("products price > 10000",     all(row["price"] > 10000 for row in r))

    r = engine.query("SELECT * FROM products GROUP BY category")
    cats = {row["category"] for row in r}
    check("products GROUP BY category", "Electronics" in cats and "Furniture" in cats)

    # orders table
    r = engine.query("SELECT * FROM orders WHERE status = 'delivered'")
    check("delivered orders",           all(row["status"] == "delivered" for row in r))

    r = engine.query("SELECT * FROM orders ORDER BY amount DESC")
    amounts = [row["amount"] for row in r]
    check("orders ORDER BY amount DESC", amounts == sorted(amounts, reverse=True))

    # Table listing
    tables = engine.tables()
    check("tables() finds csvs",        len(tables) >= 3)

    # Error handling
    check_raises("bad table",           FileNotFoundError, engine.query, "SELECT * FROM nope")
    check_raises("bad syntax",          SyntaxError,       engine.query, "SELECT FROM users")


# ─────────────────────────────────────────────────────────────────────────────
# RUNNER
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 52)
    print("  MINI QUERY ENGINE — TEST SUITE")
    print("=" * 52)

    test_type_inference()
    test_parser()
    test_filter()
    test_aggregator()
    test_executor()
    test_loader()
    test_end_to_end()

    total = results["passed"] + results["failed"]
    print("\n" + "=" * 52)
    print(f"  Results: {results['passed']}/{total} passed", end="")
    if results["failed"] > 0:
        print(f"  |  {results['failed']} FAILED")
    else:
        print("  — all passed")
    print("=" * 52 + "\n")
