"""Main orchestrator for the DataMate (ZAIC 2026) baseline solution.

Pipeline:
Question -> LLM (Qwen2.5-7B-Instruct via vLLM) -> DuckDB SQL -> Execute -> Strict Format -> submission.jsonl

Meets all problem_contract specifications:
- Zero network access compatible
- Fast preloading of multi-format business data into DuckDB
- Conservative abstention policy (A Method: abstain on execution failure or empty result)
- Line-by-line submission flushing for crash and timeout resilience
- Per-question JSON logging in /result/logs/
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    src_dir = str(Path(__file__).resolve().parent.parent)
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    from zaic_2026.data_loader import load_business_data, preload_all_businesses
    from zaic_2026.executor import execute_sql
    from zaic_2026.formatter import format_answer
    from zaic_2026.llm_engine import generate_answer, init_engine
    from zaic_2026.logger import write_log
    from zaic_2026.prompt_builder import build_messages, load_system_prompt
    from zaic_2026.schemas import LLMResponse
else:
    from .data_loader import load_business_data, preload_all_businesses
    from .executor import execute_sql
    from .formatter import format_answer
    from .llm_engine import generate_answer, init_engine
    from .logger import write_log
    from .prompt_builder import build_messages, load_system_prompt
    from .schemas import LLMResponse



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DataMate ZAIC 2026 Baseline Solution",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="/data",
        help="Path to evaluation data directory containing rulebook.md, questions.jsonl, data/",
    )
    parser.add_argument(
        "--result-dir",
        type=str,
        default="/result",
        help="Path to output directory where submission.jsonl and logs/ are stored",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default="/app/models/Qwen2.5-7B-Instruct",
        help="Local path to model weights directory",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional: limit number of questions to process (for debugging)",
    )
    parser.add_argument(
        "--tensor-parallel-size",
        type=int,
        default=None,
        help="Tensor parallel size (default: auto 2 if >= 2 GPUs, else 1)",
    )
    parser.add_argument(
        "--gpu-memory-utilization",
        type=float,
        default=0.9,
        help="vLLM GPU memory utilization fraction (default 0.9)",
    )
    return parser.parse_args()


def load_questions(questions_path: Path, limit: int | None = None) -> list[dict]:
    """Load question objects from questions.jsonl."""
    if not questions_path.exists():
        raise FileNotFoundError(f"Questions file not found: {questions_path}")

    questions = []
    with open(questions_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))
            if limit and len(questions) >= limit:
                break
    return questions


def load_rulebook(rulebook_path: Path) -> str:
    """Load the split-specific rulebook markdown."""
    if not rulebook_path.exists():
        print(f"Warning: rulebook file not found at {rulebook_path}, using empty rulebook.")
        return ""
    return rulebook_path.read_text(encoding="utf-8")


def main() -> None:
    args = parse_args()

    data_dir = Path(args.data_dir)
    result_dir = Path(args.result_dir)
    logs_dir = result_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    submission_path = result_dir / "submission.jsonl"

    questions_path = data_dir / "questions.jsonl"
    rulebook_path = data_dir / "rulebook.md"
    calendar_path = data_dir / "calendar.csv"

    questions = load_questions(questions_path, limit=args.limit)
    rulebook_text = load_rulebook(rulebook_path)
    system_prompt = load_system_prompt()

    print(f"Loaded {len(questions)} questions from {questions_path}")
    print(f"Submission output: {submission_path}")
    print(f"Logs output: {logs_dir}")

    # 1. Preload business data into DuckDB memory cache
    business_cache = preload_all_businesses(str(data_dir), str(calendar_path))

    # 2. Initialize vLLM offline engine
    print(f"Initializing vLLM engine with model: {args.model_path}")
    engine = init_engine(
        model_path=args.model_path,
        tensor_parallel_size=args.tensor_parallel_size,
        gpu_memory_utilization=args.gpu_memory_utilization,
    )
    print("vLLM engine initialized successfully.")

    # 3. Process questions and stream results line-by-line
    total = len(questions)
    processed = 0

    processed_ids: set[str] = set()
    if submission_path.exists():
        with open(submission_path, "r", encoding="utf-8") as existing_file:
            for line in existing_file:
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        if "id" in record:
                            processed_ids.add(record["id"])
                    except Exception:
                        pass
        if processed_ids:
            print(f"Resuming: found {len(processed_ids)} already processed questions.")

    with open(submission_path, "a", encoding="utf-8") as submission_file:
        for q in questions:
            qid = q["id"]
            if qid in processed_ids:
                continue
            biz_id = q["business_id"]
            as_of_date = q["as_of_date"]
            processed += 1
            t_start = time.time()

            raw_llm_output: str | None = None
            generated_sql: str | None = None
            sql_result: Any = None
            sql_error: str | None = None
            pipeline_error: str | None = None
            submission_entry: dict[str, Any]

            try:
                # Retrieve or load business data
                if biz_id in business_cache:
                    conn, schema_text = business_cache[biz_id]
                else:
                    conn, schema_text = load_business_data(
                        biz_id, str(data_dir), str(calendar_path)
                    )
                    business_cache[biz_id] = (conn, schema_text)

                # Build messages and generate structured LLM response
                messages = build_messages(
                    question=q,
                    schema_text=schema_text,
                    rulebook_text=rulebook_text,
                    system_prompt=system_prompt,
                )
                raw_llm_output = generate_answer(engine, messages)

                # Parse structured JSON response
                parsed = LLMResponse.model_validate_json(raw_llm_output)
                target_type = parsed.answer_type.value
                generated_sql = parsed.sql

                if target_type == "unanswerable":
                    submission_entry = {
                        "id": qid,
                        "type": "unanswerable",
                        "reason": parsed.reason or "Không đủ dữ liệu để tính toán",
                    }
                elif target_type == "abstain" or not generated_sql:
                    # Deliberate refusal to avoid penalty
                    submission_entry = {"id": qid, "type": "abstain"}
                else:
                    # Execute generated SQL in DuckDB
                    try:
                        exec_res = execute_sql(conn, generated_sql, as_of_date)
                        sql_result = exec_res

                        # Format SQL result according to answer_type
                        formatted_val = format_answer(exec_res, target_type)

                        if formatted_val is None:
                            # A Method: Abstain if query returns no result or None
                            submission_entry = {"id": qid, "type": "abstain"}
                        else:
                            submission_entry = {
                                "id": qid,
                                "type": target_type,
                                "answer": formatted_val,
                            }
                    except Exception as sql_exc:
                        sql_error = str(sql_exc)
                        # A Method: Abstain on execution failure
                        submission_entry = {"id": qid, "type": "abstain"}

            except Exception as exc:
                pipeline_error = str(exc)
                submission_entry = {"id": qid, "type": "abstain"}

            elapsed = time.time() - t_start

            # Line-by-line append and flush immediately
            submission_file.write(
                json.dumps(submission_entry, ensure_ascii=False) + "\n"
            )
            submission_file.flush()

            # Write diagnostic trace log
            write_log(
                logs_dir=str(logs_dir),
                question_id=qid,
                question=q,
                elapsed=elapsed,
                llm_output=raw_llm_output,
                sql=generated_sql,
                sql_result=sql_result,
                sql_error=sql_error,
                answer_entry=submission_entry,
                error=pipeline_error,
            )

            print(
                f"[{processed}/{total}] {qid} ({biz_id}): "
                f"type={submission_entry.get('type')} "
                f"time={elapsed:.2f}s"
            )

    print("All questions completed.")


if __name__ == "__main__":
    main()
