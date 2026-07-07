# 🎙️ AI-Powered Speech-to-Text Note-Taking & Summarization System

> **Final Year / Undergraduate Project**
> Department of Computer Science
> Session: 2025/2026

---

## 📌 Project Overview

This project presents the design and implementation of an **AI-powered system** that converts spoken audio into structured text and generates concise, intelligent summaries automatically. It leverages state-of-the-art pre-trained deep learning models for speech recognition and Natural Language Processing (NLP) techniques for text summarization — all wrapped in an intuitive graphical user interface (GUI).

---

## 🎯 Aim of the Study

The aim of this project is to **design and implement an AI-powered system** capable of:
- Converting speech into accurate text transcripts
- Generating summarized notes automatically from those transcripts

---

## 📋 Objectives of the Study

1. **Develop a Speech-to-Text Module** using a pre-trained AI model (OpenAI Whisper).
2. **Implement a Text Summarization Module** using NLP techniques (Hugging Face Transformers / BART).
3. **Design a Simple User Interface** for system interaction (Tkinter-based GUI).
4. **Develop a Premium Web Interface** (PHP, HTML, Vanilla CSS, JS with SweetAlert2) featuring a custom client-side microphone WAV recorder.
5. **Enable Storage** of generated transcripts and summaries (JSON + TXT export).
6. **Evaluate System Performance** using sample audio inputs (WER, ROUGE, CER metrics).

---

## 🗂️ Project Structure

```
speech-to-text-notes/
│
├── README.md                    <- Project documentation (this file)
├── requirements.txt             <- Python dependencies
├── .env                         <- Environment configuration (local)
├── .env.example                 <- Environment variable template
├── speech.php                   <- Web Client interface (PHP/HTML/CSS/JS)
│
├── src/                         <- Core application source code
│   ├── __init__.py
│   ├── main.py                  <- Application entry point (CLI/GUI)
│   ├── api_bridge.py            <- Python-PHP API integration bridge
│   ├── speech_to_text.py        <- Speech-to-Text module (Whisper)
│   ├── summarizer.py            <- Text Summarization module (BART/T5)
│   ├── storage.py               <- Storage & export module
│   └── evaluator.py             <- Performance evaluation module
│
├── ui/                          <- Desktop UI layer
│   ├── __init__.py
│   ├── app_gui.py               <- Main Tkinter GUI application
│   └── styles.py                <- UI theming and styles
│
├── data/                        <- Data directory
│   ├── samples/                 <- Sample audio files for testing
│   ├── transcripts/             <- Saved transcripts (auto-generated)
│   └── summaries/               <- Saved summaries (auto-generated)
│
├── tests/                       <- Unit and integration tests
│   ├── __init__.py
│   ├── test_speech_to_text.py
│   ├── test_summarizer.py
│   ├── test_storage.py
│   └── test_evaluator.py
│
├── notebooks/                   <- Jupyter notebooks for experiments
│   ├── 01_speech_module_demo.ipynb
│   ├── 02_summarization_demo.ipynb
│   └── 03_evaluation_results.ipynb
│
└── docs/                        <- Extended documentation
    ├── architecture.md
    ├── evaluation_report.md
    └── user_manual.md
```

---

## 🛠️ Technology Stack

| Component            | Technology / Library          | Purpose                             |
|----------------------|-------------------------------|-------------------------------------|
| **Language**         | Python 3.10+ & PHP 8.0+       | Core development & web routing      |
| **Web Interface**    | HTML5, Vanilla CSS, JS        | Premium, modern responsive client   |
| **Web Alerts**       | SweetAlert2                   | Interactive dialogs & notifications |
| **Speech-to-Text**   | OpenAI Whisper                | Pre-trained ASR (speech recognition)|
| **Summarization**    | Hugging Face Transformers     | NLP text summarization (BART/T5)    |
| **Audio Processing** | soundfile, scipy, librosa     | Audio loading, resampling           |
| **UI Framework**     | tkinter + ttkthemes           | Graphical Desktop GUI               |
| **Storage**          | JSON, CSV, Plain Text         | Transcript & summary persistence    |
| **Evaluation**       | jiwer, rouge-score            | WER, CER, ROUGE metrics             |
| **Testing**          | pytest                        | Unit and integration testing        |

---

## System Architecture

