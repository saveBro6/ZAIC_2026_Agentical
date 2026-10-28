"""Prompt assembly for the DataMate Text-to-SQL baseline."""

from pathlib import Path
from typing import Optional


def load_system_prompt(path: Optional[str] = None) -> str:
    """Load the system prompt markdown document."""
    if path and Path(path).exists():
        return Path(path).read_text(encoding="utf-8")
    
    default_path = Path(__file__).parent / "system_prompt.md"
    if default_path.exists():
        return default_path.read_text(encoding="utf-8")
    
    return "You are an analytical assistant generating DuckDB SQL for Vietnamese SMB questions."


def build_messages(
    question: dict,
    schema_text: str,
    rulebook_text: str,
    system_prompt: str,
) -> list[dict]:
    """Assemble chat messages for the LLM.

    Parameters
    ----------
    question : dict
        Dict with keys: id, business_id, question, as_of_date.
    schema_text : str
        Markdown documentation of the business data and database schemas.
    rulebook_text : str
        The split-specific rulebook markdown.
    system_prompt : str
        The base system instructions.

    Returns
    -------
    list[dict]
        Messages in the standard OpenAI chat format.
    """
    user_content = (
        f"# BUSINESS DATA & DATABASE SCHEMA\n\n"
        f"{schema_text}\n\n"
        f"---\n\n"
        f"# ACTIVE SPLIT RULEBOOK\n\n"
        f"{rulebook_text}\n\n"
        f"---\n\n"
        f"# QUESTION TO ANSWER\n"
        f"- **Question ID**: {question['id']}\n"
        f"- **Business ID**: {question['business_id']}\n"
        f"- **As-of Date (Virtual Today)**: {question['as_of_date']}\n"
        f"- **Question Text**: {question['question']}\n\n"
        f"Analyze the question, consult the active rulebook and table schema, "
        f"and output your reasoning, target answer_type, and DuckDB SQL query "
        f"in the requested JSON format."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
