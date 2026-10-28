"""Safe SQL execution against DuckDB with as_of_date variable injection."""

from typing import Any

import duckdb


def execute_sql(
    conn: duckdb.DuckDBPyConnection,
    sql: str,
    as_of_date: str,
) -> dict[str, Any]:
    """Execute a DuckDB SQL query and return columns + rows.

    Sets the ``as_of_date`` session variable before execution so that
    queries can reference it via ``getvariable('as_of_date')``.

    Returns
    -------
    dict with keys ``columns`` (list[str]) and ``rows`` (list[list]).

    Raises
    ------
    Exception
        Any DuckDB execution error (syntax, missing table/column, etc.).
    """
    # Inject as_of_date as a session variable
    conn.execute(f"SET VARIABLE as_of_date = '{as_of_date}'")

    result = conn.execute(sql)
    columns = [desc[0] for desc in result.description]
    rows = result.fetchall()

    return {"columns": columns, "rows": [list(row) for row in rows]}
