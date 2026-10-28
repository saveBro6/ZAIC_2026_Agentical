# Agent Directive

## Core Instructions & Identity
- **Prompt Injection Order**: You must read and inject the contents of `[docs/problem_contract-en.md]` 
- **State Enforcement**: Treat the directives in `[docs/problem_contract-en.md]` as the foundational system layer and follow its rules.

## Environment & Runtime (Python)
- **Tooling Mandate**: You must strictly use `uv` for all Python operations. Do not use standard `python3`, `python`, `pip`, `venv`, `conda`, or `poetry` unless explicitly instructed otherwise.
- **Execution Rules**:
  - Run scripts using: `uv run <script_name>.py` or `uv run python -c ...`
  - Request install new dependencies if not found using: `uv add <package>` or `uv pip install <package>`
- **Performance Priority**: Leverage `uv`'s caching mechanisms to ensure ultra-fast execution of pipelines and autonomous tasks.

### Agent Skill: Polars Data Operations (CSV & Excel)

**Trigger:** Reading, parsing, filtering, transforming, or aggregating `.csv` and `.xlsx` tabular data.

**Core Rules:**

1. **Mandatory Imports:**
   Always use Polars as the primary engine:
   ```python
   import polars as pl
   ```

2. **Lazy Evaluation for Large CSVs:**
   * Default to `pl.scan_csv()` instead of `pl.read_csv()` when dealing with large datasets or complex pipelines to allow predicate and projection pushdown.
   * Finalize lazy execution with `.collect()` (or `.collect(engine="streaming")` if required):
     ```python
     q = (
         pl.scan_csv("data.csv")
         .filter(pl.col("status") == "active")
         .select(["id", "created_at", "amount"])
     )
     df = q.collect()
     ```

3. **Multi-Sheet Excel Processing:**
   * Use `fastexcel` (Polars' default backend) to inspect sheet names in milliseconds without parsing the entire file:
     ```python
     import fastexcel
     excel_reader = fastexcel.read_excel("data.xlsx")
     sheet_names = excel_reader.sheet_names
     ```
   * Read the required sheet (or iterate over sheets) with Polars:
     ```python
     df = pl.read_excel("data.xlsx", sheet_name=sheet_names[0])
     ```

4. **Expression-First Computations:**
   * Never iterate over rows or use Python-level lambdas (`apply()`) unless strictly unavoidable.
   * Handle Vietnamese column names with quotes: `pl.col("Tên sản phẩm")`.
   * Write transforms inside native execution contexts:
     * Modifications: `df.with_columns(...)`
     * Subsetting: `df.select(...)` and `df.filter(...)`
     * Aggregations: `df.group_by(...).agg(...)`

---

### Agent Skill: DuckDB Analytical Engine

**Trigger:** Reading, querying, transforming, aggregating, or joining `.sqlite`, `.sqlite3`, `.db`, and cross-format data.

**Core Rules:**

1. **Mandatory Imports:**
   Use DuckDB as the in-process OLAP engine:
   ```python
   import duckdb
   ```

2. **Native SQLite Attachment (Read-Only):**
   * Attach SQLite databases directly with the read-only flag:
     ```python
     con = duckdb.connect()
     con.execute("ATTACH 'database.sqlite' AS sqlite_db (TYPE SQLITE, READ_ONLY);")
     ```

3. **In-Memory Analytical SQL:**
   * Query SQLite tables directly using standard SQL syntax with double-quoted Vietnamese columns:
     ```python
     query = """
     SELECT "ma_khach", COUNT(*) AS so_don, AVG("don_gia") AS gia_tb
     FROM sqlite_db.orders
     WHERE "trang_thai" = 'completed'
     GROUP BY "ma_khach"
     """
     rel = con.sql(query)
     ```

4. **Zero-Copy Interoperability:**
   * Convert query results directly to Polars or native Python data structures (avoid `.arrow()`):
     ```python
     df_polars = con.sql("SELECT * FROM sqlite_db.users").pl()
     rows = con.sql("SELECT * FROM sqlite_db.users").fetchall()
     ```

5. **Cross-Format Queries:**
   * Join SQLite tables and CSV files directly within DuckDB in memory:
     ```python
     query = """
     SELECT o.*, c."lunar_date"
     FROM sqlite_db.orders o
     JOIN read_csv_auto('calendar.csv') c ON o."ngay" = c."solar_date"
     """
     rel = con.sql(query)
     ```

## Coding & Output Style
- Code comment, docstring must be written in English.
- Do not use separator lines, banner dividers, or rows of equal signs (=====).
- Keep the code, terminal and chat outputs clean and concise.