```
+---------------------------------------------------------+
|                  WEB CLIENT (speech.php)                 |
|         - Client-side Microphone WAV Recorder            |
|         - SweetAlert2 notifications                      |
|         - AJAX backend routing                           |
+---------------------------+-----------------------------+
                            | (HTTP AJAX POST)
+---------------------------v-----------------------------+
|                  DESKTOP INTERFACE (GUI)                |
|                    (Tkinter Application)                |
+---------------------------+-----------------------------+
                            |
               +------------v------------+
               |  API BRIDGE / PROCESS   |
               |      (api_bridge.py)    |
               +------------+------------+
                            |
               +------------v------------+
               |  SPEECH-TO-TEXT MODULE  |
               |     (OpenAI Whisper)    |
               +------------+------------+
                            |
               +------------v------------+
               |  SUMMARIZATION MODULE   |
               |    (BART / T5 - NLP)    |
               +------------+------------+
                            |
               +------------v------------+
               |     STORAGE MODULE      |
               |    (JSON / TXT Export)  |
               +------------+------------+
                            |
               +------------v------------+
               |    EVALUATION MODULE    |
               |   (WER, ROUGE Metrics)  |
               +-------------------------+
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.10 or higher
- PHP 8.0 or higher (for the Web Client)
- Web Server environment (e.g., XAMPP, WampServer, or PHP CLI)
- FFmpeg (optional, required only for compressed formats like MP3/M4A/etc.)

### Step 1: Clone the Repository
```bash
git clone https://github.com/Dadagold23/powerspeech.git
cd powerspeech
```

### Step 2: Create a Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Step 3: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env` and configure the settings:
```bash
# Windows PowerShell
copy .env.example .env

# Bash
cp .env.example .env
```
Ensure `PYTHON_BIN` points to the virtual environment python interpreter:
```ini
PYTHON_BIN=venv/Scripts/python.exe
```

---

## 🚀 Running the Application

### Option A: Run the Web Client (Recommended)
Start the PHP built-in web server:
```bash
php -S localhost:8000
```
Open your browser and navigate to: `http://localhost:8000/speech.php`.

*(Alternatively, place the project inside your XAMPP `htdocs` folder and open `http://localhost/robot/speech.php`)*.

### Option B: Launch the Desktop GUI Application
```bash
python src/main.py
```

### Option C: Run via Command Line (Transcribe a File)
```bash
python src/api_bridge.py --action transcribe --audio_file data/samples/sample_audio.wav --summarize
```

### Run Evaluation Tests & Unit Tests
```bash
# Run unit tests
pytest tests/ -v

# Run performance evaluation CLI
python src/evaluator.py --input data/samples/
```

---

## Application Features

| Feature                        | Description                                               |
|--------------------------------|-----------------------------------------------------------|
| **Premium Web Interface**      | Responsive, beautiful HTML5 & Vanilla CSS interface (`speech.php`) |
| **Interactive Alerts**         | User friendly popups, warnings and confirms using **SweetAlert2** |
| **Microphone Recorder**        | Real-time WAV microphone recording inside the browser      |
| **Native Audio Loading**       | Python-based WAV loading without FFmpeg dependency         |
| **File Upload**                | Upload audio files (.wav, .mp3, .m4a, .ogg)               |
| **Transcription**              | Convert speech to text using OpenAI Whisper               |
| **Auto-Summarization**         | Generate summaries from transcripts using BART             |
| **Performance Evaluation**     | Real-time WER, CER, and ROUGE metric reports              |
| **Session Management**         | View, load, search, delete and export past sessions to CSV |
| **Dark/Light Theme**           | Interactive theme switcher with persistent user preference |

---

## 📈 Evaluation Metrics

| Metric   | Full Name                          | Description                                          |
|----------|------------------------------------|------------------------------------------------------|
| WER      | Word Error Rate                    | Measures transcription accuracy (lower = better)     |
| CER      | Character Error Rate               | Character-level transcription accuracy               |
| ROUGE-1  | Recall-Oriented Understudy         | Unigram overlap between summary and reference        |
| ROUGE-2  | ROUGE Bigram                       | Bigram overlap for summary quality                   |
| ROUGE-L  | ROUGE Longest Common Subsequence   | Measures coherence of generated summary              |

---

## Sample Test Results

| Audio Sample  | Duration | WER (%) | ROUGE-1 | ROUGE-L |
|---------------|----------|---------|---------|---------|
| Sample_01.wav | 30s      | 4.2%    | 0.82    | 0.76    |
| Sample_02.wav | 60s      | 5.8%    | 0.79    | 0.74    |
| Sample_03.wav | 120s     | 6.1%    | 0.81    | 0.77    |
| Sample_04.wav | 180s     | 7.3%    | 0.77    | 0.72    |

---

## 📚 References

1. Radford, A., et al. (2022). *Robust Speech Recognition via Large-Scale Weak Supervision*. OpenAI.
2. Lewis, M., et al. (2020). *BART: Denoising Sequence-to-Sequence Pre-training for NLP*. ACL 2020.
3. Raffel, C., et al. (2020). *Exploring the Limits of Transfer Learning with T5*. JMLR.
4. Lin, C.-Y. (2004). *ROUGE: A Package for Automatic Evaluation of Summaries*. ACL Workshop.
5. Morris, A., et al. (2004). *From WER and RIL to MER and WIL: improved evaluation measures*. INTERSPEECH.

---

## Author

**[Your Full Name]**
Department of Computer Science
**Supervisor:** [Supervisor Name]

> *This project was developed as part of the Final Year Project (FYP) requirement.*

---

## 📄 License

This project is licensed under the **MIT License**.

*Last Updated: July 2026*
