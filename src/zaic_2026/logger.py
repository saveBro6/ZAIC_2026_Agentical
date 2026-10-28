"""Per-question trace logging for debugging and optimization."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def write_log(
    logs_dir: str,
    question_id: str,
    question: dict,
    elapsed: float,
    llm_output: Optional[str] = None,
    sql: Optional[str] = None,
    sql_result: Any = None,
    sql_error: Optional[str] = None,
    answer_entry: Optional[dict] = None,
    error: Optional[str] = None,
) -> None:
    """Write a detailed JSON log file for a single question.

    Logs are written to ``<logs_dir>/<question_id>.json`` and include the
    full diagnostic trace required by the competition contract (§8.2):
    question ID, predicted answer & type, elapsed time, generated SQL,
    intermediate execution outputs, and error traces.
    """
    log_path = Path(logs_dir) / f"{question_id}.json"

    entry = {
        "question_id": question_id,
        "business_id": question.get("business_id"),
        "question_text": question.get("question"),
        "as_of_date": question.get("as_of_date"),
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed, 3),
        "llm_raw_output": llm_output,
        "generated_sql": sql,
        "sql_result_preview": _safe_preview(sql_result),
        "sql_error": sql_error,
        "final_answer": answer_entry,
        "pipeline_error": error,
    }

    log_path.write_text(
        json.dumps(entry, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def _safe_preview(obj: Any, max_len: int = 2000) -> Optional[str]:
    """Truncate large results for the log file."""
    if obj is None:
        return None
    text = str(obj)
    if len(text) > max_len:
        return text[:max_len] + "... [truncated]"
    return text
