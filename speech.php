<?php
/**
 * AI Speech Notes - Web Client Interface (speech.php)
 * 
 * Provides an interactive, high-performance, AJAX-driven web interface
 * mirroring the system’s Tkinter GUI features.
 * 
 * Features:
 * - Load environment configurations from .env
 * - Route AJAX actions (transcribe, list/load/delete sessions, evaluate, summarize)
 * - Custom WAV microphone recorder in JS (no server-side FFmpeg required for mic!)
 * - Dark & Light themes with persistent state
 * 
 * Department of Computer Science, Session 2025/2026.
 */

// 1. Env Loader Configuration
function loadEnv($path) {
    if (!file_exists($path)) {
        return;
    }
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) {
            continue;
        }
        $parts = explode('=', $line, 2);
        if (count($parts) === 2) {
            $name = trim($parts[0]);
            $value = trim($parts[1]);
            $value = trim($value, "\"'");
            if (!array_key_exists($name, $_SERVER) && !array_key_exists($name, $_ENV)) {
                putenv("{$name}={$value}");
                $_ENV[$name] = $value;
                $_SERVER[$name] = $value;
            }
        }
    }
}
loadEnv(__DIR__ . '/.env');

// Define PYTHON_BIN constant using env setup
define('PYTHON_BIN', getenv('PYTHON_BIN') ?: 'venv/Scripts/python.exe');

// Set upload and temp directories
$uploadDir = __DIR__ . '/data/samples/uploads';
if (!is_dir($uploadDir)) {
    mkdir($uploadDir, 0777, true);
}

// Response helper
function jsonResponse($ok, $dataOrError) {
    header('Content-Type: application/json');
    if ($ok) {
        echo json_encode(['ok' => true, 'data' => $dataOrError], JSON_UNESCAPED_UNICODE);
    } else {
        echo json_encode(['ok' => false, 'error' => $dataOrError], JSON_UNESCAPED_UNICODE);
    }
    exit;
}

