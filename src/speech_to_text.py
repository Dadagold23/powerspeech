"""
Speech-to-Text Module (speech_to_text.py)

Uses OpenAI Whisper — a pre-trained, multilingual automatic speech
recognition (ASR) model — to convert audio input to text.

Objective 1: Develop a speech-to-text module using a pre-trained AI model.

Author: [Your Name]
Date: 2026
"""

import os
import logging
import threading
import queue
import numpy as np
import whisper

# sounddevice and soundfile are only needed for live microphone recording.
# They are imported lazily inside the methods that use them so that
# file-based transcription works even when those packages are not installed.

logger = logging.getLogger(__name__)

# Default model from environment or fallback to 'base'
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "base")
AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", 16000))


class SpeechToTextModule:
    """
    Handles audio input (file or microphone) and transcribes speech to text
    using OpenAI Whisper.

    Attributes:
        model_name (str): Whisper model size (tiny/base/small/medium/large)
        model: Loaded Whisper model instance
    """

    def __init__(self, model_name: str = None):
        self.model_name = model_name or WHISPER_MODEL_NAME
        self.model = None
        self._recording = False
        self._audio_queue = queue.Queue()
        logger.info(f"SpeechToTextModule initialized with model: '{self.model_name}'")

    def load_model(self):
        """Load the Whisper model (lazy loading to save memory)."""
        if self.model is None:
            logger.info(f"Loading Whisper model '{self.model_name}'...")
            self.model = whisper.load_model(self.model_name)
            logger.info("Whisper model loaded successfully.")
        return self.model

    def load_audio(self, file_path: str, sr: int = 16000) -> np.ndarray:
        """
        Loads an audio file and converts it to a 16kHz mono waveform.
        Attempts to use soundfile (no FFmpeg dependency) for WAV, and falls back to
        FFmpeg/Whisper loader with clear error reporting if FFmpeg is missing.
        """
        import soundfile as sf
        import scipy.signal

        # Try reading with soundfile first (handles WAV natively without ffmpeg)
        try:
            data, samplerate = sf.read(file_path)
            # Convert to mono if stereo
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)

            # Resample to 16000 Hz if needed
            if samplerate != sr:
                num_samples = int(len(data) * sr / samplerate)
                data = scipy.signal.resample(data, num_samples)

            return data.astype(np.float32)
        except Exception as e:
            logger.info(f"soundfile failed to read {file_path}: {e}. Falling back to FFmpeg/Whisper loader.")

        # Fallback to standard whisper.load_audio (which requires ffmpeg)
        try:
            return whisper.load_audio(file_path, sr=sr)
        except FileNotFoundError as e:
            if getattr(e, "winerror", None) == 2 or e.errno == 2:
                raise RuntimeError(
                    "FFmpeg is not installed or not found in system PATH.\n"
                    "Please install FFmpeg to transcribe compressed formats (MP3/M4A/OGG/etc.).\n"
                    "Alternatively, upload a WAV file which is supported natively."
                ) from e
            raise

    def transcribe(self, audio_path: str, language: str = None) -> dict:
        """
        Transcribe an audio file to text.

        Args:
            audio_path (str): Path to the audio file (.wav, .mp3, .m4a, .ogg)
            language (str): Optional language code (e.g., 'en', 'fr', 'es')

        Returns:
            dict: {
                'text': Full transcript string,
                'segments': List of segment dicts with timestamps,
                'language': Detected language
            }
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        model = self.load_model()
        logger.info(f"Transcribing file: {audio_path}")

        options = {}
        if language:
            options["language"] = language

        # Load audio natively (WAV) or via standard ffmpeg fallback
        audio = self.load_audio(audio_path, sr=AUDIO_SAMPLE_RATE)

        result = model.transcribe(audio, **options)

        logger.info(f"Transcription complete. Language detected: {result.get('language')}")
        logger.debug(f"Transcript: {result['text'][:100]}...")

        return {
            "text": result["text"].strip(),
            "segments": result.get("segments", []),
            "language": result.get("language", "unknown")
        }

    def start_recording(self, duration: int = 30, callback=None):
        """
        Record audio from the microphone for a given duration.

        Args:
            duration (int): Recording duration in seconds
            callback (callable): Optional callback called when recording ends

        Returns:
            numpy.ndarray: Recorded audio array
        """
        try:
            import sounddevice as sd
        except ImportError:
            raise ImportError(
                "sounddevice is required for microphone recording. "
                "Install it with: pip install sounddevice"
            )

        self._recording = True
        logger.info(f"Recording started ({duration}s)...")
        frames = []

        def audio_callback(indata, frame_count, time_info, status):
            if status:
                logger.warning(f"Audio status: {status}")
            frames.append(indata.copy())

        with sd.InputStream(
            samplerate=AUDIO_SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=audio_callback
        ):
            sd.sleep(duration * 1000)

        self._recording = False
        audio_array = np.concatenate(frames, axis=0).flatten()
        logger.info(f"Recording stopped. Captured {len(audio_array)} samples.")

        if callback:
            callback(audio_array)

        return audio_array

    def save_recording(self, audio_array: np.ndarray, output_path: str) -> str:
        """
        Save a recorded audio array to a WAV file.

        Args:
            audio_array: NumPy array of audio samples
            output_path (str): Target file path

        Returns:
            str: Path of saved audio file
        """
        try:
            import soundfile as sf
        except ImportError:
            raise ImportError(
                "soundfile is required to save recordings. "
                "Install it with: pip install soundfile"
            )

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        sf.write(output_path, audio_array, AUDIO_SAMPLE_RATE)
        logger.info(f"Recording saved to: {output_path}")
        return output_path

    def transcribe_from_array(self, audio_array: np.ndarray, language: str = None) -> dict:
        """
        Transcribe audio directly from a NumPy array (from live desktop recording).

        Args:
            audio_array: Float32 NumPy array of audio samples at 16 kHz
            language: Optional language code

        Returns:
            dict: Same structure as transcribe()
        """
        model = self.load_model()
        audio = audio_array.astype(np.float32)
        options = {}
        if language:
            options["language"] = language
        result = model.transcribe(audio, **options)
        return {
            "text": result["text"].strip(),
            "segments": result.get("segments", []),
            "language": result.get("language", "unknown")
        }

    def transcribe_from_bytes(self, audio_bytes: bytes, suffix: str = ".webm",
                              language: str = None) -> dict:
        """
        Transcribe raw audio bytes from a browser MediaRecorder recording.
        Writes bytes to a temp file then calls transcribe().

        Supported browser formats: .webm, .ogg, .wav, .mp4
        FFmpeg must be installed for Whisper to decode webm/ogg.

        Args:
            audio_bytes: Raw audio bytes from the browser
            suffix:      File extension matching the browser MIME type
            language:    Optional language code

        Returns:
            dict: Same structure as transcribe()
        """
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            return self.transcribe(tmp_path, language=language)
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    def get_supported_languages(self) -> list:
        """Return list of supported Whisper language codes."""
        return list(whisper.tokenizer.LANGUAGES.keys())
