"""Safe SQL execution against DuckDB with as_of_date variable injection and timeout."""

import threading
from typing import Any

import duckdb


def execute_sql(
    conn: duckdb.DuckDBPyConnection,
    sql: str,
    as_of_date: str,
    timeout_seconds: float = 20.0,
) -> dict[str, Any]:
    """Execute a DuckDB SQL query and return columns + rows.

    Sets the ``as_of_date`` session variable and enforces a strict statement
    timeout via ``conn.interrupt()`` to prevent runaway Cartesian joins.

    Returns
    -------
    dict with keys ``columns`` (list[str]) and ``rows`` (list[list]).

    Raises
    ------
    Exception
        Any DuckDB execution error (syntax, missing table/column, timeout, etc.).
    """
    # Inject as_of_date as a session variable
    conn.execute(f"SET VARIABLE as_of_date = '{as_of_date}'")

    timer = threading.Timer(timeout_seconds, conn.interrupt)
    timer.start()
    try:
        result = conn.execute(sql)
        columns = [desc[0] for desc in result.description] if result.description else []
        rows = result.fetchall() if result.description else []
        return {"columns": columns, "rows": [list(row) for row in rows]}
    finally:
        timer.cancel()

