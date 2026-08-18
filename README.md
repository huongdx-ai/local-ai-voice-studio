# Local AI Voice Studio

A professional-grade, **fully local** AI-powered Text-to-Speech and Voice Cloning studio powered by **OmniVoice** (k2-fsa), supporting **600+ languages** including **English**, **Vietnamese**, and **Japanese**.

All processing runs entirely on your machine — no voice data is uploaded to external servers.

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Engine](https://img.shields.io/badge/engine-OmniVoice-blueviolet)
![Platform](https://img.shields.io/badge/platform-Windows-0078D6)
![License](https://img.shields.io/badge/license-Apache%202.0-blue)

---

## Features

- 🎙 **Massively Multilingual TTS** — Native support for 600+ languages (English, Vietnamese, Japanese, Chinese, Korean, French, German, Spanish, etc.)
- 🔊 **Zero-Shot Voice Cloning** — Clone any speaker's voice using a 3-10 second reference audio clip
- 🖥 **Hardware Auto-Detection** — Automatic CPU, RAM, GPU, VRAM, and CUDA detection with robust fallbacks
- ⚡ **Ultra-Fast Generation** — Real-Time Factor (RTF) down to ~0.025 (up to 40x faster than real-time)
- 🔒 **100% Local & Private** — All processing on your machine; zero cloud uploads or telemetry
- 📊 **Real-time SSE Progress** — Live generation stage and progress updates in the UI
- 🎵 **Audio Player & Post-Processing** — Built-in player with speed, pitch, and volume adjustments
- 📂 **Generation History** — Track, manage, and replay past voice generations
- 💾 **Model Lifecycle Management** — Easy one-click download, verify, and cache

---

## System Requirements

### Minimum (CPU Mode)
- **OS**: Windows 10/11 (64-bit)
- **CPU**: 4+ cores
- **RAM**: 8 GB
- **Disk**: 10 GB free space
- **Python**: 3.10+
- **Node.js**: 18+

### Recommended (GPU Mode)
- **GPU**: NVIDIA GTX 1660 / RTX 2060 / RTX 3060 or better
- **VRAM**: 4+ GB (6+ GB recommended)
- **RAM**: 16 GB
- **CUDA**: 12.1+

---

## Installation

### Quick Start (Windows)

```bash
# 1. Clone or open the repository
cd local-ai-voice-studio

# 2. Run the installer (auto-detects GPU and installs PyTorch CUDA / CPU + OmniVoice)
scripts\install.bat

# 3. Start the application
scripts\run.bat
```

### Manual Installation

```bash
# Create and activate Python virtual environment
python -m venv venv
venv\Scripts\activate

# Install PyTorch (CUDA 12.1 recommended for NVIDIA GPUs)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install backend dependencies & OmniVoice
pip install -r backend\requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Checking Hardware & GPU

```bash
scripts\check_gpu.bat
```

---

## Usage

### Starting the Application

```bash
scripts\run.bat
```

This opens:
- **Web App**: http://localhost:5173
- **Backend API**: http://127.0.0.1:8000
- **Interactive API Docs**: http://127.0.0.1:8000/docs

### 1. Text to Voice
1. Go to **Text to Voice** page.
2. Select target language (English 🇺🇸 / Vietnamese 🇻🇳 / Japanese 🇯🇵).
3. Type or paste your text.
4. (Optional) Choose a cloned voice profile.
5. Click **Generate Voice** and listen or download in WAV/MP3.

### 2. Voice Cloning
1. Go to **My Voices** page.
2. Click **Upload Voice**.
3. Upload a 3-10 second clean audio clip (`.wav`, `.mp3`, `.m4a`, `.flac`).
4. Review quality score and analysis.
5. Use this voice in **Text to Voice** for zero-shot synthesis.

---

## Architecture

```
Browser (React + TypeScript + Vite)
    ↓ REST API + SSE
FastAPI Backend (Python)
    ├── Hardware Detector (CPU, RAM, GPU, VRAM via PyTorch & nvidia-smi)
    ├── Model Manager (Lifecycle, cache, and download)
    ├── TTS Service (OmniVoice Provider Adapter)
    │   └── OmniVoiceProvider (k2-fsa/OmniVoice)
    ├── Voice Clone Service (Audio validation & reference profile CRUD)
    ├── Audio Service (librosa post-processing + MP3 conversion)
    └── Job Manager (Asyncio queue + Server-Sent Events)
```

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/system` | GET | System hardware info & recommendations |
| `/api/models` | GET | List registered models & installation status |
| `/api/models/{id}/download` | POST | Download / initialize model with SSE progress |
| `/api/models/{id}` | DELETE | Delete cached model |
| `/api/voices` | GET | List uploaded voice profiles |
| `/api/voices` | POST | Upload and validate voice sample |
| `/api/voices/{id}` | DELETE | Delete voice profile |
| `/api/tts` | POST | Start background TTS job |
| `/api/tts/{job_id}/progress` | GET | SSE stream for real-time progress |
| `/api/history` | GET | View generation history |
| `/api/audio/{id}` | GET | Stream audio output (WAV / MP3) |
| `/api/audio/{id}/download` | GET | Download audio file |

---

## Project Structure

```
local-ai-voice-studio/
├── backend/
│   ├── app.py                    # FastAPI application setup & middleware
│   ├── requirements.txt          # Python dependencies
│   ├── config/                   # Configuration loader
│   ├── api/                      # REST API routes
│   │   ├── system_routes.py
│   │   ├── model_routes.py
│   │   ├── voice_routes.py
│   │   ├── tts_routes.py
│   │   ├── history_routes.py
│   │   └── audio_routes.py
│   ├── services/                 # Core backend logic
│   │   ├── hardware_detector.py  # GPU/CPU/RAM detection
│   │   ├── model_registry.py     # OmniVoice registry
│   │   ├── model_selector.py     # Hardware compatibility matching
│   │   ├── model_manager.py      # Download & caching
│   │   ├── tts_provider.py       # Abstract provider interface
│   │   ├── tts_service.py        # Central TTS service
│   │   ├── voice_clone_service.py# Voice profile management
│   │   ├── audio_validator.py    # Audio quality checks
│   │   ├── audio_service.py      # Post-processing & format export
│   │   ├── job_manager.py        # SSE job tracking
│   │   └── providers/
│   │       └── omnivoice_provider.py # OmniVoice implementation
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/           # Sidebar, AudioPlayer, ProgressBar
│       ├── pages/                # Dashboard, TextToVoice, MyVoices, Models, History, Settings
│       ├── services/             # API client & SSE logic
│       └── types/                # TypeScript interfaces
├── scripts/
│   ├── install.bat               # Windows installer
│   ├── run.bat                   # Startup script
│   ├── check_gpu.bat             # Hardware inspector
│   └── download_models.bat       # Model downloader
├── samples/                      # Sample texts (EN, VI, JA)
├── config.yaml                   # Configuration file
└── README.md
```

---

## License

- **Local AI Voice Studio**: MIT License
- **OmniVoice**: Apache 2.0 License (developed by k2-fsa / Xiaomi Next-gen Kaldi team)
