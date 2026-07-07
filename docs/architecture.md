# System Architecture

## Overview

The AI-Powered Speech-to-Text Note-Taking and Summarization System follows a
**modular, layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                           │
│                  ui/app_gui.py  (Tkinter)                       │
│   [ Upload ] [ Record ] [ Summarize ] [ Save ] [ Clear ]        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
              ┌─────────────▼──────────────┐
              │     APPLICATION LAYER      │
              │      src/main.py           │
              │ (CLI + GUI entry point)    │
              └─────────────┬──────────────┘
                            │
        ┌───────────────────┼──────────────────────┐
        │                   │                      │
┌───────▼──────┐   ┌────────▼──────┐   ┌──────────▼──────┐
│ SPEECH-TO-   │   │ SUMMARIZATION │   │  EVALUATION     │
│ TEXT MODULE  │   │    MODULE     │   │    MODULE       │
│ (Whisper)    │   │  (BART/T5)    │   │ (WER + ROUGE)   │
└───────┬──────┘   └────────┬──────┘   └──────────┬──────┘
        │                   │                      │
        └───────────────────┼──────────────────────┘
                            │
              ┌─────────────▼──────────────┐
              │     STORAGE LAYER          │
              │     src/storage.py         │
              │  (JSON / TXT / CSV)        │
              └─────────────┬──────────────┘
                            │
              ┌─────────────▼──────────────┐
              │     FILE SYSTEM            │
              │  data/transcripts/         │
              │  data/summaries/           │
              └────────────────────────────┘
```

## Component Descriptions

### 1. Presentation Layer (ui/)
- **app_gui.py**: Main Tkinter window with two-panel layout
- **styles.py**: Dark/light theme definitions

### 2. Speech-to-Text Module (src/speech_to_text.py)
- Uses **OpenAI Whisper** (pre-trained transformer model)
- Supports file input (.wav, .mp3, .m4a, .ogg, .flac)
- Supports live microphone recording via sounddevice
- Multilingual (99+ languages)

### 3. Summarization Module (src/summarizer.py)
- Uses **facebook/bart-large-cnn** via Hugging Face Transformers
- Abstractive summarization (not just extraction)
- Long text chunking for inputs exceeding model context window
- Also provides extractive key points

### 4. Storage Module (src/storage.py)
- Saves transcripts as `.txt` and `.json`
- Saves summaries as `.txt`
- Enables session history browsing and CSV export

### 5. Evaluation Module (src/evaluator.py)
- **WER** (Word Error Rate) via `jiwer`
- **CER** (Character Error Rate) via `jiwer`
- **ROUGE-1/2/L** via `rouge-score`
- Generates batch evaluation reports as JSON

## Data Flow

```
Audio Input (File or Microphone)
        │
        ▼
[SpeechToTextModule]
   Whisper Model → transcribes → Raw Text Transcript
        │
        ▼
[SummarizationModule]
   BART Pipeline → summarizes → Concise Summary
        │
        ▼
[StorageModule]
   Saves → transcript.txt, session.json, summary.txt
        │
        ▼
[EvaluationModule]
   Computes → WER, CER, ROUGE scores
```

## Threading Model

The GUI uses Python threads to prevent UI blocking:
- Transcription runs in a **daemon thread**
- Summarization runs in a **daemon thread**
- UI updates are posted back to the main thread via `tk.after()`
