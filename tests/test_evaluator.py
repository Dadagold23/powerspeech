"""
Unit Tests — Evaluation Module (test_evaluator.py)

Tests the EvaluationModule for:
- Perfect transcription WER = 0
- Perfect summary ROUGE = 1
- Batch evaluation aggregation
- Report formatting

Author: [Your Name]
Date: 2026
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.evaluator import EvaluationModule


class TestEvaluationModule:
    """Test suite for EvaluationModule."""

    def setup_method(self):
        self.evaluator = EvaluationModule()

    # ── WER / CER ─────────────────────────────────────────────────────

    def test_perfect_transcription_wer_zero(self):
        """Identical reference and hypothesis gives WER = 0."""
        text = "the quick brown fox jumps over the lazy dog"
        result = self.evaluator.evaluate_transcription(text, text)
        assert result["WER"] == pytest.approx(0.0, abs=0.01)

    def test_wrong_transcription_has_nonzero_wer(self):
        """Different reference and hypothesis gives WER > 0."""
        ref = "the quick brown fox"
        hyp = "the slow white cat"
        result = self.evaluator.evaluate_transcription(ref, hyp)
        assert result["WER"] > 0

    def test_transcription_result_keys(self):
        """evaluate_transcription returns expected keys."""
        result = self.evaluator.evaluate_transcription("hello world", "hello world")
        assert "WER" in result
        assert "CER" in result
        assert "WER_pct" in result
        assert "CER_pct" in result

    # ── ROUGE ─────────────────────────────────────────────────────────

    def test_perfect_summary_rouge_one(self):
        """Identical texts give ROUGE-1 F = 1.0."""
        text = "artificial intelligence enables computers to learn from data"
        result = self.evaluator.evaluate_summarization(text, text)
        assert result["ROUGE-1"]["fmeasure"] == pytest.approx(1.0, abs=0.01)

    def test_different_summary_rouge_below_one(self):
        """Different texts give ROUGE-1 F < 1.0."""
        ref = "Artificial intelligence transforms industries globally."
        hyp  = "Machine learning is a subset of computer science."
        result = self.evaluator.evaluate_summarization(ref, hyp)
        assert result["ROUGE-1"]["fmeasure"] < 1.0

    def test_summarization_result_keys(self):
        """evaluate_summarization returns ROUGE-1, ROUGE-2, ROUGE-L."""
        result = self.evaluator.evaluate_summarization("test sentence", "test sentence")
        for key in ["ROUGE-1", "ROUGE-2", "ROUGE-L"]:
            assert key in result
            assert "precision" in result[key]
            assert "recall" in result[key]
            assert "fmeasure" in result[key]

    # ── Batch Evaluation ──────────────────────────────────────────────

    def test_batch_evaluation_aggregation(self, tmp_path):
        """Batch evaluation computes averages correctly."""
        cases = [
            {
                "audio_file": "audio_01.wav",
                "reference_transcript": "hello world",
                "hypothesis_transcript": "hello world",
                "reference_summary": "greeting message",
                "generated_summary": "greeting message"
            },
            {
                "audio_file": "audio_02.wav",
                "reference_transcript": "the quick fox",
                "hypothesis_transcript": "the quick fox",
                "reference_summary": "fox description",
                "generated_summary": "fox description"
            }
        ]
        report_path = str(tmp_path / "report.json")
        results = self.evaluator.run_batch_evaluation(cases, report_path=report_path)

        assert results["total_cases"] == 2
        assert results["avg_WER"] == pytest.approx(0.0, abs=0.01)
        assert results["avg_ROUGE1_F"] == pytest.approx(1.0, abs=0.01)
        assert Path(report_path).exists()

    # ── Report Formatting ─────────────────────────────────────────────

    def test_format_report_returns_string(self):
        """format_report returns a non-empty string."""
        data = {
            "total_cases": 3,
            "avg_WER": 0.045,
            "avg_CER": 0.021,
            "avg_ROUGE1_F": 0.81,
            "avg_ROUGE2_F": 0.65,
            "avg_ROUGEL_F": 0.77,
            "evaluated_at": "2026-07-01T12:00:00",
            "detailed": []
        }
        report = self.evaluator.format_report(data)
        assert isinstance(report, str)
        assert "WER" in report
        assert "ROUGE" in report
