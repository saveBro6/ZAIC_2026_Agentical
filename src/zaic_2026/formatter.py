"""Strict type-aware answer formatting per DataMate competition rules.

Each answer type has specific formatting requirements (§4 and §9 of the
rulebook).  This module converts raw SQL results into the exact JSON
values expected by the evaluation harness.
"""

import math
from typing import Any, Optional


def format_answer(
    sql_result: dict[str, Any],
    answer_type: str,
) -> Optional[Any]:
    """Convert a SQL result dict into the competition answer value.

    Parameters
    ----------
    sql_result : dict
        ``{"columns": [...], "rows": [[...], ...]}`` from executor.
    answer_type : str
        One of the valid competition answer types.

    Returns
    -------
    The formatted answer value, or None if the result is empty
    (caller should treat as abstain).
    """
    columns = sql_result["columns"]
    rows = sql_result["rows"]

    if answer_type == "number":
        return _format_number(rows)
    elif answer_type == "percent":
        return _format_percent(rows)
    elif answer_type == "string":
        return _format_string(rows)
    elif answer_type == "date":
        return _format_date(rows)
    elif answer_type == "boolean":
        return _format_boolean(rows)
    elif answer_type == "list":
        return _format_list(rows, columns)
    elif answer_type == "table":
        return _format_table(rows, columns)
    else:
        return None


def _format_number(rows: list) -> Optional[int]:
    """Number answers are integers (VND, counts, quantities)."""
    if not rows or rows[0][0] is None:
        return None
    val = rows[0][0]
    return int(round(float(val)))


def _format_percent(rows: list) -> Optional[float]:
    """Percent answers are rounded to exactly 2 decimal places."""
    if not rows or rows[0][0] is None:
        return None
    val = float(rows[0][0])
    if math.isnan(val) or math.isinf(val):
        return None
    return round(val, 2)


def _format_string(rows: list) -> Optional[str]:
    """String answers preserve the exact name from data."""
    if not rows or rows[0][0] is None:
        return None
    return str(rows[0][0])


def _format_date(rows: list) -> Optional[str]:
    """Date answers must be ISO ``YYYY-MM-DD`` or ``YYYY-MM``."""
    if not rows or rows[0][0] is None:
        return None
    raw = str(rows[0][0])
    # Handle datetime strings by taking only the date part
    if len(raw) >= 10 and raw[4] == "-" and raw[7] == "-":
        return raw[:10]
    if len(raw) == 7 and raw[4] == "-":
        return raw
    # Fallback: return first 10 chars
    return raw[:10]


def _format_boolean(rows: list) -> Optional[bool]:
    """Boolean answers must be JSON true/false."""
    if not rows or rows[0][0] is None:
        return None
    val = rows[0][0]
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes", "có")
    return bool(val)


def _format_list(rows: list, columns: list) -> Optional[list]:
    """List answers are ordered arrays of strings or numbers.

    Strategy:
    - Multiple rows × 1 column → list of those column values.
    - 1 row × multiple columns → list of those cell values.
    - Multiple rows × multiple columns → list of first-column values.
    """
    if not rows:
        return None

    if len(columns) == 1:
        # Each row contributes one element
        return [_format_cell(row[0]) for row in rows]
    elif len(rows) == 1:
        # Single row, multiple columns → list of cell values
        return [_format_cell(v) for v in rows[0]]
    else:
        # Multiple rows and columns → take first column
        return [_format_cell(row[0]) for row in rows]


def _format_table(
    rows: list, columns: list
) -> Optional[dict[str, Any]]:
    """Table answers have the shape ``{"columns": [...], "rows": [[...]]}``.

    Rows are evaluated as an unordered set by the harness, so ordering
    does not matter for scoring.
    """
    if not rows:
        return None

    formatted_rows = []
    for row in rows:
        formatted_rows.append([_format_cell(v) for v in row])

    return {"columns": columns, "rows": formatted_rows}


def _format_cell(val: Any) -> Any:
    """Format a single cell value for list/table answers."""
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, float):
        # Convert to int if it's a whole number (e.g., monetary amounts)
        if val == int(val) and not (math.isnan(val) or math.isinf(val)):
            return int(val)
        return val
    if isinstance(val, int):
        return val
    return str(val)
