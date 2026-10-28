"""Pydantic models for vLLM structured output (GuidedDecodingParams)."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AnswerType(str, Enum):
    """Valid answer types per the DataMate problem contract."""
    number = "number"
    percent = "percent"
    string = "string"
    date = "date"
    boolean = "boolean"
    list = "list"
    table = "table"
    unanswerable = "unanswerable"
    abstain = "abstain"


class LLMResponse(BaseModel):
    """Structured output schema enforced by vLLM GuidedDecodingParams.

    The LLM is forced to emit valid JSON matching this schema on every call,
    eliminating output-parsing failures entirely.
    """
    thinking: str = Field(
        description=(
            "Brief chain-of-thought reasoning: what the question asks, "
            "which tables/columns are relevant, and the computation plan."
        ),
    )
    answer_type: AnswerType = Field(
        description="The answer type that matches the question.",
    )
    sql: Optional[str] = Field(
        default=None,
        description=(
            "A DuckDB SQL query that computes the answer. "
            "Must be null when answer_type is unanswerable or abstain."
        ),
    )
    reason: Optional[str] = Field(
        default=None,
        description=(
            "Short explanation when answer_type is unanswerable "
            "(e.g., missing columns, data outside range). Null otherwise."
        ),
    )
