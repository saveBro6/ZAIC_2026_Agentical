"""vLLM offline engine wrapper with structured-output enforcement."""

from typing import Any, Optional

from .schemas import LLMResponse


def init_engine(
    model_path: str,
    tensor_parallel_size: Optional[int] = None,
    gpu_memory_utilization: float = 0.9,
    max_model_len: int = 32768,
) -> Any:
    """Initialise the vLLM engine for offline inference.

    Configuration notes
    -------------------
    * ``tensor_parallel_size`` defaults to 2 if 2+ GPUs are available,
      or matches available GPU count (supports 2x RTX 5090 evaluation environment).
    * ``dtype=bfloat16`` keeps full precision.
    * ``gpu_memory_utilization=0.9`` leaves headroom for DuckDB / system.
    * ``max_model_len=32768`` provides ample context for schema + rulebook + question.
    * ``trust_remote_code=True`` required for Qwen2.5 tokenizer.
    """
    import torch
    from vllm import LLM

    if tensor_parallel_size is None:
        gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 1
        tensor_parallel_size = min(2, max(1, gpu_count))

    return LLM(
        model=model_path,
        dtype="bfloat16",
        tensor_parallel_size=tensor_parallel_size,
        max_model_len=max_model_len,
        gpu_memory_utilization=gpu_memory_utilization,
        trust_remote_code=True,
    )


def generate_answer(engine: Any, messages: list[dict]) -> str:
    """Run a single structured-output generation.

    Parameters
    ----------
    engine : LLM
        The initialised vLLM engine.
    messages : list[dict]
        Chat messages ``[{"role": ..., "content": ...}, ...]``.

    Returns
    -------
    str
        Raw JSON text conforming to the ``LLMResponse`` schema.
    """
    from vllm import SamplingParams

    schema_json = LLMResponse.model_json_schema()

    try:
        from vllm.sampling_params import StructuredOutputsParams
        struct_params = StructuredOutputsParams(json=schema_json)
        try:
            sampling_params = SamplingParams(
                temperature=0.0,
                max_tokens=2048,
                structured_outputs=struct_params,
            )
        except TypeError:
            sampling_params = SamplingParams(
                temperature=0.0,
                max_tokens=2048,
                guided_decoding=struct_params,
            )
    except ImportError:
        from vllm.sampling_params import GuidedDecodingParams
        guided_params = GuidedDecodingParams(json=schema_json)
        sampling_params = SamplingParams(
            temperature=0.0,
            max_tokens=2048,
            guided_decoding=guided_params,
        )

    tokenizer = engine.get_tokenizer()
    prompt_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    outputs = engine.generate([prompt_text], sampling_params=sampling_params)
    return outputs[0].outputs[0].text