// 2. Router for AJAX Actions
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_GET['action'])) {
    $action = $_GET['action'];
    
    switch ($action) {
        case 'transcribe':
            if (!isset($_FILES['audio_file'])) {
                jsonResponse(false, 'No audio file uploaded.');
            }
            $file = $_FILES['audio_file'];
            if ($file['error'] !== UPLOAD_ERR_OK) {
                jsonResponse(false, 'File upload error: ' . $file['error']);
            }
            
            $ext = pathinfo($file['name'], PATHINFO_EXTENSION);
            $newFileName = 'audio_' . uniqid() . '.' . ($ext ?: 'wav');
            $filePath = $uploadDir . '/' . $newFileName;
            
            if (!move_uploaded_file($file['tmp_name'], $filePath)) {
                jsonResponse(false, 'Failed to save uploaded file.');
            }
            
            $lang = isset($_POST['lang']) ? $_POST['lang'] : 'auto';
            $summarize = isset($_POST['summarize']) && $_POST['summarize'] === 'true';
            
            $cmd = '"' . PYTHON_BIN . '" src/api_bridge.py --action transcribe --file ' . escapeshellarg($filePath) . ' --lang ' . escapeshellarg($lang);
            if ($summarize) {
                $cmd .= ' --summarize';
            }
            
            $output = shell_exec($cmd);
            $res = json_decode($output, true);
            if ($res === null) {
                jsonResponse(false, 'Failed to parse transcription bridge response: ' . trim($output));
            }
            
            if (isset($res['ok']) && $res['ok']) {
                jsonResponse(true, $res['data']);
            } else {
                jsonResponse(false, isset($res['error']) ? $res['error'] : 'Transcription error.');
            }
            break;
            
        case 'transcribe_mic':
            if (!isset($_FILES['audio_file'])) {
                jsonResponse(false, 'No mic audio file uploaded.');
            }
            $file = $_FILES['audio_file'];
            if ($file['error'] !== UPLOAD_ERR_OK) {
                jsonResponse(false, 'File upload error: ' . $file['error']);
            }
            
            // Client-side records directly in WAV format
            $newFileName = 'mic_' . uniqid() . '.wav';
            $filePath = $uploadDir . '/' . $newFileName;
            
            if (!move_uploaded_file($file['tmp_name'], $filePath)) {
                jsonResponse(false, 'Failed to save microphone recording.');
            }
            
            $lang = isset($_POST['lang']) ? $_POST['lang'] : 'auto';
            $summarize = isset($_POST['summarize']) && $_POST['summarize'] === 'true';
            
            $cmd = '"' . PYTHON_BIN . '" src/api_bridge.py --action transcribe_mic --file ' . escapeshellarg($filePath) . ' --lang ' . escapeshellarg($lang);
            if ($summarize) {
                $cmd .= ' --summarize';
            }
            
            $output = shell_exec($cmd);
            $res = json_decode($output, true);
            if ($res === null) {
                jsonResponse(false, 'Failed to parse mic transcription response: ' . trim($output));
            }
            
            if (isset($res['ok']) && $res['ok']) {
                jsonResponse(true, $res['data']);
            } else {
                jsonResponse(false, isset($res['error']) ? $res['error'] : 'Mic transcription error.');
            }
            break;
            
        case 'summarize':
            if (!isset($_POST['text']) || empty(trim($_POST['text']))) {
                jsonResponse(false, 'Transcript text is required.');
            }
            $text = $_POST['text'];
            
            $cmd = '"' . PYTHON_BIN . '" src/api_bridge.py --action summarize --text ' . escapeshellarg($text);
            $output = shell_exec($cmd);
            $res = json_decode($output, true);
            if ($res === null) {
                jsonResponse(false, 'Failed to parse summarizer response: ' . trim($output));
            }
            
            if (isset($res['ok']) && $res['ok']) {
                jsonResponse(true, $res['data']);
            } else {
                jsonResponse(false, isset($res['error']) ? $res['error'] : 'Summarizer error.');
            }
            break;
            
        case 'save_session':
            if (!isset($_POST['text']) || empty(trim($_POST['text']))) {
                jsonResponse(false, 'Transcript text is required to save.');
            }
            $text = $_POST['text'];
            $summary = isset($_POST['summary']) ? $_POST['summary'] : '';
            $audioFile = isset($_POST['audio_file']) ? $_POST['audio_file'] : 'live_recording';
            $lang = isset($_POST['lang']) ? $_POST['lang'] : 'unknown';
            
            $cmd = '"' . PYTHON_BIN . '" src/api_bridge.py --action save_session --text ' . escapeshellarg($text);
            if (!empty($summary)) {
                $cmd .= ' --ref_summary ' . escapeshellarg($summary);
            }
            if (!empty($audioFile)) {
                $cmd .= ' --file ' . escapeshellarg($audioFile);
            }
            if (!empty($lang)) {
                $cmd .= ' --lang ' . escapeshellarg($lang);
            }
            
            $output = shell_exec($cmd);
            $res = json_decode($output, true);
            if ($res === null) {
                jsonResponse(false, 'Failed to parse save session response: ' . trim($output));
            }
            
            if (isset($res['ok']) && $res['ok']) {
                jsonResponse(true, $res['data']);
            } else {
                jsonResponse(false, isset($res['error']) ? $res['error'] : 'Save session error.');
            }
            break;
            
        case 'list_sessions':
            $cmd = '"' . PYTHON_BIN . '" src/api_bridge.py --action list_sessions';
            $output = shell_exec($cmd);
            $res = json_decode($output, true);
            if ($res === null) {
                jsonResponse(false, 'Failed to parse list sessions response: ' . trim($output));
            }
            
            if (isset($res['ok']) && $res['ok']) {
                jsonResponse(true, $res['data']);
            } else {
                jsonResponse(false, isset($res['error']) ? $res['error'] : 'List sessions error.');
            }
            break;
            
        case 'load_session':
            if (!isset($_POST['session_id']) || empty(trim($_POST['session_id']))) {
                jsonResponse(false, 'Session ID is required.');
            }
            $sessionId = $_POST['session_id'];
            
            $cmd = '"' . PYTHON_BIN . '" src/api_bridge.py --action load_session --session_id ' . escapeshellarg($sessionId);
            $output = shell_exec($cmd);
            $res = json_decode($output, true);
            if ($res === null) {
                jsonResponse(false, 'Failed to parse load session response: ' . trim($output));
            }
            
            if (isset($res['ok']) && $res['ok']) {
                jsonResponse(true, $res['data']);
            } else {
                jsonResponse(false, isset($res['error']) ? $res['error'] : 'Load session error.');
            }
            break;
            
        case 'delete_session':
            if (!isset($_POST['session_id']) || empty(trim($_POST['session_id']))) {
                jsonResponse(false, 'Session ID is required.');
            }
            $sessionId = $_POST['session_id'];
            
            $cmd = '"' . PYTHON_BIN . '" src/api_bridge.py --action delete_session --session_id ' . escapeshellarg($sessionId);
            $output = shell_exec($cmd);
            $res = json_decode($output, true);
            if ($res === null) {
                jsonResponse(false, 'Failed to parse delete session response: ' . trim($output));
            }
            
            if (isset($res['ok']) && $res['ok']) {
                jsonResponse(true, $res['data']);
            } else {
                jsonResponse(false, isset($res['error']) ? $res['error'] : 'Delete session error.');
            }
            break;
            
        case 'evaluate':
            if (!isset($_POST['ref_transcript']) || !isset($_POST['hyp_transcript'])) {
                jsonResponse(false, 'Reference and hypothesis transcripts are required.');
            }
            $refTranscript = $_POST['ref_transcript'];
            $hypTranscript = $_POST['hyp_transcript'];
            $refSummary = isset($_POST['ref_summary']) ? $_POST['ref_summary'] : '';
            $genSummary = isset($_POST['gen_summary']) ? $_POST['gen_summary'] : '';
            
            $cmd = '"' . PYTHON_BIN . '" src/api_bridge.py --action evaluate --ref_transcript ' . escapeshellarg($refTranscript) . ' --hyp_transcript ' . escapeshellarg($hypTranscript);
            if (!empty($refSummary) && !empty($genSummary)) {
                $cmd .= ' --ref_summary ' . escapeshellarg($refSummary) . ' --gen_summary ' . escapeshellarg($genSummary);
            }
            
            $output = shell_exec($cmd);
            $res = json_decode($output, true);
            if ($res === null) {
                jsonResponse(false, 'Failed to parse evaluation response: ' . trim($output));
            }
            
            if (isset($res['ok']) && $res['ok']) {
                jsonResponse(true, $res['data']);
            } else {
                jsonResponse(false, isset($res['error']) ? $res['error'] : 'Evaluation error.');
            }
            break;
            
        default:
            jsonResponse(false, 'Invalid action specified.');
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="AI Speech Notes: Auto-generate text notes and summaries from your speech and audio files using Whisper & BART.">
    <title>AI Speech Notes — Speech-to-Text & Summarizer</title>
    
    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&family=Plus+Jakarta+Sans:wght@400;500;600&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    
    <!-- SweetAlert2 -->
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    
    <style>
        :root {
            /* GitHub-inspired Sleek Dark Theme (Default) */
            --bg-primary: #0D1117;
            --bg-secondary: #161B22;
            --bg-card: #1C2128;
            --bg-input: #21262D;
            --accent: #2EA043;
            --accent-hover: #3FB950;
            --accent-danger: #DA3633;
            --accent-danger-hover: #F85149;
            --accent-warn: #E3B341;
            --accent-warn-hover: #F2C75C;
            --accent-blue: #388BFD;
            --accent-blue-hover: #58A6FF;
            --text-primary: #E6EDF3;
            --text-secondary: #8B949E;
            --border: #30363D;
            --shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            
            --font-display: 'Outfit', 'Segoe UI', sans-serif;
            --font-body: 'Plus Jakarta Sans', 'Segoe UI', sans-serif;
            --font-mono: 'Fira Code', 'Consolas', monospace;
            --radius: 8px;
            --transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }

        body.light-theme {
            /* GitHub-inspired Sleek Light Theme */
            --bg-primary: #FFFFFF;
            --bg-secondary: #F6F8FA;
            --bg-card: #FFFFFF;
            --bg-input: #F6F8FA;
            --accent: #1A7F37;
            --accent-hover: #2EA043;
            --accent-danger: #CF222E;
            --accent-danger-hover: #A01B24;
            --accent-warn: #9A6700;
            --accent-warn-hover: #BF8000;
            --accent-blue: #0969DA;
            --accent-blue-hover: #1A84FF;
            --text-primary: #1F2328;
            --text-secondary: #656D76;
            --border: #D0D7DE;
            --shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: var(--font-body);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            transition: var(--transition);
        }

        /* ── Header ── */
        header {
            background-color: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            height: 64px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
            transition: var(--transition);
            z-index: 10;
        }

        .header-title-container {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .header-title-container h1 {
            font-family: var(--font-display);
            font-size: 20px;
            font-weight: 800;
            background: linear-gradient(90deg, var(--accent-blue), var(--accent-hover));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header-meta {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .header-tag {
            font-size: 12px;
            color: var(--text-secondary);
            font-family: var(--font-display);
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .btn-theme-toggle {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 6px 12px;
            border-radius: var(--radius);
            font-family: var(--font-display);
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .btn-theme-toggle:hover {
            color: var(--text-primary);
            border-color: var(--text-secondary);
        }

        /* ── Action Toolbar ── */
        .toolbar {
            background-color: var(--bg-card);
            border-bottom: 1px solid var(--border);
            padding: 12px 24px;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            flex-wrap: wrap;
            gap: 12px;
            transition: var(--transition);
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 600;
            border-radius: var(--radius);
            border: 1px solid transparent;
            cursor: pointer;
            color: #FFFFFF;
            font-family: var(--font-display);
            transition: var(--transition);
            gap: 8px;
        }

        .btn-blue {
            background-color: var(--accent-blue);
        }
        .btn-blue:hover {
            background-color: var(--accent-blue-hover);
        }
        .btn-danger {
            background-color: var(--accent-danger);
        }
        .btn-danger:hover {
            background-color: var(--accent-danger-hover);
        }
        .btn-warn {
            background-color: var(--accent-warn);
        }
        .btn-warn:hover {
            background-color: var(--accent-warn-hover);
        }
        .btn-success {
            background-color: var(--accent);
        }
        .btn-success:hover {
            background-color: var(--accent-hover);
        }
        .btn-clear {
            background-color: transparent;
            border-color: var(--border);
            color: var(--text-secondary);
        }
        .btn-clear:hover {
            color: var(--text-primary);
            border-color: var(--text-secondary);
        }

        .toolbar-group {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            color: var(--text-secondary);
        }

        .toolbar-group label {
            font-weight: 500;
        }

        .select-input, .number-input {
            background-color: var(--bg-input);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 6px 12px;
            border-radius: var(--radius);
            outline: none;
            font-family: var(--font-body);
            transition: var(--transition);
        }

        .select-input:focus, .number-input:focus {
            border-color: var(--accent-blue);
        }

        .number-input {
            width: 70px;
            text-align: center;
        }

        /* ── Tabs Navigation ── */
        .tabs-nav {
            display: flex;
            background-color: var(--bg-primary);
            padding: 12px 24px 0 24px;
            border-bottom: 1px solid var(--border);
            gap: 4px;
        }

        .tab-link {
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
            color: var(--text-secondary);
            background: transparent;
            border: none;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            font-family: var(--font-display);
            transition: var(--transition);
        }

        .tab-link:hover {
            color: var(--text-primary);
        }

        .tab-link.active {
            color: var(--text-primary);
            border-bottom-color: var(--accent-blue);
        }

        /* ── Content Panes ── */
        .main-content {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            position: relative;
        }

        .tab-pane {
            display: none;
            height: 100%;
        }

        .tab-pane.active {
            display: block;
        }

        /* ── Panel Layouts (Two-Panel for main) ── */
        .panels-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            height: 100%;
        }

        @media (max-width: 768px) {
            .panels-grid {
                grid-template-columns: 1fr;
            }
        }

        .panel {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: var(--shadow);
            transition: var(--transition);
        }

        .panel-header {
            background-color: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            padding: 12px 18px;
            font-family: var(--font-display);
            font-size: 15px;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .panel-body {
            flex: 1;
            display: flex;
            flex-direction: column;
        }

        .panel-textarea {
            flex: 1;
            width: 100%;
            min-height: 380px;
            background-color: var(--bg-input);
            color: var(--text-primary);
            border: none;
            padding: 16px;
            font-family: var(--font-mono);
            font-size: 14px;
            line-height: 1.6;
            resize: none;
            outline: none;
        }

        .panel-textarea:focus {
            background-color: var(--bg-card);
        }

        .panel-footer {
            background-color: var(--bg-secondary);
            border-top: 1px solid var(--border);
            padding: 10px 18px;
            font-size: 12px;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        /* ── Progress Indicators ── */
        .progress-bar-container {
            width: 100%;
            height: 4px;
            background-color: var(--bg-input);
            position: relative;
            overflow: hidden;
            border-radius: 2px;
            margin-bottom: 16px;
            display: none;
        }

        .progress-bar-fill {
            height: 100%;
            background-color: var(--accent-blue);
            position: absolute;
            width: 30%;
            animation: progress-slide 1.5s infinite linear;
        }

        @keyframes progress-slide {
            0% { left: -30%; }
            100% { left: 100%; }
        }

        /* ── Evaluation Layout ── */
        .eval-container {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .eval-header {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .eval-header h2 {
            font-family: var(--font-display);
            font-size: 18px;
        }

        .eval-header p {
            font-size: 13px;
            color: var(--text-secondary);
        }

        .eval-inputs {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        @media (max-width: 768px) {
            .eval-inputs {
                grid-template-columns: 1fr;
            }
        }

        .eval-textarea {
            width: 100%;
            height: 160px;
            background-color: var(--bg-input);
            color: var(--text-primary);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 12px;
            font-family: var(--font-mono);
            font-size: 13px;
            resize: none;
            outline: none;
            transition: var(--transition);
        }

        .eval-textarea:focus {
            border-color: var(--accent-blue);
        }

        .eval-results-container {
            border: 1px solid var(--border);
            border-radius: var(--radius);
            background-color: var(--bg-card);
            overflow: hidden;
            box-shadow: var(--shadow);
        }

        .eval-results-body {
            background-color: var(--bg-input);
            padding: 16px;
            font-family: var(--font-mono);
            font-size: 13px;
            line-height: 1.5;
            color: var(--text-primary);
            white-space: pre-wrap;
            overflow-y: auto;
            max-height: 250px;
            min-height: 150px;
        }

        /* ── Session History Layout ── */
        .history-container {
            display: flex;
            flex-direction: column;
            gap: 16px;
            height: 100%;
        }

        .history-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .history-header h2 {
            font-family: var(--font-display);
            font-size: 18px;
        }

        .history-controls {
            display: flex;
            gap: 8px;
        }

        .table-container {
            border: 1px solid var(--border);
            border-radius: var(--radius);
            overflow: hidden;
            background-color: var(--bg-card);
            box-shadow: var(--shadow);
            max-height: 400px;
            overflow-y: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            text-align: left;
        }

        th {
            background-color: var(--bg-secondary);
            color: var(--text-primary);
            font-weight: 600;
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
            font-family: var(--font-display);
        }

        td {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
            color: var(--text-secondary);
            max-width: 250px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        tr {
            cursor: pointer;
            transition: var(--transition);
        }

        tr:hover td {
            color: var(--text-primary);
            background-color: var(--bg-input);
        }

        tr.selected td {
            background-color: var(--bg-input);
            color: var(--text-primary);
        }

        .history-actions {
            display: flex;
            gap: 10px;
        }

        /* ── Status Bar ── */
        .statusbar {
            background-color: var(--bg-secondary);
            border-top: 1px solid var(--border);
            height: 32px;
            display: flex;
            align-items: center;
            padding: 0 24px;
            font-size: 12px;
            color: var(--text-secondary);
            transition: var(--transition);
        }

        /* ── Audio Record Badge Animation ── */
        .recording-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background-color: var(--accent-danger);
            color: #FFFFFF;
            padding: 4px 8px;
            border-radius: 4px;
            font-family: var(--font-display);
            font-weight: 600;
            font-size: 11px;
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>

    <!-- Header -->
    <header>
        <div class="header-title-container">
            <span>🎙️</span>
            <h1>POWERSpeech Noting</h1>
        </div>
        <div class="header-meta">
            <span class="header-tag">v1.2  |  PowerSpeech</span>
            <button class="btn-theme-toggle" id="themeToggleBtn">
                <span id="themeToggleIcon">🌙</span> <span id="themeToggleText">Dark Mode</span>
            </button>
        </div>
    </header>

    <!-- Action Toolbar -->
    <div class="toolbar">
        <button class="btn btn-blue" id="btnUpload">
            <span>📂</span> Upload Audio
        </button>
        <input type="file" id="audioFileInput" accept=".wav,.mp3,.m4a,.ogg,.flac,.aac" style="display: none;">
        
        <button class="btn btn-danger" id="btnRecord">
            <span>🔴</span> Start Recording
        </button>
        
        <div class="toolbar-group">
            <label for="duration">Duration (s):</label>
            <input type="number" id="duration" class="number-input" value="30" min="5" max="300" step="5">
        </div>

        <div class="toolbar-group">
            <label for="language">Language:</label>
            <select id="language" class="select-input">
                <option value="auto">auto</option>
                <option value="en">en</option>
                <option value="fr">fr</option>
                <option value="de">de</option>
                <option value="es">es</option>
                <option value="it">it</option>
                <option value="pt">pt</option>
                <option value="nl">nl</option>
                <option value="pl">pl</option>
                <option value="ru">ru</option>
                <option value="zh">zh</option>
                <option value="ja">ja</option>
                <option value="ko">ko</option>
                <option value="ar">ar</option>
                <option value="hi">hi</option>
                <option value="tr">tr</option>
                <option value="vi">vi</option>
                <option value="uk">uk</option>
                <option value="cs">cs</option>
                <option value="sv">sv</option>
                <option value="ro">ro</option>
                <option value="hu">hu</option>
                <option value="fi">fi</option>
                <option value="da">da</option>
                <option value="no">no</option>
                <option value="id">id</option>
                <option value="th">th</option>
                <option value="he">he</option>
            </select>
        </div>

        <button class="btn btn-warn" id="btnSummarize">
            <span>📝</span> Summarize
        </button>

        <button class="btn btn-success" id="btnSave">
            <span>💾</span> Save Session
        </button>

        <button class="btn btn-clear" id="btnClear" style="margin-left: auto;">
            <span>🧹</span> Clear
        </button>
    </div>

    <!-- Tabs Navigation -->
    <div class="tabs-nav">
        <button class="tab-link active" data-target="tabMain">Transcript & Summary</button>
        <button class="tab-link" data-target="tabEval">Evaluation</button>
        <button class="tab-link" data-target="tabHistory">Session History</button>
    </div>

    <!-- Main Content -->
    <div class="main-content">
        <!-- Floating Progress Bar -->
        <div class="progress-bar-container" id="progressBar">
            <div class="progress-bar-fill"></div>
        </div>

        <!-- Tab 1: Main Panel -->
        <div class="tab-pane active" id="tabMain">
            <div class="panels-grid">
                <!-- Left Panel: Transcript -->
                <div class="panel">
                    <div class="panel-header">
                        <span>Transcript</span>
                        <span id="recordingBadge" style="display: none;" class="recording-badge">🔴 RECORDING</span>
                    </div>
                    <div class="panel-body">
                        <textarea class="panel-textarea" id="txtTranscript" placeholder="Audio transcript will appear here. You can also edit it manually..."></textarea>
                    </div>
                    <div class="panel-footer">
                        <span id="lblLang">Language: —</span>
                        <span id="lblWords">Words: 0</span>
                    </div>
                </div>

                <!-- Right Panel: Summary -->
                <div class="panel">
                    <div class="panel-header">
                        <span>AI Summary</span>
                    </div>
                    <div class="panel-body">
                        <textarea class="panel-textarea" id="txtSummary" placeholder="AI-generated notes and summaries will appear here..."></textarea>
                    </div>
                    <div class="panel-footer">
                        <span id="lblRouge">ROUGE: —</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tab 2: Evaluation Panel -->
        <div class="tab-pane" id="tabEval">
            <div class="eval-container">
                <div class="eval-header">
                    <h2>Performance Evaluation</h2>
                    <p>Paste the reference (ground-truth) transcript and summary, then click Run Evaluation to measure Word Error Rate (WER) and ROUGE overlap scores.</p>
                </div>
                
                <div class="eval-inputs">
                    <div>
                        <div style="font-size: 13px; font-weight: 600; margin-bottom: 6px;">Reference Transcript</div>
                        <textarea class="eval-textarea" id="txtRefTranscript" placeholder="Paste ground-truth transcript here..."></textarea>
                    </div>
                    <div>
                        <div style="font-size: 13px; font-weight: 600; margin-bottom: 6px;">Reference Summary</div>
                        <textarea class="eval-textarea" id="txtRefSummary" placeholder="Paste ground-truth summary here..."></textarea>
                    </div>
                </div>

                <div style="text-align: center;">
                    <button class="btn btn-blue" id="btnRunEval">
                        <span>📊</span> Run Evaluation
                    </button>
                </div>

                <div class="eval-results-container">
                    <div class="panel-header" style="border-bottom: 1px solid var(--border);">
                        <span>Results</span>
                    </div>
                    <pre class="eval-results-body" id="preEvalResults">Ready. Paste references and run evaluation.</pre>
                </div>
            </div>
        </div>

        <!-- Tab 3: Session History Panel -->
        <div class="tab-pane" id="tabHistory">
            <div class="history-container">
                <div class="history-header">
                    <h2>Saved Sessions</h2>
                    <div class="history-controls">
                        <button class="btn btn-blue" id="btnRefreshHistory">Refresh</button>
                        <button class="btn btn-success" id="btnExportCSV">Export CSV</button>
                    </div>
                </div>

                <div class="table-container">
                    <table id="tblSessions">
                        <thead>
                            <tr>
                                <th>Session ID</th>
                                <th>Created At</th>
                                <th>Audio Source</th>
                                <th>Language</th>
                            </tr>
                        </thead>
                        <tbody id="tblSessionsBody">
                            <tr>
                                <td colspan="4" style="text-align: center; color: var(--text-secondary);">No sessions loaded. Click Refresh to scan.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="history-actions">
                    <button class="btn btn-blue" id="btnLoadSession">Load Session</button>
                    <button class="btn btn-danger" id="btnDeleteSession">Delete Session</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Status Bar -->
    <div class="statusbar" id="statusbar">
        Ready. Upload an audio file or start recording.
    </div>

    <!-- JavaScript WAV Recording & AJAX Logic -->
    <script>
        // ── State Management ──
        let currentTheme = localStorage.getItem('theme') || 'dark';
        let isRecording = false;
        let recordingTimer = null;
        let recordingSeconds = 0;
        let maxRecordingSeconds = 30;
        let lastAudioPath = '';
        let detectedLanguage = 'unknown';
        let sessionsList = [];
        let selectedSessionIndex = -1;

        // Custom WAV recorder helper
        class WAVRecorder {
            constructor() {
                this.audioContext = null;
                this.processor = null;
                this.input = null;
                this.leftChannel = [];
                this.recordingLength = 0;
                this.sampleRate = 16000;
            }

            async start() {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                    sampleRate: this.sampleRate
                });
                this.sampleRate = this.audioContext.sampleRate;
                this.input = this.audioContext.createMediaStreamSource(stream);
                this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
                
                this.leftChannel = [];
                this.recordingLength = 0;
                
                this.processor.onaudioprocess = (e) => {
                    const left = e.inputBuffer.getChannelData(0);
                    this.leftChannel.push(new Float32Array(left));
                    this.recordingLength += left.length;
                };
                
                this.input.connect(this.processor);
                this.processor.connect(this.audioContext.destination);
                this.stream = stream;
            }

            stop() {
                if (this.processor) {
                    this.processor.disconnect();
                    this.input.disconnect();
                    this.stream.getTracks().forEach(track => track.stop());
                    
                    const samples = new Float32Array(this.recordingLength);
                    let offset = 0;
                    for (let i = 0; i < this.leftChannel.length; i++) {
                        samples.set(this.leftChannel[i], offset);
                        offset += this.leftChannel[i].length;
                    }
                    
                    const buffer = new ArrayBuffer(44 + samples.length * 2);
                    const view = new DataView(buffer);
                    
                    this.writeString(view, 0, 'RIFF');
                    view.setUint32(4, 36 + samples.length * 2, true);
                    this.writeString(view, 8, 'WAVE');
                    this.writeString(view, 12, 'fmt ');
                    view.setUint32(16, 16, true);
                    view.setUint16(20, 1, true);
                    view.setUint16(22, 1, true);
                    view.setUint32(24, this.sampleRate, true);
                    view.setUint32(28, this.sampleRate * 2, true);
                    view.setUint16(32, 2, true);
                    view.setUint16(34, 16, true);
                    this.writeString(view, 36, 'data');
                    view.setUint32(40, samples.length * 2, true);
                    
                    this.floatTo16BitPCM(view, 44, samples);
                    return new Blob([view], { type: 'audio/wav' });
                }
                return null;
            }

            writeString(view, offset, string) {
                for (let i = 0; i < string.length; i++) {
                    view.setUint8(offset + i, string.charCodeAt(i));
                }
            }

            floatTo16BitPCM(output, offset, input) {
                for (let i = 0; i < input.length; i++, offset += 2) {
                    let s = Math.max(-1, Math.min(1, input[i]));
                    output.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
                }
            }
        }

        const recorder = new WAVRecorder();

        // ── DOM Elements ──
        const themeToggleBtn = document.getElementById('themeToggleBtn');
        const themeToggleIcon = document.getElementById('themeToggleIcon');
        const themeToggleText = document.getElementById('themeToggleText');
        const btnUpload = document.getElementById('btnUpload');
        const audioFileInput = document.getElementById('audioFileInput');
        const btnRecord = document.getElementById('btnRecord');
        const btnSummarize = document.getElementById('btnSummarize');
        const btnSave = document.getElementById('btnSave');
        const btnClear = document.getElementById('btnClear');
        const durationInput = document.getElementById('duration');
        const languageSelect = document.getElementById('language');
        const progressBar = document.getElementById('progressBar');
        const recordingBadge = document.getElementById('recordingBadge');
        const txtTranscript = document.getElementById('txtTranscript');
        const txtSummary = document.getElementById('txtSummary');
        const lblLang = document.getElementById('lblLang');
        const lblWords = document.getElementById('lblWords');
        const lblRouge = document.getElementById('lblRouge');
        const statusbar = document.getElementById('statusbar');
        const tabLinks = document.querySelectorAll('.tab-link');
        const tabPanes = document.querySelectorAll('.tab-pane');

        // Evaluation Elements
        const txtRefTranscript = document.getElementById('txtRefTranscript');
        const txtRefSummary = document.getElementById('txtRefSummary');
        const btnRunEval = document.getElementById('btnRunEval');
        const preEvalResults = document.getElementById('preEvalResults');

        // History Elements
        const btnRefreshHistory = document.getElementById('btnRefreshHistory');
        const btnExportCSV = document.getElementById('btnExportCSV');
        const tblSessionsBody = document.getElementById('tblSessionsBody');
        const btnLoadSession = document.getElementById('btnLoadSession');
        const btnDeleteSession = document.getElementById('btnDeleteSession');

        // ── Initialization ──
        applyTheme(currentTheme);
        updateWordCount();
        txtTranscript.addEventListener('input', updateWordCount);

        // ── Event Listeners ──
        themeToggleBtn.addEventListener('click', toggleTheme);

        // Tab Switching
        tabLinks.forEach(link => {
            link.addEventListener('click', () => {
                tabLinks.forEach(l => l.classList.remove('active'));
                tabPanes.forEach(p => p.classList.remove('active'));
                link.classList.add('active');
                document.getElementById(link.dataset.target).classList.add('active');
                
                // Special actions on tab load
                if (link.dataset.target === 'tabHistory') {
                    refreshSessionsList();
                }
            });
        });

        // Clear Outputs
        btnClear.addEventListener('click', () => {
            txtTranscript.value = '';
            txtSummary.value = '';
            lblLang.textContent = 'Language: —';
            lblWords.textContent = 'Words: 0';
            lblRouge.textContent = 'ROUGE: —';
            lastAudioPath = '';
            detectedLanguage = 'unknown';
            updateStatus('Cleared.');
        });

        // Trigger file input upload
        btnUpload.addEventListener('click', () => {
            audioFileInput.click();
        });

        audioFileInput.addEventListener('change', () => {
            if (audioFileInput.files.length === 0) return;
            const file = audioFileInput.files[0];
            transcribeFile(file);
        });

        // Microphone Recording
        btnRecord.addEventListener('click', toggleMicrophoneRecording);

        // Summarize current transcript
        btnSummarize.addEventListener('click', generateSummary);

        // Save current session
        btnSave.addEventListener('click', saveSession);

        // Run Performance Evaluation
        btnRunEval.addEventListener('click', runEvaluation);

        // History Controls
        btnRefreshHistory.addEventListener('click', refreshSessionsList);
        btnLoadSession.addEventListener('click', loadSelectedSession);
        btnDeleteSession.addEventListener('click', deleteSelectedSession);
        btnExportCSV.addEventListener('click', exportCSV);

        // ── Helper Functions ──
        function updateStatus(msg) {
            statusbar.textContent = msg;
        }

        function alertUser(type, title, message, html = '') {
            const isLight = document.body.classList.contains('light-theme');
            Swal.fire({
                icon: type, // 'success', 'error', 'warning', 'info'
                title: title,
                text: html ? undefined : message,
                html: html ? html : undefined,
                background: isLight ? '#FFFFFF' : '#1C2128',
                color: isLight ? '#1F2328' : '#E6EDF3',
                confirmButtonColor: isLight ? '#0969DA' : '#388BFD'
            });
        }

        function showLoading(show) {
            progressBar.style.display = show ? 'block' : 'none';
            // Disable actions during loading
            btnUpload.disabled = show;
            btnRecord.disabled = show;
            btnSummarize.disabled = show;
            btnSave.disabled = show;
            btnClear.disabled = show;
        }

        function updateWordCount() {
            const text = txtTranscript.value.trim();
            const count = text ? text.split(/\s+/).length : 0;
            lblWords.textContent = `Words: ${count}`;
        }

        function applyTheme(theme) {
            if (theme === 'light') {
                document.body.classList.add('light-theme');
                themeToggleIcon.textContent = '☀️';
                themeToggleText.textContent = 'Light Mode';
            } else {
                document.body.classList.remove('light-theme');
                themeToggleIcon.textContent = '🌙';
                themeToggleText.textContent = 'Dark Mode';
            }
            localStorage.setItem('theme', theme);
        }

        function toggleTheme() {
            currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(currentTheme);
        }

        // ── Audio Upload Transcription ──
        function transcribeFile(file) {
            updateStatus(`Uploading and transcribing: ${file.name}...`);
            showLoading(true);

            const formData = new FormData();
            formData.append('audio_file', file);
            formData.append('lang', languageSelect.value);
            formData.append('summarize', 'true');

            fetch('speech.php?action=transcribe', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                showLoading(false);
                if (data.ok) {
                    txtTranscript.value = data.data.transcript || '';
                    txtSummary.value = data.data.summary || '';
                    detectedLanguage = data.data.language || 'unknown';
                    lblLang.textContent = `Language: ${detectedLanguage}`;
                    lastAudioPath = data.data.saved.session_json || '';
                    updateWordCount();
                    updateStatus('Transcription complete.');
                } else {
                    updateStatus(`Error: ${data.error}`);
                    alertUser('error', 'Transcription Failed', data.error);
                }
            })
            .catch(err => {
                showLoading(false);
                updateStatus(`Error connecting to transcription API: ${err.message}`);
                console.error(err);
            });
        }

        // ── Microphone Recording Logic ──
        async function toggleMicrophoneRecording() {
            if (!isRecording) {
                // Start
                try {
                    updateStatus('Initializing microphone...');
                    await recorder.start();
                    isRecording = true;
                    btnRecord.innerHTML = '<span>⏹️</span> Stop Recording';
                    btnRecord.classList.remove('btn-danger');
                    btnRecord.classList.add('btn-warn');
                    recordingBadge.style.display = 'inline-flex';
                    
                    recordingSeconds = 0;
                    maxRecordingSeconds = parseInt(durationInput.value) || 30;
                    updateStatus(`Recording: 0s / ${maxRecordingSeconds}s`);
                    
                    recordingTimer = setInterval(() => {
                        recordingSeconds++;
                        updateStatus(`Recording: ${recordingSeconds}s / ${maxRecordingSeconds}s`);
                        if (recordingSeconds >= maxRecordingSeconds) {
                            toggleMicrophoneRecording(); // stop
                        }
                    }, 1000);
                } catch (err) {
                    updateStatus(`Microphone access error: ${err.message}`);
                    alertUser('error', 'Microphone Error', `Could not start recording: ${err.message}`);
                }
            } else {
                // Stop
                isRecording = false;
                clearInterval(recordingTimer);
                recordingTimer = null;
                recordingBadge.style.display = 'none';
                btnRecord.innerHTML = '<span>🔴</span> Start Recording';
                btnRecord.classList.remove('btn-warn');
                btnRecord.classList.add('btn-danger');
                
                updateStatus('Processing recording buffer...');
                const audioBlob = recorder.stop();
                if (audioBlob) {
                    transcribeMicrophone(audioBlob);
                } else {
                    updateStatus('Failed to capture audio buffer.');
                }
            }
        }

        function transcribeMicrophone(audioBlob) {
            updateStatus('Transcribing live voice...');
            showLoading(true);

            const file = new File([audioBlob], 'live_mic.wav', { type: 'audio/wav' });
            const formData = new FormData();
            formData.append('audio_file', file);
            formData.append('lang', languageSelect.value);
            formData.append('summarize', 'true');

            fetch('speech.php?action=transcribe_mic', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                showLoading(false);
                if (data.ok) {
                    txtTranscript.value = data.data.transcript || '';
                    txtSummary.value = data.data.summary || '';
                    detectedLanguage = data.data.language || 'unknown';
                    lblLang.textContent = `Language: ${detectedLanguage}`;
                    lastAudioPath = data.data.saved.session_json || '';
                    updateWordCount();
                    updateStatus('Mic transcription complete.');
                } else {
                    updateStatus(`Error: ${data.error}`);
                    alertUser('error', 'Transcription Failed', data.error);
                }
            })
            .catch(err => {
                showLoading(false);
                updateStatus(`Error connecting to transcription API: ${err.message}`);
                console.error(err);
            });
        }

        // ── Text Summarization ──
        function generateSummary() {
            const text = txtTranscript.value.trim();
            if (!text) {
                alertUser('warning', 'No Transcript', 'Please transcribe some audio or enter text first.');
                return;
            }

            updateStatus('Generating summary...');
            showLoading(true);

            const formData = new FormData();
            formData.append('text', text);

            fetch('speech.php?action=summarize', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                showLoading(false);
                if (data.ok) {
                    txtSummary.value = data.data.summary || '';
                    updateStatus('Summary generated successfully.');
                } else {
                    updateStatus(`Error: ${data.error}`);
                    alertUser('error', 'Summarization Failed', data.error);
                }
            })
            .catch(err => {
                showLoading(false);
                updateStatus(`Error calling summarizer API: ${err.message}`);
                console.error(err);
            });
        }

        // ── Save Session ──
        function saveSession() {
            const text = txtTranscript.value.trim();
            const summary = txtSummary.value.trim();
            if (!text) {
                alertUser('warning', 'No Transcript', 'No transcript to save.');
                return;
            }

            updateStatus('Saving session...');
            showLoading(true);

            const formData = new FormData();
            formData.append('text', text);
            formData.append('summary', summary);
            formData.append('audio_file', lastAudioPath || 'live_recording');
            formData.append('lang', detectedLanguage);

            fetch('speech.php?action=save_session', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                showLoading(false);
                if (data.ok) {
                    updateStatus('Session saved successfully.');
                    let html = '<p style="margin-bottom: 12px; font-weight: 500;">Session saved successfully!</p><ul style="text-align: left; font-size: 13px; list-style-type: none; padding-left: 0; margin-top: 10px;">';
                    for (const key in data.data.paths) {
                        html += `<li style="margin-bottom: 6px; font-family: monospace; font-size: 11px; word-break: break-all;">📄 ${data.data.paths[key]}</li>`;
                    }
                    html += '</ul>';
                    alertUser('success', 'Session Saved', '', html);
                } else {
                    updateStatus(`Error: ${data.error}`);
                    alertUser('error', 'Save Failed', data.error);
                }
            })
            .catch(err => {
                showLoading(false);
                updateStatus(`Error saving session: ${err.message}`);
                console.error(err);
            });
        }

        // ── Performance Evaluation ──
        function runEvaluation() {
            const refTranscript = txtRefTranscript.value.trim();
            const hypTranscript = txtTranscript.value.trim();
            const refSummary = txtRefSummary.value.trim();
            const genSummary = txtSummary.value.trim();

            if (!refTranscript || !hypTranscript) {
                alertUser('warning', 'Missing Inputs', 'Reference transcript and active hypothesis transcript are required.');
                return;
            }

            updateStatus('Running evaluation metrics...');
            preEvalResults.textContent = 'Computing WER, CER, and ROUGE...';

            const formData = new FormData();
            formData.append('ref_transcript', refTranscript);
            formData.append('hyp_transcript', hypTranscript);
            if (refSummary && genSummary) {
                formData.append('ref_summary', refSummary);
                formData.append('gen_summary', genSummary);
            }

            fetch('speech.php?action=evaluate', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.ok) {
                    const results = data.data;
                    let outputText = '========================================\n';
                    outputText += '           EVALUATION RESULTS           \n';
                    outputText += '========================================\n\n';
                    
                    outputText += `Word Error Rate (WER)      : ${(results.transcription.wer * 100).toFixed(2)}%\n`;
                    outputText += `Character Error Rate (CER) : ${(results.transcription.cer * 100).toFixed(2)}%\n\n`;
                    
                    if (results.summarization) {
                        outputText += 'ROUGE Overlay Metrics:\n';
                        outputText += `  ROUGE-1 F1-Score : ${(results.summarization['rouge-1'] * 100).toFixed(2)}%\n`;
                        outputText += `  ROUGE-2 F1-Score : ${(results.summarization['rouge-2'] * 100).toFixed(2)}%\n`;
                        outputText += `  ROUGE-L F1-Score : ${(results.summarization['rouge-l'] * 100).toFixed(2)}%\n`;
                        
                        // Update the ROUGE text in main pane footer
                        lblRouge.textContent = `ROUGE: R1=${results.summarization['rouge-1'].toFixed(3)} | RL=${results.summarization['rouge-l'].toFixed(3)}`;
                    } else {
                        outputText += 'No reference summary evaluation computed.\n';
                    }
                    
                    preEvalResults.textContent = outputText;
                    updateStatus('Evaluation completed successfully.');
                } else {
                    preEvalResults.textContent = `Error: ${data.error}`;
                    updateStatus(`Evaluation Error: ${data.error}`);
                    alertUser('error', 'Evaluation Failed', data.error);
                }
            })
            .catch(err => {
                preEvalResults.textContent = `Error: ${err.message}`;
                updateStatus(`Error running evaluation: ${err.message}`);
                console.error(err);
            });
        }

        // ── Session History Operations ──
        function refreshSessionsList() {
            updateStatus('Loading saved sessions...');
            tblSessionsBody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-secondary);">Scanning transcripts directory...</td></tr>';
            selectedSessionIndex = -1;

            fetch('speech.php?action=list_sessions', {
                method: 'POST'
            })
            .then(res => res.json())
            .then(data => {
                if (data.ok) {
                    sessionsList = data.data.sessions || [];
                    renderSessionsTable();
                    updateStatus('Sessions refreshed.');
                } else {
                    tblSessionsBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--accent-danger);">Error: ${data.error}</td></tr>`;
                    updateStatus(`Error: ${data.error}`);
                }
            })
            .catch(err => {
                tblSessionsBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--accent-danger);">Connection error.</td></tr>`;
                updateStatus(`Connection Error: ${err.message}`);
                console.error(err);
            });
        }

        function renderSessionsTable() {
            if (sessionsList.length === 0) {
                tblSessionsBody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-secondary);">No saved sessions found.</td></tr>';
                return;
            }

            let html = '';
            sessionsList.forEach((session, idx) => {
                const date = new Date(session.created_at).toLocaleString();
                const source = session.source.replace(/\\/g, '/').split('/').pop();
                html += `<tr data-index="${idx}" onclick="selectSessionRow(${idx})">
                    <td style="font-family: var(--font-mono);">${session.session_id}</td>
                    <td>${date}</td>
                    <td title="${session.source}">${source}</td>
                    <td>${session.language}</td>
                </tr>`;
            });
            tblSessionsBody.innerHTML = html;
        }

        window.selectSessionRow = function(index) {
            selectedSessionIndex = index;
            const rows = tblSessionsBody.querySelectorAll('tr');
            rows.forEach((r, idx) => {
                if (idx === index) {
                    r.classList.add('selected');
                } else {
                    r.classList.remove('selected');
                }
            });
        };

        function loadSelectedSession() {
            if (selectedSessionIndex < 0) {
                alertUser('warning', 'Selection Required', 'Please select a session from the table first.');
                return;
            }

            const session = sessionsList[selectedSessionIndex];
            updateStatus(`Loading session: ${session.session_id}...`);
            showLoading(true);

            const formData = new FormData();
            formData.append('session_id', session.session_id);

            fetch('speech.php?action=load_session', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                showLoading(false);
                if (data.ok) {
                    // Load back to main panels and switch active tab
                    txtTranscript.value = data.data.session.transcript || '';
                    txtSummary.value = data.data.session.summary || '';
                    detectedLanguage = data.data.session.language || 'unknown';
                    lblLang.textContent = `Language: ${detectedLanguage}`;
                    lastAudioPath = data.data.session.audio_source || '';
                    updateWordCount();
                    lblRouge.textContent = 'ROUGE: —';
                    
                    // Switch to main tab
                    tabLinks[0].click();
                    updateStatus(`Session loaded.`);
                } else {
                    updateStatus(`Error: ${data.error}`);
                    alertUser('error', 'Load Failed', data.error);
                }
            })
            .catch(err => {
                showLoading(false);
                updateStatus(`Connection Error: ${err.message}`);
                console.error(err);
            });
        }

        function deleteSelectedSession() {
            if (selectedSessionIndex < 0) {
                alertUser('warning', 'Selection Required', 'Please select a session from the table first.');
                return;
            }

            const session = sessionsList[selectedSessionIndex];
            const isLight = document.body.classList.contains('light-theme');
            
            Swal.fire({
                title: 'Are you sure?',
                text: `You are about to permanently delete session ${session.session_id}. This action cannot be undone!`,
                icon: 'warning',
                showCancelButton: true,
                background: isLight ? '#FFFFFF' : '#1C2128',
                color: isLight ? '#1F2328' : '#E6EDF3',
                confirmButtonColor: isLight ? '#CF222E' : '#DA3633',
                cancelButtonColor: isLight ? '#656D76' : '#8B949E',
                confirmButtonText: 'Yes, delete it!'
            }).then((result) => {
                if (result.isConfirmed) {
                    performSessionDeletion(session.session_id);
                }
            });
        }

        function performSessionDeletion(sessionId) {
            updateStatus(`Deleting session: ${sessionId}...`);

            const formData = new FormData();
            formData.append('session_id', sessionId);

            fetch('speech.php?action=delete_session', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.ok) {
                    updateStatus(`Session deleted successfully.`);
                    alertUser('success', 'Deleted!', 'The session has been deleted.');
                    refreshSessionsList();
                } else {
                    updateStatus(`Error: ${data.error}`);
                    alertUser('error', 'Delete Failed', data.error);
                }
            })
            .catch(err => {
                updateStatus(`Connection Error: ${err.message}`);
                console.error(err);
            });
        }

        function exportCSV() {
            if (sessionsList.length === 0) {
                alertUser('warning', 'No Sessions', 'No sessions available to export.');
                return;
            }

            let csvContent = 'data:text/csv;charset=utf-8,';
            csvContent += 'Session ID,Created At,Audio Source,Language,JSON Path\n';

            sessionsList.forEach(session => {
                const date = new Date(session.created_at).toLocaleString();
                const source = session.source.replace(/\\/g, '\\\\');
                const file = session.file.replace(/\\/g, '\\\\');
                csvContent += `"${session.session_id}","${date}","${source}","${session.language}","${file}"\n`;
            });

            const encodedUri = encodeURI(csvContent);
            const link = document.createElement('a');
            link.setAttribute('href', encodedUri);
            link.setAttribute('download', `sessions_export_${new Date().toISOString().slice(0,10)}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            updateStatus('CSV export triggered.');
        }
    </script>
</body>
</html>
