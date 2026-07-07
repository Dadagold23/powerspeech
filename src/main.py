"""
AI-Powered Speech-to-Text Note-Taking & Summarization System
Entry Point (main.py)

Author: [Your Name]
Date: 2026
"""

import argparse
import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Ensure project root is on sys.path so both `python src/main.py`
# and `python -m src.main` resolve imports correctly.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
_SRC_DIR = str(Path(__file__).resolve().parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(_PROJECT_ROOT, "app.log")),
    ]
)
logger = logging.getLogger(__name__)


def run_gui():
    """Launch the Tkinter GUI application."""
    logger.info("Launching GUI application...")
    from ui.app_gui import SpeechNotesApp
    app = SpeechNotesApp()
    app.mainloop()


def run_cli(args):
    """Run the system in command-line mode."""
    from speech_to_text import SpeechToTextModule
    from summarizer import SummarizationModule
    from storage import StorageModule

    logger.info("Running in CLI mode...")

    stt = SpeechToTextModule()
    summarizer = SummarizationModule()
    storage = StorageModule()

    # Transcribe
    logger.info(f"Transcribing: {args.file}")
    transcript = stt.transcribe(args.file)
    print("\n=== TRANSCRIPT ===")
    print(transcript)

    # Summarize if requested
    if args.summarize:
        logger.info("Generating summary...")
        summary = summarizer.summarize(transcript)
        print("\n=== SUMMARY ===")
        print(summary)
    else:
        summary = None

    # Save output
    saved = storage.save(
        audio_file=args.file,
        transcript=transcript,
        summary=summary
    )
    logger.info(f"Saved to: {saved}")
    print(f"\n[Saved] => {saved}")


def main():
    parser = argparse.ArgumentParser(
        description="AI-Powered Speech-to-Text Note-Taking & Summarization System"
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to audio file for CLI transcription"
    )
    parser.add_argument(
        "--summarize",
        action="store_true",
        help="Generate a summary of the transcription"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        default=True,
        help="Launch the GUI (default behavior)"
    )

    args = parser.parse_args()

    if args.file:
        run_cli(args)
    else:
        run_gui()


if __name__ == "__main__":
    main()
