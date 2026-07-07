"""
Main GUI Application (app_gui.py)

Tkinter-based graphical user interface for the AI-powered
Speech-to-Text Note-Taking and Summarization System.

Objective 3: Design a simple user interface for system interaction.

Features:
- Record from microphone (with interruptible stop)
- Upload audio file
- Language selector (99+ languages via Whisper)
- View live transcript
- Auto-summarize transcript
- Progress indicator during long operations
- Evaluation panel (WER / ROUGE scoring)
- Session history viewer (browse, reload, delete)
- Save / Export output
- Live dark/light theme switching

Author: [Your Name]
Date: 2026
"""

import os
import sys
import threading
import logging
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
from pathlib import Path

# Add project root and src/ to path so imports work regardless of
# where Python is invoked from.
_UI_DIR      = Path(__file__).resolve().parent
_PROJECT_ROOT = _UI_DIR.parent
_SRC_DIR     = _PROJECT_ROOT / "src"
for _p in [str(_PROJECT_ROOT), str(_SRC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from src.speech_to_text import SpeechToTextModule
from src.summarizer import SummarizationModule
from src.storage import StorageModule
from src.evaluator import EvaluationModule
from ui.styles import DARK_THEME, LIGHT_THEME, FONTS, PAD, BUTTON_STYLE

logger = logging.getLogger(__name__)


class SpeechNotesApp(tk.Tk):
    """
    Main application window for the AI-powered Speech-to-Text
    Note-Taking and Summarization System.
    """

    APP_TITLE  = "AI Speech Notes — Speech-to-Text & Summarizer"
    APP_WIDTH  = 1150
    APP_HEIGHT = 780

    def __init__(self):
        super().__init__()
        self.title(self.APP_TITLE)
        self.geometry(f"{self.APP_WIDTH}x{self.APP_HEIGHT}")
        self.minsize(860, 620)

        # ── Theme ────────────────────────────────────────────────────
        self._theme_name = os.getenv("UI_THEME", "dark")
        self.theme = DARK_THEME if self._theme_name == "dark" else LIGHT_THEME
        self.configure(bg=self.theme["bg_primary"])

        # ── State ────────────────────────────────────────────────────
        self._recording        = False
        self._stop_recording   = threading.Event()   # signals mic thread to stop
        self._last_audio_path  = None
        self._transcript       = ""
        self._summary          = ""
        self._language         = "auto"
        self._record_seconds   = tk.IntVar(value=30)
        self._selected_lang    = tk.StringVar(value="auto")

        # ── AI Modules ───────────────────────────────────────────────
        self.stt        = SpeechToTextModule()
        self.summarizer = SummarizationModule()
        self.storage    = StorageModule()
        self.evaluator  = EvaluationModule()

        # ── Build UI ─────────────────────────────────────────────────
        self._build_ui()
        self._status("Ready. Upload an audio file or start recording.")
        logger.info("GUI initialized.")

    # ─────────────────────────────────────────────────────────────────
    # UI Construction
    # ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        """Build and lay out all UI widgets."""
        self._build_header()
        self._build_toolbar()
        self._build_notebook()
        self._build_statusbar()

    def _build_header(self):
        """Top header bar with title and theme toggle."""
        C = self.theme
        header = tk.Frame(self, bg=C["bg_secondary"], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="AI Speech Notes",
            font=FONTS["title"],
            bg=C["bg_secondary"],
            fg=C["text_primary"]
        ).pack(side=tk.LEFT, padx=PAD["lg"], pady=10)

        self._theme_btn = tk.Button(
            header,
            text="Light Mode" if self._theme_name == "dark" else "Dark Mode",
            font=FONTS["small"],
            bg=C["bg_card"],
            fg=C["text_secondary"],
            command=self._toggle_theme,
            **BUTTON_STYLE
        )
        self._theme_btn.pack(side=tk.RIGHT, padx=PAD["lg"], pady=10)

        tk.Label(
            header,
            text="v1.0  |  FYP 2026",
            font=FONTS["small"],
            bg=C["bg_secondary"],
            fg=C["text_secondary"]
        ).pack(side=tk.RIGHT, padx=PAD["sm"])

    def _build_toolbar(self):
        """Action toolbar: upload, record, language, summarize, save, clear."""
        C = self.theme
        self._toolbar_frame = tk.Frame(self, bg=C["bg_card"], pady=8)
        self._toolbar_frame.pack(fill=tk.X, padx=0, pady=(0, 2))

        self._btn_upload = self._make_button(
            self._toolbar_frame, "Upload Audio", C["accent_blue"], self._on_upload
        )
        self._btn_upload.pack(side=tk.LEFT, padx=(PAD["lg"], PAD["sm"]))

        self._btn_record = self._make_button(
            self._toolbar_frame, "Start Recording", C["accent_danger"], self._on_record_toggle
        )
        self._btn_record.pack(side=tk.LEFT, padx=PAD["sm"])

        tk.Label(
            self._toolbar_frame, text="Duration (s):",
            font=FONTS["small"], bg=C["bg_card"], fg=C["text_secondary"]
        ).pack(side=tk.LEFT, padx=(PAD["lg"], 0))

        tk.Spinbox(
            self._toolbar_frame,
            from_=5, to=300, increment=5,
            textvariable=self._record_seconds,
            width=5, font=FONTS["body"],
            bg=C["bg_input"], fg=C["text_primary"], relief="flat"
        ).pack(side=tk.LEFT, padx=PAD["sm"])

        # ── Language selector ──────────────────────────────────────
        tk.Label(
            self._toolbar_frame, text="Language:",
            font=FONTS["small"], bg=C["bg_card"], fg=C["text_secondary"]
        ).pack(side=tk.LEFT, padx=(PAD["lg"], 0))

        lang_options = ["auto"] + sorted([
            "en", "fr", "de", "es", "it", "pt", "nl", "pl", "ru",
            "zh", "ja", "ko", "ar", "hi", "tr", "vi", "uk", "cs",
            "sv", "ro", "hu", "fi", "da", "no", "id", "th", "he",
        ])
        self._lang_combo = ttk.Combobox(
            self._toolbar_frame,
            textvariable=self._selected_lang,
            values=lang_options,
            state="readonly",
            width=6,
            font=FONTS["body"]
        )
        self._lang_combo.pack(side=tk.LEFT, padx=PAD["sm"])

        self._btn_summarize = self._make_button(
            self._toolbar_frame, "Summarize", C["accent_warn"], self._on_summarize
        )
        self._btn_summarize.pack(side=tk.LEFT, padx=PAD["sm"])

        self._btn_save = self._make_button(
            self._toolbar_frame, "Save Session", C["accent"], self._on_save
        )
        self._btn_save.pack(side=tk.LEFT, padx=PAD["sm"])

        self._btn_clear = self._make_button(
            self._toolbar_frame, "Clear", C["text_secondary"], self._on_clear
        )
        self._btn_clear.pack(side=tk.RIGHT, padx=PAD["lg"])

    def _build_notebook(self):
        """Tabbed content: Main | Evaluate | History."""
        C = self.theme
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure(
            "App.TNotebook",
            background=C["bg_primary"],
            borderwidth=0
        )
        style.configure(
            "App.TNotebook.Tab",
            background=C["bg_card"],
            foreground=C["text_secondary"],
            padding=[12, 6],
            font=FONTS["body_bold"]
        )
        style.map(
            "App.TNotebook.Tab",
            background=[("selected", C["accent"])],
            foreground=[("selected", "#FFFFFF")]
        )

        self._notebook = ttk.Notebook(self, style="App.TNotebook")
        self._notebook.pack(fill=tk.BOTH, expand=True,
                            padx=PAD["md"], pady=(4, 0))

        self._tab_main    = tk.Frame(self._notebook, bg=C["bg_primary"])
        self._tab_eval    = tk.Frame(self._notebook, bg=C["bg_primary"])
        self._tab_history = tk.Frame(self._notebook, bg=C["bg_primary"])

        self._notebook.add(self._tab_main,    text="  Transcript & Summary  ")
        self._notebook.add(self._tab_eval,    text="  Evaluation  ")
        self._notebook.add(self._tab_history, text="  Session History  ")

        self._build_main_tab()
        self._build_eval_tab()
        self._build_history_tab()

    def _build_main_tab(self):
        """Two-panel layout: Transcript (left) + Summary (right)."""
        C = self.theme
        content = tk.Frame(self._tab_main, bg=C["bg_primary"])
        content.pack(fill=tk.BOTH, expand=True,
                     padx=PAD["sm"], pady=PAD["sm"])

        # progress bar (hidden until an operation runs)
        self._progress = ttk.Progressbar(
            self._tab_main, mode="indeterminate", length=200
        )

        # ── Left: Transcript ───────────────────────────────────────
        left = tk.Frame(content, bg=C["bg_card"])
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                  padx=(0, PAD["sm"]))

        self._build_panel_header(left, "Transcript", C)
        self._txt_transcript = scrolledtext.ScrolledText(
            left,
            font=FONTS["mono_large"],
            bg=C["bg_input"],
            fg=C["text_primary"],
            insertbackground=C["text_primary"],
            relief="flat", padx=10, pady=10,
            wrap=tk.WORD
        )
        self._txt_transcript.pack(fill=tk.BOTH, expand=True,
                                  padx=PAD["sm"], pady=(0, PAD["sm"]))

        tf = tk.Frame(left, bg=C["bg_card"])
        tf.pack(fill=tk.X, padx=PAD["sm"], pady=(0, PAD["sm"]))
        self._lbl_lang = tk.Label(
            tf, text="Language: —",
            font=FONTS["small"], bg=C["bg_card"], fg=C["text_secondary"]
        )
        self._lbl_lang.pack(side=tk.LEFT)
        self._lbl_words = tk.Label(
            tf, text="Words: 0",
            font=FONTS["small"], bg=C["bg_card"], fg=C["text_secondary"]
        )
        self._lbl_words.pack(side=tk.RIGHT)

        # ── Right: Summary ─────────────────────────────────────────
        right = tk.Frame(content, bg=C["bg_card"])
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True,
                   padx=(PAD["sm"], 0))

        self._build_panel_header(right, "AI Summary", C)
        self._txt_summary = scrolledtext.ScrolledText(
            right,
            font=FONTS["mono_large"],
            bg=C["bg_input"],
            fg=C["text_primary"],
            insertbackground=C["text_primary"],
            relief="flat", padx=10, pady=10,
            wrap=tk.WORD
        )
        self._txt_summary.pack(fill=tk.BOTH, expand=True,
                               padx=PAD["sm"], pady=(0, PAD["sm"]))

        sf_frame = tk.Frame(right, bg=C["bg_card"])
        sf_frame.pack(fill=tk.X, padx=PAD["sm"], pady=(0, PAD["sm"]))
        self._lbl_rouge = tk.Label(
            sf_frame, text="ROUGE: —",
            font=FONTS["small"], bg=C["bg_card"], fg=C["text_secondary"]
        )
        self._lbl_rouge.pack(side=tk.LEFT)

    def _build_eval_tab(self):
        """Evaluation panel: enter reference text, compute WER + ROUGE."""
        C = self.theme
        pad = PAD["md"]

        tk.Label(
            self._tab_eval,
            text="Performance Evaluation",
            font=FONTS["heading"], bg=C["bg_primary"], fg=C["text_primary"]
        ).pack(anchor="w", padx=pad, pady=(pad, 2))

        tk.Label(
            self._tab_eval,
            text="Paste the reference (ground-truth) transcript and summary, "
                 "then click Evaluate.",
            font=FONTS["small"], bg=C["bg_primary"], fg=C["text_secondary"],
            wraplength=900, justify="left"
        ).pack(anchor="w", padx=pad, pady=(0, pad))

        panels = tk.Frame(self._tab_eval, bg=C["bg_primary"])
        panels.pack(fill=tk.BOTH, expand=True, padx=pad, pady=(0, pad))

        # Reference transcript
        lf_trans = tk.LabelFrame(
            panels, text=" Reference Transcript ",
            font=FONTS["small"], bg=C["bg_primary"],
            fg=C["text_secondary"], bd=1,
            relief="groove"
        )
        lf_trans.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                      padx=(0, pad))
        self._txt_ref_transcript = scrolledtext.ScrolledText(
            lf_trans, font=FONTS["mono_large"],
            bg=C["bg_input"], fg=C["text_primary"],
            insertbackground=C["text_primary"],
            relief="flat", padx=8, pady=8, wrap=tk.WORD, height=10
        )
        self._txt_ref_transcript.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Reference summary
        lf_summ = tk.LabelFrame(
            panels, text=" Reference Summary ",
            font=FONTS["small"], bg=C["bg_primary"],
            fg=C["text_secondary"], bd=1, relief="groove"
        )
        lf_summ.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self._txt_ref_summary = scrolledtext.ScrolledText(
            lf_summ, font=FONTS["mono_large"],
            bg=C["bg_input"], fg=C["text_primary"],
            insertbackground=C["text_primary"],
            relief="flat", padx=8, pady=8, wrap=tk.WORD, height=10
        )
        self._txt_ref_summary.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Evaluate button
        self._btn_evaluate = self._make_button(
            self._tab_eval, "Run Evaluation", C["accent_blue"], self._on_evaluate
        )
        self._btn_evaluate.pack(pady=(0, pad))

        # Results display
        lf_results = tk.LabelFrame(
            self._tab_eval, text=" Results ",
            font=FONTS["small"], bg=C["bg_primary"],
            fg=C["text_secondary"], bd=1, relief="groove"
        )
        lf_results.pack(fill=tk.X, padx=pad, pady=(0, pad))
        self._txt_eval_results = scrolledtext.ScrolledText(
            lf_results, font=FONTS["mono"],
            bg=C["bg_input"], fg=C["text_primary"],
            insertbackground=C["text_primary"],
            relief="flat", padx=8, pady=8, wrap=tk.WORD, height=8,
            state=tk.DISABLED
        )
        self._txt_eval_results.pack(fill=tk.X, padx=4, pady=4)

    def _build_history_tab(self):
        """Session history: list saved sessions, reload or delete them."""
        C = self.theme
        pad = PAD["md"]

        top = tk.Frame(self._tab_history, bg=C["bg_primary"])
        top.pack(fill=tk.X, padx=pad, pady=(pad, 0))

        tk.Label(
            top, text="Saved Sessions",
            font=FONTS["heading"], bg=C["bg_primary"], fg=C["text_primary"]
        ).pack(side=tk.LEFT)

        self._btn_refresh = self._make_button(
            top, "Refresh", C["accent_blue"], self._on_history_refresh
        )
        self._btn_refresh.pack(side=tk.RIGHT)

        self._btn_export_csv = self._make_button(
            top, "Export CSV", C["accent"], self._on_export_csv
        )
        self._btn_export_csv.pack(side=tk.RIGHT, padx=(0, PAD["sm"]))

        # Treeview
        cols = ("session_id", "created_at", "source", "language")
        style = ttk.Style()
        style.configure(
            "App.Treeview",
            background=C["bg_input"],
            foreground=C["text_primary"],
            fieldbackground=C["bg_input"],
            rowheight=24,
            font=FONTS["body"]
        )
        style.configure(
            "App.Treeview.Heading",
            background=C["bg_card"],
            foreground=C["text_primary"],
            font=FONTS["body_bold"]
        )

        tree_frame = tk.Frame(self._tab_history, bg=C["bg_primary"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=pad, pady=pad)

        self._tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings",
            style="App.Treeview", selectmode="browse"
        )
        for col, width, label in [
            ("session_id",  160, "Session ID"),
            ("created_at",  180, "Created At"),
            ("source",      260, "Audio Source"),
            ("language",     80, "Language"),
        ]:
            self._tree.heading(col, text=label)
            self._tree.column(col, width=width, anchor="w")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Action buttons
        btn_row = tk.Frame(self._tab_history, bg=C["bg_primary"])
        btn_row.pack(fill=tk.X, padx=pad, pady=(0, pad))

        self._btn_load_session = self._make_button(
            btn_row, "Load Session", C["accent"], self._on_load_session
        )
        self._btn_load_session.pack(side=tk.LEFT)

        self._btn_delete_session = self._make_button(
            btn_row, "Delete Session", C["accent_danger"], self._on_delete_session
        )
        self._btn_delete_session.pack(side=tk.LEFT, padx=(PAD["sm"], 0))

        # Populate on first load
        self._on_history_refresh()

    def _build_panel_header(self, parent, title: str, C: dict):
        """Styled section header with separator line."""
        hf = tk.Frame(parent, bg=C["bg_card"])
        hf.pack(fill=tk.X, padx=PAD["sm"], pady=(PAD["sm"], 0))
        tk.Label(
            hf, text=title,
            font=FONTS["heading"],
            bg=C["bg_card"], fg=C["text_primary"]
        ).pack(side=tk.LEFT)
        tk.Frame(parent, bg=C["border"], height=1).pack(
            fill=tk.X, padx=PAD["sm"], pady=(4, 8)
        )

    def _build_statusbar(self):
        """Bottom status bar."""
        C = self.theme
        self._statusbar = tk.Frame(self, bg=C["bg_secondary"], height=28)
        self._statusbar.pack(fill=tk.X, side=tk.BOTTOM)
        self._statusbar.pack_propagate(False)
        self._status_var = tk.StringVar(value="Ready")
        self._lbl_status = tk.Label(
            self._statusbar,
            textvariable=self._status_var,
            font=FONTS["small"],
            bg=C["bg_secondary"], fg=C["text_secondary"],
            anchor="w"
        )
        self._lbl_status.pack(fill=tk.X, padx=PAD["md"], pady=4)

    # ─────────────────────────────────────────────────────────────────
    # Event Handlers
    # ─────────────────────────────────────────────────────────────────

    def _on_upload(self):
        """Open file dialog and transcribe selected audio."""
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Audio Files", "*.wav *.mp3 *.m4a *.ogg *.flac *.aac"),
                ("All Files", "*.*")
            ]
        )
        if not file_path:
            return
        self._last_audio_path = file_path
        self._status(f"Transcribing: {Path(file_path).name} ...")
        self._set_buttons_state(tk.DISABLED)
        self._progress_start()
        threading.Thread(
            target=self._transcribe_task, args=(file_path,), daemon=True
        ).start()

    def _on_record_toggle(self):
        """Toggle microphone recording on/off."""
        if not self._recording:
            self._recording = True
            self._stop_recording.clear()
            self._btn_record.config(text="Stop Recording")
            duration = self._record_seconds.get()
            self._status(f"Recording for up to {duration} seconds...")
            threading.Thread(
                target=self._record_task, args=(duration,), daemon=True
            ).start()
        else:
            # Signal the recording thread to stop early
            self._stop_recording.set()
            self._btn_record.config(text="Start Recording")
            self._status("Stopping recording...")

    def _on_summarize(self):
        """Summarize the current transcript text."""
        text = self._txt_transcript.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning(
                "No Transcript",
                "Please transcribe audio before summarizing."
            )
            return
        self._transcript = text
        self._status("Generating AI summary...")
        self._set_buttons_state(tk.DISABLED)
        self._progress_start()
        threading.Thread(
            target=self._summarize_task, args=(text,), daemon=True
        ).start()

    def _on_save(self):
        """Save current session to disk."""
        transcript = self._txt_transcript.get("1.0", tk.END).strip()
        summary    = self._txt_summary.get("1.0", tk.END).strip()
        if not transcript:
            messagebox.showwarning("Nothing to Save", "No transcript to save.")
            return
        try:
            paths = self.storage.save(
                audio_file=self._last_audio_path or "live_recording",
                transcript=transcript,
                summary=summary if summary else None,
                language=self._language
            )
            self._status(f"Session saved.")
            messagebox.showinfo(
                "Saved",
                "Session saved successfully!\n\n" + "\n".join(paths.values())
            )
            # Refresh history tab
            self._on_history_refresh()
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def _on_clear(self):
        """Clear all output fields."""
        self._txt_transcript.delete("1.0", tk.END)
        self._txt_summary.delete("1.0", tk.END)
        self._lbl_lang.config(text="Language: —")
        self._lbl_words.config(text="Words: 0")
        self._lbl_rouge.config(text="ROUGE: —")
        self._last_audio_path = None
        self._transcript = ""
        self._summary = ""
        self._status("Cleared.")

    def _on_evaluate(self):
        """Compute WER + ROUGE against user-supplied reference text."""
        hyp_transcript = self._txt_transcript.get("1.0", tk.END).strip()
        ref_transcript = self._txt_ref_transcript.get("1.0", tk.END).strip()
        hyp_summary    = self._txt_summary.get("1.0", tk.END).strip()
        ref_summary    = self._txt_ref_summary.get("1.0", tk.END).strip()

        if not hyp_transcript:
            messagebox.showwarning(
                "No Transcript",
                "Generate a transcript first before evaluating."
            )
            return
        if not ref_transcript:
            messagebox.showwarning(
                "No Reference",
                "Paste a reference transcript in the Evaluation tab."
            )
            return

        self._btn_evaluate.config(state=tk.DISABLED)
        self._status("Running evaluation...")

        def _run():
            lines = ["=" * 52, "  EVALUATION RESULTS", "=" * 52, ""]
            try:
                trans_res = self.evaluator.evaluate_transcription(
                    ref_transcript, hyp_transcript
                )
                lines += [
                    "  TRANSCRIPTION",
                    f"    WER : {trans_res.get('WER_pct', 'N/A')}",
                    f"    CER : {trans_res.get('CER_pct', 'N/A')}",
                    ""
                ]
                if ref_summary and hyp_summary:
                    summ_res = self.evaluator.evaluate_summarization(
                        ref_summary, hyp_summary
                    )
                    r1 = summ_res.get("ROUGE-1", {})
                    r2 = summ_res.get("ROUGE-2", {})
                    rl = summ_res.get("ROUGE-L", {})
                    lines += [
                        "  SUMMARIZATION",
                        f"    ROUGE-1 F : {r1.get('fmeasure', 'N/A')}",
                        f"    ROUGE-2 F : {r2.get('fmeasure', 'N/A')}",
                        f"    ROUGE-L F : {rl.get('fmeasure', 'N/A')}",
                        ""
                    ]
                    # Update ROUGE label on main tab
                    rouge_txt = (
                        f"ROUGE-1: {r1.get('fmeasure', '?')}  "
                        f"ROUGE-2: {r2.get('fmeasure', '?')}  "
                        f"ROUGE-L: {rl.get('fmeasure', '?')}"
                    )
                    self.after(0, lambda: self._lbl_rouge.config(text=rouge_txt))
                else:
                    lines.append(
                        "  (Paste a reference summary to also compute ROUGE)"
                    )
            except Exception as e:
                lines.append(f"  Error: {e}")

            lines.append("=" * 52)
            report = "\n".join(lines)
            self.after(0, self._show_eval_results, report)
            self.after(0, lambda: self._btn_evaluate.config(state=tk.NORMAL))
            self.after(0, lambda: self._status("Evaluation complete."))

        threading.Thread(target=_run, daemon=True).start()

    def _show_eval_results(self, report: str):
        """Write evaluation results into the read-only results box."""
        self._txt_eval_results.config(state=tk.NORMAL)
        self._txt_eval_results.delete("1.0", tk.END)
        self._txt_eval_results.insert(tk.END, report)
        self._txt_eval_results.config(state=tk.DISABLED)

    def _on_history_refresh(self):
        """Reload the session list from disk."""
        for row in self._tree.get_children():
            self._tree.delete(row)
        sessions = self.storage.list_sessions()
        for s in sessions:
            self._tree.insert("", tk.END, values=(
                s.get("session_id", ""),
                s.get("created_at", ""),
                Path(s.get("source", "")).name if s.get("source") else "",
                s.get("language", ""),
            ), tags=(s.get("file", ""),))
        self._status(f"History: {len(sessions)} session(s) found.")

    def _on_load_session(self):
        """Load the selected session into the main transcript/summary panels."""
        selected = self._tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Select a session to load.")
            return
        tags = self._tree.item(selected[0], "tags")
        if not tags:
            return
        json_path = tags[0]
        try:
            data = self.storage.load_session(json_path)
            self._txt_transcript.delete("1.0", tk.END)
            self._txt_transcript.insert(tk.END, data.get("transcript", ""))
            self._txt_summary.delete("1.0", tk.END)
            self._txt_summary.insert(tk.END, data.get("summary", "") or "")
            lang = data.get("language", "unknown")
            words = len((data.get("transcript", "")).split())
            self._lbl_lang.config(text=f"Language: {lang.upper()}")
            self._lbl_words.config(text=f"Words: {words:,}")
            self._last_audio_path = data.get("audio_source")
            self._language = lang
            self._notebook.select(0)   # switch to main tab
            self._status(f"Session loaded: {data.get('session_id')}")
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def _on_delete_session(self):
        """Delete the selected session from disk."""
        selected = self._tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Select a session to delete.")
            return
        vals = self._tree.item(selected[0], "values")
        session_id = vals[0] if vals else ""
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete session '{session_id}'?\nThis cannot be undone."
        ):
            return
        deleted = self.storage.delete_session(session_id)
        if deleted:
            self._status(f"Deleted session: {session_id}")
        else:
            self._status("Session files not found (may already be deleted).")
        self._on_history_refresh()

    def _on_export_csv(self):
        """Export all sessions to a CSV file chosen by the user."""
        csv_path = filedialog.asksaveasfilename(
            title="Export Sessions as CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not csv_path:
            return
        result = self.storage.export_csv(output_path=csv_path)
        if result:
            messagebox.showinfo("Exported", f"CSV saved to:\n{result}")
            self._status(f"CSV exported: {result}")
        else:
            messagebox.showwarning("No Data", "No sessions to export.")

    # ─────────────────────────────────────────────────────────────────
    # Background Tasks
    # ─────────────────────────────────────────────────────────────────

    def _transcribe_task(self, file_path: str):
        """Background thread: run transcription from file."""
        try:
            lang = self._selected_lang.get()
            lang = None if lang == "auto" else lang
            result = self.stt.transcribe(file_path, language=lang)
            self._transcript = result["text"]
            self._language   = result.get("language", "unknown")
            self.after(0, self._on_transcription_done, result)
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            self.after(0, lambda: messagebox.showerror("Transcription Error", str(e)))
        finally:
            self.after(0, self._progress_stop)
            self.after(0, lambda: self._set_buttons_state(tk.NORMAL))

    def _record_task(self, duration: int):
        """
        Background thread: record from microphone then transcribe.
        Honours self._stop_recording event for early stop.
        """
        import sounddevice as sd
        import numpy as np
        import soundfile as sf

        frames = []
        SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", 16000))

        def _audio_cb(indata, frame_count, time_info, status):
            if status:
                logger.warning(f"Audio status: {status}")
            frames.append(indata.copy())

        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE, channels=1,
                dtype="float32", callback=_audio_cb
            ):
                # Poll stop event every 100 ms instead of blocking for full duration
                elapsed = 0
                while elapsed < duration * 1000:
                    sd.sleep(100)
                    elapsed += 100
                    if self._stop_recording.is_set():
                        break

            if not frames:
                self.after(0, lambda: self._status("No audio captured."))
                return

            audio_array = np.concatenate(frames, axis=0).flatten()
            tmp_path = tempfile.mktemp(suffix=".wav", prefix="recording_")
            sf.write(tmp_path, audio_array, SAMPLE_RATE)
            self._last_audio_path = tmp_path
            self.after(0, lambda: self._status("Transcribing recording..."))
            self._progress_start()

            lang = self._selected_lang.get()
            lang = None if lang == "auto" else lang
            result = self.stt.transcribe(tmp_path, language=lang)
            self._transcript = result["text"]
            self._language   = result.get("language", "unknown")
            self.after(0, self._on_transcription_done, result)
        except Exception as e:
            logger.error(f"Recording error: {e}")
            self.after(0, lambda: messagebox.showerror("Recording Error", str(e)))
        finally:
            self._recording = False
            self.after(0, self._progress_stop)
            self.after(0, lambda: self._btn_record.config(text="Start Recording"))
            self.after(0, lambda: self._set_buttons_state(tk.NORMAL))

    def _summarize_task(self, text: str):
        """Background thread: run summarization."""
        try:
            summary = self.summarizer.summarize(text)
            self._summary = summary
            self.after(0, self._on_summarization_done, summary)
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            self.after(0, lambda: messagebox.showerror("Summarization Error", str(e)))
        finally:
            self.after(0, self._progress_stop)
            self.after(0, lambda: self._set_buttons_state(tk.NORMAL))

    # ─────────────────────────────────────────────────────────────────
    # UI Update Callbacks  (always called on main thread via after())
    # ─────────────────────────────────────────────────────────────────

    def _on_transcription_done(self, result: dict):
        """Update transcript panel after transcription completes."""
        text     = result.get("text", "")
        language = result.get("language", "unknown")
        words    = len(text.split())
        self._txt_transcript.delete("1.0", tk.END)
        self._txt_transcript.insert(tk.END, text)
        self._lbl_lang.config(text=f"Language: {language.upper()}")
        self._lbl_words.config(text=f"Words: {words:,}")
        self._status(
            f"Transcription complete — {words:,} words  |  Language: {language}"
        )

    def _on_summarization_done(self, summary: str):
        """Update summary panel after summarization completes."""
        self._txt_summary.delete("1.0", tk.END)
        self._txt_summary.insert(tk.END, summary)
        self._status("Summary generated successfully.")

    # ─────────────────────────────────────────────────────────────────
    # Utility Methods
    # ─────────────────────────────────────────────────────────────────

    def _make_button(self, parent, text: str, color: str, command) -> tk.Button:
        """Create a styled flat button."""
        C = self.theme
        return tk.Button(
            parent,
            text=text,
            font=FONTS["body_bold"],
            bg=color,
            fg="#FFFFFF",
            activebackground=C["accent_hover"],
            activeforeground="#FFFFFF",
            command=command,
            **BUTTON_STYLE
        )

    def _set_buttons_state(self, state):
        """Enable or disable the main action buttons."""
        for btn in [
            self._btn_upload, self._btn_record,
            self._btn_summarize, self._btn_save
        ]:
            btn.config(state=state)

    def _progress_start(self):
        """Show and start the indeterminate progress bar."""
        self._progress.pack(pady=(0, 4))
        self._progress.start(12)

    def _progress_stop(self):
        """Stop and hide the progress bar."""
        self._progress.stop()
        self._progress.pack_forget()

    def _status(self, msg: str):
        """Update the status bar with a timestamped message."""
        ts = datetime.now().strftime("%H:%M:%S")
        self._status_var.set(f"[{ts}]  {msg}")
        logger.info(msg)

    def _toggle_theme(self):
        """Live-switch between dark and light themes."""
        if self._theme_name == "dark":
            self._theme_name = "light"
            self.theme = LIGHT_THEME
        else:
            self._theme_name = "dark"
            self.theme = DARK_THEME

        C = self.theme
        self._theme_btn.config(
            text="Light Mode" if self._theme_name == "dark" else "Dark Mode"
        )
        self._apply_theme_recursive(self, C)

    def _apply_theme_recursive(self, widget, C: dict):
        """
        Walk the widget tree and recolour every widget that has
        background / foreground options we know about.
        """
        widget_type = widget.winfo_class()

        bg_map = {
            "Frame":        C["bg_primary"],
            "Label":        None,           # handled per-parent below
            "Button":       None,           # leave button accent colours alone
            "Text":         C["bg_input"],
            "ScrolledText": C["bg_input"],
            "Spinbox":      C["bg_input"],
        }

        try:
            if widget_type in ("Frame", "Toplevel"):
                parent_bg = widget.cget("bg")
                # Map old colour to new
                if parent_bg in (DARK_THEME["bg_primary"], LIGHT_THEME["bg_primary"]):
                    widget.config(bg=C["bg_primary"])
                elif parent_bg in (DARK_THEME["bg_secondary"], LIGHT_THEME["bg_secondary"]):
                    widget.config(bg=C["bg_secondary"])
                elif parent_bg in (DARK_THEME["bg_card"], LIGHT_THEME["bg_card"]):
                    widget.config(bg=C["bg_card"])
            elif widget_type == "Label":
                parent_bg = widget.cget("bg")
                if parent_bg in (DARK_THEME["bg_secondary"], LIGHT_THEME["bg_secondary"]):
                    widget.config(bg=C["bg_secondary"], fg=C["text_secondary"])
                elif parent_bg in (DARK_THEME["bg_card"], LIGHT_THEME["bg_card"]):
                    widget.config(bg=C["bg_card"], fg=C["text_secondary"])
                else:
                    widget.config(bg=C["bg_primary"], fg=C["text_primary"])
            elif widget_type in ("Text",):
                widget.config(bg=C["bg_input"], fg=C["text_primary"],
                              insertbackground=C["text_primary"])
            elif widget_type == "Spinbox":
                widget.config(bg=C["bg_input"], fg=C["text_primary"])
        except tk.TclError:
            pass   # widget doesn't support that option — skip

        for child in widget.winfo_children():
            self._apply_theme_recursive(child, C)

        # Also update the root window and status bar backgrounds
        self.configure(bg=C["bg_primary"])
        try:
            self._statusbar.config(bg=C["bg_secondary"])
            self._lbl_status.config(bg=C["bg_secondary"], fg=C["text_secondary"])
        except AttributeError:
            pass


