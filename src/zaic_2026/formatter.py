"""Strict type-aware answer formatting per DataMate competition rules.

Each answer type has specific formatting requirements (§4 and §9 of the
rulebook). This module converts raw SQL results into the exact JSON
values expected by the evaluation harness.
"""

from datetime import date, datetime
from decimal import Decimal
import math
import re
from typing import Any, Optional, Union
import unicodedata


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


def _format_number(rows: list) -> Optional[Union[int, float]]:
    """Number answers are integers (VND, counts) or rounded to 2 decimal places."""
    if not rows or rows[0][0] is None:
        return None
    try:
        val = float(rows[0][0])
    except (ValueError, TypeError):
        return None
    if math.isnan(val) or math.isinf(val):
        return None
    if val.is_integer():
        return int(val)
    return round(val, 2)


def _format_percent(rows: list) -> Optional[float]:
    """Percent answers are rounded to exactly 2 decimal places."""
    if not rows or rows[0][0] is None:
        return None
    try:
        val = float(rows[0][0])
    except (ValueError, TypeError):
        return None
    if math.isnan(val) or math.isinf(val):
        return None
    return round(val, 2)


def _format_string(rows: list) -> Optional[str]:
    """String answers preserve the exact name with NFC Unicode normalization."""
    if not rows or rows[0][0] is None:
        return None
    raw = str(rows[0][0])
    return unicodedata.normalize("NFC", raw).strip()


def _format_date(rows: list) -> Optional[str]:
    """Date answers must be ISO ``YYYY-MM-DD`` or ``YYYY-MM``."""
    if not rows or rows[0][0] is None:
        return None
    val = rows[0][0]

    # Handle native date/datetime objects from DuckDB
    if isinstance(val, (date, datetime)):
        return val.strftime("%Y-%m-%d")

    raw = str(val).strip()

    # Handle ISO YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}", raw):
        return raw[:10]

    # Handle ISO YYYY-MM
    if re.match(r"^\d{4}-\d{2}$", raw):
        return raw

    # Handle Vietnamese format DD/MM/YYYY or DD-MM-YYYY
    m = re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", raw)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{year:04d}-{month:02d}-{day:02d}"

    return raw[:10] if len(raw) >= 10 else raw


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
    if isinstance(val, Decimal):
        val_float = float(val)
        return int(val_float) if val_float.is_integer() else val_float
    if isinstance(val, float):
        if val == int(val) and not (math.isnan(val) or math.isinf(val)):
            return int(val)
        return val
    if isinstance(val, int):
        return val
    if isinstance(val, (date, datetime)):
        return val.strftime("%Y-%m-%d")
    return unicodedata.normalize("NFC", str(val)).strip()

