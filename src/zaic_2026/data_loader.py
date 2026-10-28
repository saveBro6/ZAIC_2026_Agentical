"""Multi-format business data loading into DuckDB.

Handles CSV, XLSX (multi-sheet), and SQLite files. All data for a
single business is loaded into one in-memory DuckDB connection so the
LLM-generated SQL can query across tables seamlessly.
"""

import re
from pathlib import Path
from typing import Optional

import duckdb
import fastexcel
import polars as pl


def sanitize_table_name(name: str) -> str:
    """Convert a raw filename/sheet name into a clean DuckDB table identifier."""
    stem = Path(name).stem if "." in name else name
    sanitized = re.sub(r"[^\w]", "_", stem, flags=re.UNICODE)
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")
    if sanitized and sanitized[0].isdigit():
        sanitized = "t_" + sanitized
    return sanitized.lower()


def get_table_schema_text(
    conn: duckdb.DuckDBPyConnection,
    table_ref: str,
    max_sample: int = 3,
) -> str:
    """Return a human-readable schema description for *table_ref*.

    Includes column names/types, row count, and a few sample rows so the
    LLM has enough context to write correct SQL.
    """
    try:
        cols = conn.execute(f"DESCRIBE {table_ref}").fetchall()
        col_info = [(c[0], c[1]) for c in cols]

        count = conn.execute(f"SELECT COUNT(*) FROM {table_ref}").fetchone()[0]

        sample = conn.execute(
            f"SELECT * FROM {table_ref} LIMIT {max_sample}"
        ).fetchall()

        lines = [f"### Table: `{table_ref}` ({count:,} rows)"]
        lines.append("Columns:")
        for cname, ctype in col_info:
            lines.append(f"  - `{cname}` ({ctype})")

        if sample:
            headers = [c[0] for c in col_info]
            lines.append(f"\nSample ({len(sample)} rows):")
            lines.append("| " + " | ".join(h[:40] for h in headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
            for row in sample:
                cells = [
                    str(v)[:50] if v is not None else "NULL" for v in row
                ]
                lines.append("| " + " | ".join(cells) + " |")

        return "\n".join(lines)
    except Exception as exc:
        return f"### Table: `{table_ref}` (error reading schema: {exc})"


def _load_csv(
    conn: duckdb.DuckDBPyConnection,
    filepath: Path,
    schema_parts: list[str],
) -> None:
    """Load a single CSV file as a DuckDB table."""
    table_name = sanitize_table_name(filepath.stem)
    conn.execute(
        f'CREATE TABLE "{table_name}" AS '
        f"SELECT * FROM read_csv_auto('{filepath}', all_varchar=false)"
    )
    schema_parts.append(get_table_schema_text(conn, f'"{table_name}"'))


def _load_xlsx(
    conn: duckdb.DuckDBPyConnection,
    filepath: Path,
    schema_parts: list[str],
) -> None:
    """Load an XLSX file (all sheets) into DuckDB tables."""
    wb = fastexcel.read_excel(str(filepath))
    sheet_names = wb.sheet_names

    for sheet_name in sheet_names:
        if len(sheet_names) == 1:
            table_name = sanitize_table_name(filepath.stem)
        else:
            table_name = sanitize_table_name(f"{filepath.stem}__{sheet_name}")

        try:
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message=".*Could not determine dtype.*")
                df = pl.read_excel(str(filepath), sheet_name=sheet_name)
        except Exception:
            continue
        if df.height == 0:
            continue

        conn.execute(
            f'CREATE TABLE "{table_name}" AS SELECT * FROM df'
        )
        schema_parts.append(get_table_schema_text(conn, f'"{table_name}"'))


def _load_sqlite(
    conn: duckdb.DuckDBPyConnection,
    filepath: Path,
    schema_parts: list[str],
) -> None:
    """Attach a SQLite database and extract table schemas."""
    conn.execute(
        f"ATTACH '{filepath}' AS sqlite_db (TYPE SQLITE, READ_ONLY)"
    )
    tables = conn.execute(
        "SELECT name FROM sqlite_db.sqlite_master WHERE type='table'"
    ).fetchall()
    for (tname,) in tables:
        ref = f'sqlite_db."{tname}"'
        schema_parts.append(get_table_schema_text(conn, ref))


def load_business_data(
    business_id: str,
    data_dir: str,
    calendar_path: str,
) -> tuple[duckdb.DuckDBPyConnection, str]:
    """Load every data file for *business_id* into a fresh DuckDB instance.

    Returns
    -------
    conn : DuckDBPyConnection
        In-memory DuckDB connection with all tables loaded.
    schema_text : str
        Markdown-formatted schema description (README + tables) ready to
        be injected into the LLM prompt.
    """
    biz_dir = Path(data_dir) / "data" / business_id
    conn = duckdb.connect(database=":memory:")

    # Attempt to load SQLite extension gracefully (offline first)
    try:
        conn.execute("LOAD sqlite;")
    except Exception:
        try:
            conn.execute("INSTALL sqlite; LOAD sqlite;")
        except Exception:
            pass

    schema_parts: list[str] = []
    readme_text = ""

    # Business README
    readme_path = biz_dir / "README.md"
    if readme_path.exists():
        readme_text = readme_path.read_text(encoding="utf-8")

    # Calendar table (shared across all businesses in a split)
    cal = Path(calendar_path)
    if cal.exists():
        conn.execute(
            f"CREATE TABLE calendar AS "
            f"SELECT * FROM read_csv_auto('{cal}')"
        )
        schema_parts.append(get_table_schema_text(conn, "calendar"))

    # Process each data file in the business directory
    if biz_dir.exists():
        for fpath in sorted(biz_dir.iterdir()):
            if fpath.name == "README.md":
                continue
            try:
                if fpath.suffix == ".csv":
                    _load_csv(conn, fpath, schema_parts)
                elif fpath.suffix == ".xlsx":
                    _load_xlsx(conn, fpath, schema_parts)
                elif fpath.suffix in (".sqlite", ".sqlite3", ".db"):
                    _load_sqlite(conn, fpath, schema_parts)
            except Exception as exc:
                schema_parts.append(f"### Error loading `{fpath.name}`: {exc}")

    full_schema = (
        f"## Business Description\n{readme_text}\n\n"
        f"## Database Schema\n\n" + "\n\n".join(schema_parts)
    )
    return conn, full_schema


def preload_all_businesses(
    data_dir: str,
    calendar_path: str,
) -> dict[str, tuple[duckdb.DuckDBPyConnection, str]]:
    """Preload data for all businesses in data_dir into memory at startup."""
    cache: dict[str, tuple[duckdb.DuckDBPyConnection, str]] = {}
    biz_base_dir = Path(data_dir) / "data"
    if not biz_base_dir.exists():
        return cache

    biz_folders = sorted([d.name for d in biz_base_dir.iterdir() if d.is_dir()])
    print(f"Preloading {len(biz_folders)} businesses into memory...")
    for biz_id in biz_folders:
        try:
            conn, schema = load_business_data(biz_id, data_dir, calendar_path)
            cache[biz_id] = (conn, schema)
            print(f"  Loaded business {biz_id}")
        except Exception as exc:
            print(f"  Warning: failed to preload business {biz_id}: {exc}")
    print("Preloading complete.")
    return cache
