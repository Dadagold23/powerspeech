"""
Unit Tests — Speech-to-Text Module (test_speech_to_text.py)

Tests the SpeechToTextModule for:
- Model loading
- File-based transcription
- Array-based transcription
- Missing file error handling
- Language detection

Author: [Your Name]
Date: 2026
"""

import os
import sys
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.speech_to_text import SpeechToTextModule


class TestSpeechToTextModule:
    """Test suite for SpeechToTextModule."""

    def setup_method(self):
        """Instantiate module before each test."""
        self.stt = SpeechToTextModule(model_name="tiny")

    # ── Model Loading ────────────────────────────────────────────────

    def test_instantiation(self):
        """Module can be instantiated."""
        assert self.stt is not None
        assert self.stt.model_name == "tiny"

    @patch("src.speech_to_text.whisper.load_model")
    def test_load_model(self, mock_load):
        """Model is loaded exactly once (lazy loading)."""
        mock_load.return_value = MagicMock()
        model_1 = self.stt.load_model()
        model_2 = self.stt.load_model()
        mock_load.assert_called_once()
        assert model_1 is model_2

    # ── File Transcription ────────────────────────────────────────────

    @patch("src.speech_to_text.whisper.load_model")
    @patch.object(SpeechToTextModule, "load_audio")
    def test_transcribe_returns_dict(self, mock_load_audio, mock_load, tmp_path):
        """Transcribe returns a dict with text, segments, language."""
        # Create a dummy audio file
        dummy_audio = tmp_path / "test.wav"
        dummy_audio.write_bytes(b"\x00" * 1024)

        mock_load_audio.return_value = np.zeros(16000, dtype=np.float32)

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Hello world this is a test.",
            "segments": [{"start": 0.0, "end": 2.5, "text": "Hello world"}],
            "language": "en"
        }
        mock_load.return_value = mock_model

        result = self.stt.transcribe(str(dummy_audio))

        assert isinstance(result, dict)
        assert "text" in result
        assert "segments" in result
        assert "language" in result
        assert result["text"] == "Hello world this is a test."
        assert result["language"] == "en"

    def test_transcribe_missing_file_raises(self):
        """Transcribe raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            self.stt.transcribe("non_existent_audio.wav")

    @patch("src.speech_to_text.whisper.load_model")
    @patch.object(SpeechToTextModule, "load_audio")
    def test_transcribe_with_language_hint(self, mock_load_audio, mock_load, tmp_path):
        """Language hint is passed to Whisper model."""
        dummy_audio = tmp_path / "test.wav"
        dummy_audio.write_bytes(b"\x00" * 1024)

        mock_load_audio.return_value = np.zeros(16000, dtype=np.float32)

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Bonjour le monde.",
            "segments": [],
            "language": "fr"
        }
        mock_load.return_value = mock_model

        result = self.stt.transcribe(str(dummy_audio), language="fr")
        mock_model.transcribe.assert_called_once()
        call_kwargs = mock_model.transcribe.call_args[1]
        assert call_kwargs.get("language") == "fr"

    # ── Array Transcription ────────────────────────────────────────────

    @patch("src.speech_to_text.whisper.load_model")
    def test_transcribe_from_array(self, mock_load):
        """transcribe_from_array handles NumPy float32 arrays."""
        audio_array = np.zeros(16000, dtype=np.float32)
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Test audio array",
            "segments": [],
            "language": "en"
        }
        mock_load.return_value = mock_model

        result = self.stt.transcribe_from_array(audio_array)
        assert result["text"] == "Test audio array"

    # ── Save Recording ────────────────────────────────────────────────

    def test_save_recording(self, tmp_path):
        """save_recording writes a WAV file."""
        import soundfile as sf
        audio_array = np.zeros(16000, dtype=np.float32)
        output_path = str(tmp_path / "output.wav")
        saved = self.stt.save_recording(audio_array, output_path)
        assert os.path.exists(saved)

    # ── Language Support ──────────────────────────────────────────────

    @patch("src.speech_to_text.whisper.tokenizer")
    def test_get_supported_languages(self, mock_tokenizer):
        """Returns a list of language codes."""
        mock_tokenizer.LANGUAGES = {"en": "English", "fr": "French"}
        langs = self.stt.get_supported_languages()
        assert isinstance(langs, list)
