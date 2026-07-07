"""
conftest.py — Shared pytest fixtures for all test modules.

Adds the project root and src/ directory to sys.path once, so every
test file can import from src.* without its own sys.path hack.
"""

import sys
import pytest
from pathlib import Path

# ── Path setup ───────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
_SRC  = _ROOT / "src"
for _p in [str(_ROOT), str(_SRC)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ── Shared sample data ───────────────────────────────────────────────

SAMPLE_TRANSCRIPT = (
    "Artificial intelligence is the simulation of human intelligence "
    "processes by machines, especially computer systems. Machine learning "
    "is a subset of AI that enables systems to learn from data."
)

SAMPLE_SUMMARY = (
    "AI simulates human intelligence in machines. "
    "Machine learning allows systems to learn from data."
)

SAMPLE_REFERENCE = (
    "Artificial intelligence simulates human thinking in computers. "
    "Machine learning is a core technique within AI."
)


@pytest.fixture
def sample_transcript():
    return SAMPLE_TRANSCRIPT


@pytest.fixture
def sample_summary():
    return SAMPLE_SUMMARY


@pytest.fixture
def sample_reference():
    return SAMPLE_REFERENCE


@pytest.fixture
def storage(tmp_path):
    """StorageModule backed by temp directories — used across test files."""
    from src.storage import StorageModule
    return StorageModule(
        transcripts_dir=str(tmp_path / "transcripts"),
        summaries_dir=str(tmp_path / "summaries")
    )


@pytest.fixture
def evaluator():
    """EvaluationModule instance."""
    from src.evaluator import EvaluationModule
    return EvaluationModule()

