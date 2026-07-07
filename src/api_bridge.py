"""
api_bridge.py - Thin CLI bridge for the PHP front-end.

Called by text_to_speech.php via shell_exec(). Reads action + arguments
from command-line flags, runs the appropriate module, and prints a single
JSON object to stdout.

Actions
-------
  transcribe      -- transcribe an uploaded audio file
  transcribe_mic  -- transcribe a browser mic recording (webm/ogg blob)
  list_sessions   -- list all saved sessions
  load_session    -- load one session by ID
  delete_session  -- delete one session by ID
  evaluate        -- compute WER/CER/ROUGE against reference texts

All responses: { "ok": true, "data": {...} }  or  { "ok": false, "error": "..." }
"""

import sys
import os
import json
import argparse
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SRC  = Path(__file__).resolve().parent
for _p in [str(_ROOT), str(_SRC)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from dotenv import load_dotenv
load_dotenv(dotenv_path=_ROOT / ".env")


def _ok(data: dict):
    print(json.dumps({"ok": True, "data": data}, ensure_ascii=False))
    sys.exit(0)


def _err(message: str):
    print(json.dumps({"ok": False, "error": message}, ensure_ascii=False))
    sys.exit(1)


#  Shared transcription logic 

def _run_transcription(filepath: str, lang: str, do_summarize: bool) -> dict:
    """
    Core transcription + optional summarisation + storage.
    Used by both action_transcribe and action_transcribe_mic.
    """
    from speech_to_text import SpeechToTextModule
    from storage import StorageModule

    stt     = SpeechToTextModule()
    storage = StorageModule()

    language_hint = lang if lang and lang != "auto" else None
    result = stt.transcribe(filepath, language=language_hint)

    transcript = result["text"]
    language   = result.get("language", "unknown")
    segments   = result.get("segments", [])
    summary    = None

    if do_summarize and transcript.strip():
        from summarizer import SummarizationModule
        summary = SummarizationModule().summarize(transcript)

    saved = storage.save(
        audio_file=filepath,
        transcript=transcript,
        summary=summary,
        segments=segments,
        language=language,
    )

    return {
        "transcript": transcript,
        "summary":    summary,
        "language":   language,
        "word_count": len(transcript.split()),
        "segments":   segments[:10],
        "saved":      saved,
    }


#  Actions 

def action_transcribe(args):
    """Transcribe a file uploaded from the browser file-picker."""
    if not args.file:
        _err("--file is required for action=transcribe")
    if not os.path.exists(args.file):
        _err(f"File not found: {args.file}")
    _ok(_run_transcription(args.file, args.lang, args.summarize))


def action_transcribe_mic(args):
    """
    Transcribe a browser microphone recording.
    PHP saves the raw WebM/OGG blob to a temp file and passes --file.
    Whisper decodes WebM/OGG natively via FFmpeg.
    """
    if not args.file:
        _err("--file is required for action=transcribe_mic")
    if not os.path.exists(args.file):
        _err(f"Mic recording file not found: {args.file}")
    _ok(_run_transcription(args.file, args.lang, args.summarize))


def action_list_sessions(args):
    from storage import StorageModule
    _ok({"sessions": StorageModule().list_sessions()})


def action_load_session(args):
    if not args.session_id:
        _err("--session_id is required for action=load_session")
    from storage import StorageModule
    storage   = StorageModule()
    candidate = storage.transcripts_dir / f"session_{args.session_id}.json"
    if not candidate.exists():
        _err(f"Session not found: {args.session_id}")
    _ok({"session": storage.load_session(str(candidate))})


def action_delete_session(args):
    if not args.session_id:
        _err("--session_id is required for action=delete_session")
    from storage import StorageModule
    deleted = StorageModule().delete_session(args.session_id)
    _ok({"deleted": deleted, "session_id": args.session_id})


def action_evaluate(args):
    if not args.ref_transcript or not args.hyp_transcript:
        _err("--ref_transcript and --hyp_transcript are required for action=evaluate")
    from evaluator import EvaluationModule
    ev     = EvaluationModule()
    trans  = ev.evaluate_transcription(args.ref_transcript, args.hyp_transcript)
    result = {"transcription": trans, "summarization": None}
    if args.ref_summary and args.gen_summary:
        result["summarization"] = ev.evaluate_summarization(args.ref_summary, args.gen_summary)
    _ok(result)


def action_summarize(args):
    if not args.text:
        _err("--text is required for action=summarize")
    from summarizer import SummarizationModule
    summary = SummarizationModule().summarize(args.text)
    _ok({"summary": summary})


def action_save_session(args):
    if not args.text:
        _err("--text is required for action=save_session")
    from storage import StorageModule
    storage = StorageModule()
    paths = storage.save(
        audio_file=args.file or "live_recording",
        transcript=args.text,
        summary=args.ref_summary,
        language=args.lang or "unknown"
    )
    _ok({"paths": paths})


#  Entry point 

def main():
    parser = argparse.ArgumentParser(description="API bridge for PHP front-end")
    parser.add_argument("--action", required=True,
                        choices=["transcribe", "transcribe_mic", "list_sessions",
                                 "load_session", "delete_session", "evaluate",
                                 "summarize", "save_session"])
    parser.add_argument("--file",           default=None)
    parser.add_argument("--lang",           default="auto")
    parser.add_argument("--summarize",      action="store_true")
    parser.add_argument("--session_id",     default=None)
    parser.add_argument("--ref_transcript", default=None)
    parser.add_argument("--hyp_transcript", default=None)
    parser.add_argument("--ref_summary",    default=None)
    parser.add_argument("--gen_summary",    default=None)
    parser.add_argument("--text",           default=None)

    args = parser.parse_args()

    try:
        dispatch = {
            "transcribe":      action_transcribe,
            "transcribe_mic":  action_transcribe_mic,
            "list_sessions":   action_list_sessions,
            "load_session":    action_load_session,
            "delete_session":  action_delete_session,
            "evaluate":        action_evaluate,
            "summarize":       action_summarize,
            "save_session":    action_save_session,
        }
        dispatch[args.action](args)
    except Exception as e:
        _err(str(e))


if __name__ == "__main__":
    main()
