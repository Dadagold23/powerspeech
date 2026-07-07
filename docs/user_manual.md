# User Manual

## Getting Started

### 1. Installation
Follow the steps in `README.md` to install all dependencies.

### 2. Launching the Application
```bash
python src/main.py
```

---

## Interface Guide

### Header Bar
- **App Name** — "AI Speech Notes"
- **Dark / Light Mode toggle** — switches the colour theme live

### Toolbar

| Control | Action |
|---------|--------|
| Upload Audio | Open a file picker to select a `.wav`, `.mp3`, `.m4a`, `.ogg`, `.flac`, or `.aac` file |
| Start Recording | Begin live microphone capture |
| Stop Recording | Click again to stop early (recording stops immediately, then transcribes) |
| Duration (s) | Set maximum recording duration in seconds (5 – 300) |
| Language | Select a language hint for Whisper, or leave on **auto** for automatic detection |
| Summarize | Generate an AI summary of the current transcript |
| Save Session | Save transcript + summary to `data/transcripts/` and `data/summaries/` |
| Clear | Clear all text fields and reset state |

### Tabs

#### Transcript & Summary (main tab)
- **Left panel** — full speech-to-text output.  Detected language and word count shown at the bottom.
- **Right panel** — AI-generated abstractive summary.  ROUGE scores shown here after running evaluation.
- A progress bar appears below the panels during transcription or summarization.

#### Evaluation
- Paste a **reference (ground-truth) transcript** and optionally a **reference summary**.
- Click **Run Evaluation** to compute:
  - **WER** (Word Error Rate) and **CER** (Character Error Rate) vs. the hypothesis transcript
  - **ROUGE-1 / ROUGE-2 / ROUGE-L** F-measures vs. the generated summary
- Results are displayed in the read-only results box.
- ROUGE scores are also reflected in the Summary panel footer.

#### Session History
- Lists all previously saved sessions (most recent first).
- **Load Session** — reloads the selected session into the main panels.
- **Delete Session** — permanently removes the session files (asks for confirmation).
- **Export CSV** — saves a CSV index of all sessions to a location you choose.
- **Refresh** — re-reads the sessions directory.

### Status Bar
- Shows a timestamped message describing the current or last action.

---

## Workflows

### Transcribe an Audio File
1. Click **Upload Audio**.
2. Select your audio file.
3. Wait for the transcript to appear (time depends on file length and model size).

### Record and Transcribe
1. Set the desired **Duration (s)** in the toolbar.
2. Optionally select a language.
3. Click **Start Recording** and speak into your microphone.
4. Either wait for the timer to expire, or click **Stop Recording** to stop early.
5. Transcription starts automatically after recording ends.

### Generate a Summary
1. Ensure a transcript is visible in the left panel.
2. Click **Summarize**.
3. The AI-generated summary appears in the right panel.

### Evaluate Performance
1. Generate a transcript and optionally a summary.
2. Go to the **Evaluation** tab.
3. Paste your reference (ground-truth) transcript.
4. Optionally paste a reference summary.
5. Click **Run Evaluation** and view the metric scores.

### Save and Revisit a Session
1. Click **Save Session** after transcription / summarization.
2. Switch to the **Session History** tab to see the saved entry.
3. Select a session and click **Load Session** to restore it.

---

## Supported Audio Formats

| Format | Extension |
|--------|-----------|
| WAV (recommended) | `.wav` |
| MP3 | `.mp3` |
| M4A / AAC | `.m4a`, `.aac` |
| OGG | `.ogg` |
| FLAC | `.flac` |

---

## Configuration (via `.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_MODEL` | `base` | Model size: `tiny` / `base` / `small` / `medium` / `large` |
| `SUMMARIZATION_MODEL` | `facebook/bart-large-cnn` | Hugging Face model ID |
| `SUMMARY_MAX_LENGTH` | `150` | Max tokens in summary |
| `SUMMARY_MIN_LENGTH` | `40` | Min tokens in summary |
| `AUDIO_SAMPLE_RATE` | `16000` | Microphone sample rate (Hz) |
| `TRANSCRIPTS_DIR` | `data/transcripts` | Where transcript files are saved |
| `SUMMARIES_DIR` | `data/summaries` | Where summary files are saved |
| `UI_THEME` | `dark` | `dark` or `light` (also changeable live in the GUI) |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No microphone detected | Check system audio settings; ensure a microphone is connected and permitted |
| Slow transcription | Use `WHISPER_MODEL=tiny` in `.env` for faster (less accurate) results |
| Out of memory | Use a smaller Whisper model (`tiny` or `base`) |
| FFmpeg not found | Install FFmpeg and add it to your system PATH |
| `ImportError` on launch | Run `pip install -r requirements.txt` again |
| Recording stops immediately | Ensure `sounddevice` is installed and your OS grants microphone access |
| Summary is cut off | Increase `SUMMARY_MAX_LENGTH` in `.env` |
