# Mini Query Engine

A SQL-like query engine that runs on CSV files — built with **pure Python**, no pandas, no databases.

---

## Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![OOP](https://img.shields.io/badge/OOP-Design-6A1B9A?style=flat&logoColor=white)
![CSV](https://img.shields.io/badge/Data-CSV-2E7D32?style=flat&logoColor=white)

---

## Current Focus

🛠️ **Currently working on:** `LIMIT` support for query output pagination.

---

## Features

- `SELECT` specific columns or `*`
- `WHERE` clause with operators: `=` `!=` `>` `<` `>=` `<=`
- `ORDER BY` with `ASC` / `DESC`
- `GROUP BY` with `COUNT`
- Automatic type inference — numbers compare numerically, not as strings
- Descriptive errors for malformed queries or missing columns
- Interactive REPL mode

> **Note:** Single-condition WHERE only — no AND/OR or subqueries yet

---

## Run with Docker (Recommended)

> **Prerequisite:** [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running.

**1. Clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/mini-query-engine.git
cd mini-query-engine
```

**2. Build the image:**
```bash
docker compose build
```

**3. Start the interactive REPL:**
```bash
docker compose run --rm repl
```

**4. Run the full test suite (73/73 tests):**
```bash
docker compose run --rm tests
```

> No Python installation required — Docker handles everything.

---

## Example Queries

Once inside the REPL (`sql>`), try these:

```sql
SELECT * FROM users
SELECT name, salary FROM users WHERE age > 30
SELECT * FROM users WHERE city = 'Mumbai'
SELECT * FROM users ORDER BY salary DESC
SELECT * FROM users GROUP BY department
SELECT name, salary FROM users WHERE age >= 30 ORDER BY salary DESC
```

Type `exit` to quit the REPL.

---

## Run from Source (Alternative)

If you prefer running without Docker:

1. Make sure you have **Python 3.x** installed — no external dependencies
2. Run the interactive REPL:
```bash
python main.py
```
3. Run the test suite:
```bash
python tests/test_engine.py
```

---

## Project Structure

```
mini-query-engine/
├── engine/
│   ├── parser.py         # Tokenizes SQL string into structured dict
│   ├── executor.py       # Orchestrates the full query pipeline
│   ├── filter.py         # WHERE clause evaluation with type coercion
│   └── aggregator.py     # GROUP BY + COUNT logic
├── loader.py             # CSV reading + automatic type inference
├── main.py               # Public QueryEngine API + REPL
├── data/
│   ├── users.csv         # Sample dataset
│   ├── products.csv      # Sample dataset
│   └── orders.csv        # Sample dataset
├── tests/
│   └── test_engine.py    # Full test suite (73 tests, no external dependencies)
├── Dockerfile
├── docker-compose.yml
└── .dockerignore
```

---

## Design Decisions

**Why not use pandas?**
`pandas` `read_csv()` + `df.query()` is 3 lines. The goal was to implement the filtering, sorting, and projection logic myself — to understand how data processing actually works under the hood.

**Why separate `parser.py` and `executor.py`?**
Parsing (understanding the query) and execution (running it) are two different concerns. Keeping them separate means either can be swapped or extended independently — and it mirrors how real database engines are architected.

**Why `WHERE 1=1` pattern avoided here?**
Unlike the Task Manager API (where dynamic SQL string building is appropriate), here the WHERE clause is fully parsed into a structured dict first. The executor never builds raw query strings — it works on data structures, which is cleaner and safer.

**What I'd add with more time:**
- `AND` / `OR` support in WHERE using a recursive descent parser
- `JOIN` across two CSVs using a hash-join approach for O(n+m) performance
- `LIMIT` and `OFFSET` for pagination

---

## License

Free to use for learning and personal purposes.
