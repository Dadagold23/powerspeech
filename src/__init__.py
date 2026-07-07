"""
src/__init__.py

Lazy imports — each class is only loaded when explicitly referenced.
This prevents heavy dependencies (whisper, torch, sounddevice) from
being imported just because another module in the package is needed.
"""

__all__ = [
    "SpeechToTextModule",
    "SummarizationModule",
    "StorageModule",
    "EvaluationModule",
]


def __getattr__(name):
    if name == "SpeechToTextModule":
        from .speech_to_text import SpeechToTextModule
        return SpeechToTextModule
    if name == "SummarizationModule":
        from .summarizer import SummarizationModule
        return SummarizationModule
    if name == "StorageModule":
        from .storage import StorageModule
        return StorageModule
    if name == "EvaluationModule":
        from .evaluator import EvaluationModule
        return EvaluationModule
    raise AttributeError(f"module 'src' has no attribute {name!r}")
