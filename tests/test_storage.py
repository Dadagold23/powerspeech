"""
Unit Tests — Storage Module (test_storage.py)

Tests the StorageModule for:
- Directory creation
- Session save (txt, json)
- Session load
- Session listing
- CSV export
- Session deletion

Author: [Your Name]
Date: 2026
"""

import os
import sys
import json
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.storage import StorageModule

SAMPLE_TRANSCRIPT = (
    "Artificial intelligence is the simulation of human intelligence processes "
    "by machines, especially computer systems."
)
SAMPLE_SUMMARY = (
    "AI simulates human intelligence in computer systems."
)


class TestStorageModule:
    """Test suite for StorageModule."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Create StorageModule instance using temp directories."""
        return StorageModule(
            transcripts_dir=str(tmp_path / "transcripts"),
            summaries_dir=str(tmp_path / "summaries")
        )

    # ── Directory Creation ────────────────────────────────────────────

    def test_directories_created(self, tmp_path):
        """StorageModule creates output directories on init."""
        t_dir = tmp_path / "t"
        s_dir = tmp_path / "s"
        StorageModule(transcripts_dir=str(t_dir), summaries_dir=str(s_dir))
        assert t_dir.exists()
        assert s_dir.exists()

    # ── Save Session ──────────────────────────────────────────────────

    def test_save_transcript_creates_txt(self, storage, tmp_path):
        """Save creates a transcript .txt file."""
        paths = storage.save(
            audio_file="test.wav",
            transcript=SAMPLE_TRANSCRIPT
        )
        assert "transcript_txt" in paths
        assert os.path.exists(paths["transcript_txt"])

    def test_save_creates_json(self, storage):
        """Save creates a session .json file."""
        paths = storage.save(
            audio_file="test.wav",
            transcript=SAMPLE_TRANSCRIPT
        )
        assert "session_json" in paths
        assert os.path.exists(paths["session_json"])

    def test_save_with_summary_creates_summary_txt(self, storage):
        """Save creates a summary .txt file when summary provided."""
        paths = storage.save(
            audio_file="test.wav",
            transcript=SAMPLE_TRANSCRIPT,
            summary=SAMPLE_SUMMARY
        )
        assert "summary_txt" in paths
        assert os.path.exists(paths["summary_txt"])

    def test_save_without_summary_no_summary_file(self, storage):
        """Save does NOT create summary file when no summary provided."""
        paths = storage.save(
            audio_file="test.wav",
            transcript=SAMPLE_TRANSCRIPT,
            summary=None
        )
        assert "summary_txt" not in paths

    # ── Load Session ──────────────────────────────────────────────────

    def test_load_session_returns_correct_data(self, storage):
        """Loaded session contains expected keys and values."""
        paths = storage.save(
            audio_file="test.wav",
            transcript=SAMPLE_TRANSCRIPT,
            summary=SAMPLE_SUMMARY,
            language="en"
        )
        data = storage.load_session(paths["session_json"])
        assert data["transcript"] == SAMPLE_TRANSCRIPT
        assert data["summary"] == SAMPLE_SUMMARY
        assert data["language"] == "en"
        assert data["audio_source"] == "test.wav"

    # ── List Sessions ─────────────────────────────────────────────────

    def test_list_sessions_empty(self, storage):
        """Empty directory returns empty list."""
        sessions = storage.list_sessions()
        assert sessions == []

    def test_list_sessions_after_save(self, storage):
        """Listed sessions reflect saved sessions."""
        storage.save(audio_file="a.wav", transcript="First transcript")
        storage.save(audio_file="b.wav", transcript="Second transcript")
        sessions = storage.list_sessions()
        assert len(sessions) == 2

    # ── CSV Export ────────────────────────────────────────────────────

    def test_export_csv(self, storage, tmp_path):
        """CSV export creates a valid CSV file."""
        storage.save(audio_file="test.wav", transcript=SAMPLE_TRANSCRIPT)
        csv_path = str(tmp_path / "export.csv")
        result = storage.export_csv(output_path=csv_path)
        assert result is not None
        assert os.path.exists(result)

    def test_export_csv_no_sessions(self, storage):
        """CSV export returns None when no sessions exist."""
        result = storage.export_csv()
        assert result is None

    # ── Delete Session ─────────────────────────────────────────────────

    def test_delete_session(self, storage):
        """Deleted session files no longer exist."""
        paths = storage.save(audio_file="test.wav", transcript=SAMPLE_TRANSCRIPT)
        # Extract session ID from filename
        json_path = Path(paths["session_json"])
        session_id = json_path.stem.replace("session_", "")
        deleted = storage.delete_session(session_id)
        assert deleted is True
        assert not json_path.exists()
