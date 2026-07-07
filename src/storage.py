"""
Storage Module (storage.py)

Handles saving, loading, and managing transcripts and summaries.
Supports export to .txt and .json formats.

Objective 4: Enable storage of generated transcripts and summaries.

Author: [Your Name]
Date: 2026
"""

import os
import json
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

TRANSCRIPTS_DIR = os.getenv("TRANSCRIPTS_DIR", "data/transcripts")
SUMMARIES_DIR = os.getenv("SUMMARIES_DIR", "data/summaries")


class StorageModule:
    """
    Manages persistence of transcription and summarization outputs.

    Supports:
    - Save transcripts as .txt and .json
    - Save summaries as .txt
    - Load previous sessions
    - Export a complete session report
    """

    def __init__(
        self,
        transcripts_dir: str = None,
        summaries_dir: str = None
    ):
        self.transcripts_dir = Path(transcripts_dir or TRANSCRIPTS_DIR)
        self.summaries_dir = Path(summaries_dir or SUMMARIES_DIR)
        self._ensure_dirs()
        logger.info("StorageModule initialized.")

    def _ensure_dirs(self):
        """Create output directories if they don't exist."""
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        self.summaries_dir.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, prefix: str, extension: str) -> str:
        """Generate a timestamped filename with microseconds to avoid collisions."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"{prefix}_{timestamp}.{extension}"

    def save(
        self,
        audio_file: str,
        transcript: str,
        summary: Optional[str] = None,
        segments: Optional[list] = None,
        language: str = "unknown"
    ) -> dict:
        """
        Save a transcription session to disk.

        Args:
            audio_file (str): Source audio file path
            transcript (str): Full transcription text
            summary (str): Optional summary text
            segments (list): Optional list of timestamped segments
            language (str): Detected language

        Returns:
            dict: Paths of saved files
        """
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        saved_paths = {}

        # --- Save transcript as .txt ---
        txt_name = f"transcript_{session_id}.txt"
        txt_path = self.transcripts_dir / txt_name
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"AI Speech-to-Text Transcript\n")
            f.write(f"{'=' * 40}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source: {audio_file}\n")
            f.write(f"Language: {language}\n")
            f.write(f"{'=' * 40}\n\n")
            f.write(transcript)
        saved_paths["transcript_txt"] = str(txt_path)
        logger.info(f"Transcript saved: {txt_path}")

        # --- Save full session as .json ---
        json_name = f"session_{session_id}.json"
        json_path = self.transcripts_dir / json_name
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "audio_source": audio_file,
            "language": language,
            "transcript": transcript,
            "summary": summary,
            "segments": segments or []
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=4, ensure_ascii=False)
        saved_paths["session_json"] = str(json_path)
        logger.info(f"Session JSON saved: {json_path}")

        # --- Save summary if provided ---
        if summary:
            sum_name = f"summary_{session_id}.txt"
            sum_path = self.summaries_dir / sum_name
            with open(sum_path, "w", encoding="utf-8") as f:
                f.write(f"AI-Generated Summary\n")
                f.write(f"{'=' * 40}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Source: {audio_file}\n")
                f.write(f"{'=' * 40}\n\n")
                f.write(summary)
            saved_paths["summary_txt"] = str(sum_path)
            logger.info(f"Summary saved: {sum_path}")

        return saved_paths

    def load_session(self, json_path: str) -> dict:
        """
        Load a previously saved session from a JSON file.

        Args:
            json_path (str): Path to session JSON file

        Returns:
            dict: Session data
        """
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Session loaded: {json_path}")
        return data

    def list_sessions(self) -> list:
        """
        List all saved session JSON files.

        Returns:
            list: List of session metadata dicts (id, date, source)
        """
        sessions = []
        for json_file in sorted(self.transcripts_dir.glob("session_*.json"), reverse=True):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append({
                    "file": str(json_file),
                    "session_id": data.get("session_id"),
                    "created_at": data.get("created_at"),
                    "source": data.get("audio_source"),
                    "language": data.get("language")
                })
            except Exception as e:
                logger.warning(f"Could not load {json_file}: {e}")
        return sessions

    def export_csv(self, output_path: str = None) -> str:
        """
        Export all sessions to a CSV summary file.

        Args:
            output_path (str): Target CSV file path

        Returns:
            str: Path of created CSV file
        """
        sessions = self.list_sessions()
        if not sessions:
            logger.warning("No sessions to export.")
            return None

        csv_path = output_path or str(self.transcripts_dir / "sessions_export.csv")
        fieldnames = ["session_id", "created_at", "source", "language", "file"]

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sessions)

        logger.info(f"CSV export saved: {csv_path}")
        return csv_path

    def delete_session(self, session_id: str) -> bool:
        """
        Delete all files associated with a session.

        Args:
            session_id (str): Session ID (timestamp string)

        Returns:
            bool: True if deleted successfully
        """
        deleted = False
        patterns = [
            self.transcripts_dir / f"session_{session_id}.json",
            self.transcripts_dir / f"transcript_{session_id}.txt",
            self.summaries_dir / f"summary_{session_id}.txt"
        ]
        for path in patterns:
            if path.exists():
                path.unlink()
                logger.info(f"Deleted: {path}")
                deleted = True
        return deleted
