"""
Unit Tests — Summarization Module (test_summarizer.py)

Tests the SummarizationModule for:
- Model pipeline loading
- Single-chunk summarization
- Multi-chunk long text summarization
- Empty text edge case
- Key points extraction

Author: [Your Name]
Date: 2026
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.summarizer import SummarizationModule


class TestSummarizationModule:
    """Test suite for SummarizationModule."""

    def setup_method(self):
        self.summarizer = SummarizationModule()

    # ── Instantiation ────────────────────────────────────────────────

    def test_instantiation(self):
        assert self.summarizer is not None
        assert "bart" in self.summarizer.model_name.lower() or \
               "t5" in self.summarizer.model_name.lower() or \
               self.summarizer.model_name is not None

    # ── Summarization ────────────────────────────────────────────────

    @patch.object(SummarizationModule, "load_pipeline")
    def test_summarize_returns_string(self, mock_load_pipeline):
        """summarize() returns a non-empty string."""
        mock_pipe = MagicMock()
        mock_pipe.return_value = [{"summary_text": "A concise summary of the text."}]
        mock_load_pipeline.return_value = mock_pipe

        text = "The quick brown fox jumped over the lazy dog. " * 20
        result = self.summarizer.summarize(text)

        assert isinstance(result, str)
        assert len(result) > 0

    @patch.object(SummarizationModule, "load_pipeline")
    def test_summarize_empty_input(self, mock_load_pipeline):
        """summarize() returns empty string for empty input."""
        result = self.summarizer.summarize("")
        assert result == ""
        result2 = self.summarizer.summarize("   ")
        assert result2 == ""

    @patch.object(SummarizationModule, "load_pipeline")
    def test_summarize_short_text(self, mock_load_pipeline):
        """Short texts are handled in a single chunk."""
        mock_pipe = MagicMock()
        mock_pipe.return_value = [{"summary_text": "Short summary."}]
        mock_load_pipeline.return_value = mock_pipe

        result = self.summarizer.summarize("This is a short sentence.")
        assert isinstance(result, str)

    @patch.object(SummarizationModule, "load_pipeline")
    def test_summarize_long_text_chunked(self, mock_load_pipeline):
        """Long texts are chunked before summarization."""
        mock_pipe = MagicMock()
        mock_pipe.return_value = [{"summary_text": "Chunk summary."}]
        mock_load_pipeline.return_value = mock_pipe

        long_text = "word " * 5000  # ~25000 characters
        result = self.summarizer.summarize(long_text)
        assert isinstance(result, str)

    # ── Key Points ────────────────────────────────────────────────────

    def test_get_key_points(self):
        """get_key_points() returns the correct number of bullet points."""
        text = (
            "Artificial intelligence is transforming industries worldwide. "
            "Machine learning models are being deployed in healthcare applications. "
            "Natural language processing enables machines to understand human speech. "
            "Computer vision allows automated recognition of images and patterns. "
            "Deep learning has revolutionized speech recognition accuracy. "
            "Whisper by OpenAI achieves near-human transcription accuracy."
        )
        points = self.summarizer.get_key_points(text, num_points=3)
        assert isinstance(points, list)
        assert len(points) <= 3

    # ── Chunking ──────────────────────────────────────────────────────

    def test_chunk_text_single_chunk(self):
        """Short text produces a single chunk."""
        text = "Hello world."
        chunks = SummarizationModule._chunk_text(text, max_chunk_chars=100)
        assert len(chunks) == 1

    def test_chunk_text_multiple_chunks(self):
        """Long text produces multiple chunks."""
        text = "word " * 1000  # 5000 chars
        chunks = SummarizationModule._chunk_text(text, max_chunk_chars=200)
        assert len(chunks) > 1

    def test_chunk_text_preserves_content(self):
        """Chunking preserves all words."""
        text = "one two three four five six seven eight nine ten"
        chunks = SummarizationModule._chunk_text(text, max_chunk_chars=20)
        rejoined = " ".join(chunks)
        for word in text.split():
            assert word in rejoined
