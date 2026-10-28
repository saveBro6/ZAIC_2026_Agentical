"""ZAIC 2026 DataMate baseline solution package."""


def main() -> None:
    """Lazy entrypoint to avoid importing torch/vllm on package import."""
    from .main import main as _main
    _main()


__all__ = ["main"]

