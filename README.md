# Local AI Voice Studio

A professional-grade, **fully local** AI-powered Text-to-Speech and Voice Cloning studio supporting **English**, **Vietnamese**, and **Japanese**.

All processing runs entirely on your machine — no data is uploaded to external servers.

![Status](https://img.shields.io/badge/status-active-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Platform](https://img.shields.io/badge/platform-Windows-0078D6)

---

## Features

- 🎙 **Text-to-Speech** — Generate natural speech from text in 3 languages
- 🔊 **Voice Cloning** — Clone any voice with a 5-10 second audio sample
- 🖥 **Hardware Auto-Detection** — CPU, GPU, VRAM, CUDA automatic detection
- 🤖 **Smart Model Selection** — Auto-selects the best model for your hardware
- 🇺🇸🇻🇳🇯🇵 **Multilingual** — English, Vietnamese, Japanese
- 🔒 **100% Local** — All processing on your machine, no cloud uploads
- 📊 **Real-time Progress** — Live SSE-based generation progress
- 🎵 **Audio Player** — Built-in player with speed control and download
- 📂 **Generation History** — Track and replay past generations
- 💾 **Model Management** — Download, cache, and manage AI models

---

## System Requirements

### Minimum
- **OS**: Windows 10/11 (64-bit)
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disk**: 10 GB free space
- **Python**: 3.10+
- **Node.js**: 18+

### Recommended (GPU Mode)
- **RAM**: 16+ GB
- **GPU**: NVIDIA GTX 1660 or better
- **VRAM**: 6+ GB
- **CUDA**: 12.1+

### Optimal
- **GPU**: NVIDIA RTX 3060 12GB or better
- **VRAM**: 8+ GB
- **RAM**: 32 GB

---

## Installation

### Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>
cd local-ai-voice-studio

# 2. Run the installer
scripts\install.bat

# 3. Start the application
scripts\run.bat
```

### Manual Installation

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install backend dependencies
pip install -r backend\requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### CUDA Installation (GPU Mode)

1. Install [NVIDIA GPU drivers](https://www.nvidia.com/drivers)
2. Install [CUDA Toolkit 12.1+](https://developer.nvidia.com/cuda-downloads)
3. Install PyTorch with CUDA:
   ```bash
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```
4. Verify:
   ```bash
   scripts\check_gpu.bat
   ```

### CPU Mode

If you don't have an NVIDIA GPU, the application automatically falls back to CPU mode.
CPU mode uses lightweight models (Kokoro for EN/JA, Piper for VI) for faster inference.

---

## Usage

### Starting the Application

```bash
scripts\run.bat
```

This starts:
- **Backend**: http://127.0.0.1:8000
- **Frontend**: http://localhost:5173
- **API Docs**: http://127.0.0.1:8000/docs

### Text to Speech

1. Navigate to **Text to Voice** page
2. Select language (English / Vietnamese / Japanese)
3. Enter text
4. Click **Generate Voice**
5. Listen, adjust speed, download WAV/MP3

### Voice Cloning

1. Navigate to **My Voices** page
2. Click **Upload Voice**
3. Upload a 5-10 second clean audio sample (.wav, .mp3, .m4a, .flac)
4. Review the audio quality analysis
5. Go to **Text to Voice** and select your cloned voice

### Model Management

1. Navigate to **Models** page
2. Download models you need
3. Models are cached locally in `models/` directory
4. The system auto-selects the best model for your hardware

---

## Architecture

```
Browser (React + TypeScript)
    ↓ REST API + SSE
FastAPI Backend (Python)
    ├── Hardware Detector
    ├── Model Manager (Registry → Selector → Cache)
    ├── TTS Service (Provider Adapter Pattern)
    │   ├── ChatterboxProvider (EN/VI/JA + Cloning)
    │   ├── KokoroProvider (EN/JA, CPU-fast)
    │   └── PiperProvider (VI, CPU-fast)
    ├── Voice Clone Service
    ├── Audio Service (Post-processing + Format conversion)
    └── Job Manager (Background tasks + SSE progress)
```

### TTS Models

| Model | Languages | Cloning | License | Size | Best For |
|-------|-----------|---------|---------|------|----------|
| **Chatterbox V3** | EN/VI/JA (23+) | ✓ Zero-shot | MIT | ~2GB | GPU, high quality |
| **Kokoro v1** | EN/JA | ✗ | Apache 2.0 | ~0.3GB | CPU, fast |
| **Piper** | VI | ✗ | MIT | ~0.1GB | CPU, Vietnamese |

### Model Selection Algorithm

```
GPU ≥ 6GB VRAM  → Chatterbox V3 (best quality + cloning)
GPU 4-6GB VRAM  → Chatterbox V3 FP16
GPU < 4GB VRAM  → Kokoro (EN/JA) + Piper (VI)
CPU ≥ 16GB RAM  → Chatterbox CPU (slow) or Kokoro (fast)
CPU < 16GB RAM  → Kokoro (EN/JA) + Piper (VI)
```

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/system` | GET | Hardware info & recommendations |
| `/api/models` | GET | List all models |
| `/api/models/{id}/download` | POST | Download model (SSE progress) |
| `/api/models/{id}` | DELETE | Delete model |
| `/api/voices` | GET | List voice profiles |
| `/api/voices` | POST | Upload voice sample |
| `/api/voices/{id}` | DELETE | Delete voice profile |
| `/api/tts` | POST | Start TTS generation |
| `/api/tts/{job_id}/progress` | GET | SSE progress stream |
| `/api/history` | GET | Generation history |
| `/api/audio/{id}` | GET | Stream audio |
| `/api/audio/{id}/download` | GET | Download audio |

Full interactive docs: http://127.0.0.1:8000/docs

---

## Project Structure

```
local-ai-voice-studio/
├── backend/
│   ├── app.py                    # FastAPI application
│   ├── requirements.txt          # Python dependencies
│   ├── config/                   # Configuration loader
│   ├── api/                      # REST API routes
│   │   ├── system_routes.py
│   │   ├── model_routes.py
│   │   ├── voice_routes.py
│   │   ├── tts_routes.py
│   │   ├── history_routes.py
│   │   └── audio_routes.py
│   ├── services/                 # Business logic
│   │   ├── hardware_detector.py
│   │   ├── model_registry.py
│   │   ├── model_selector.py
│   │   ├── model_manager.py
│   │   ├── tts_provider.py       # Abstract interface
│   │   ├── tts_service.py
│   │   ├── voice_clone_service.py
│   │   ├── audio_validator.py
│   │   ├── audio_service.py
│   │   ├── job_manager.py
│   │   └── providers/            # TTS engine adapters
│   │       ├── chatterbox_provider.py
│   │       ├── kokoro_provider.py
│   │       └── piper_provider.py
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/           # Reusable UI components
│       ├── pages/                # Route pages
│       ├── services/             # API client
│       └── types/                # TypeScript types
├── scripts/
│   ├── install.bat
│   ├── run.bat
│   ├── check_gpu.bat
│   └── download_models.bat
├── samples/                      # Demo text files
├── config.yaml                   # Application configuration
└── README.md
```

---

## Troubleshooting

### Backend won't start
```
pip install -r backend\requirements.txt
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

### CUDA Out Of Memory
- Use a smaller model or switch to CPU mode
- Close other GPU-intensive applications
- In `config.yaml`, set `hardware.force_device: cpu`

### Model not installed
- Navigate to Models page and click Download
- Or run `scripts\download_models.bat`

### Audio generation is slow
- Use GPU mode for 5-10x speedup
- Keep text under 500 characters
- Use Kokoro model for fastest CPU inference

### Import errors
- Ensure virtual environment is activated: `venv\Scripts\activate`
- Reinstall dependencies: `pip install -r backend\requirements.txt`

### Port already in use
- Backend: Change port in `config.yaml` (default: 8000)
- Frontend: Set `VITE_PORT` environment variable

---

## Performance Optimization

### GPU Mode
- Ensure CUDA is properly installed
- Use FP16 for supported models (automatic)
- Keep VRAM free of other applications
- Chatterbox V3 generates ~5-10s of audio per second on RTX 3060

### CPU Mode
- Use Kokoro for fastest inference (~2s per sentence)
- Close memory-intensive applications
- Increase Python thread count in config

---

## Testing

```bash
# Activate venv
venv\Scripts\activate

# Run all tests
cd local-ai-voice-studio
python -m pytest backend/tests/ -v

# Run specific test
python -m pytest backend/tests/test_hardware_detector.py -v
```

---

## Security & Privacy

- **100% Local Processing** — All TTS and voice cloning runs on your machine
- **No Cloud Uploads** — Voice samples, embeddings, and audio never leave your device
- **Safe Logging** — Only job_id, timestamp, model, language, duration, status logged
- **No Tracking** — No telemetry, analytics, or data collection

---

## License

This project is open source. Individual model licenses:
- **Chatterbox V3**: MIT
- **Kokoro v1**: Apache 2.0
- **Piper TTS**: MIT
