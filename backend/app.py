"""
Local AI Voice Studio — FastAPI Application
Main entry point for the backend server.
"""

import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure backend is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import get_config, get_project_root
from backend.api.system_routes import router as system_router
from backend.api.model_routes import router as model_router
from backend.api.voice_routes import router as voice_router
from backend.api.tts_routes import router as tts_router
from backend.api.history_routes import router as history_router
from backend.api.audio_routes import router as audio_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    config = get_config()
    project_root = get_project_root()

    logger.info("=" * 60)
    logger.info("  Local AI Voice Studio — Starting")
    logger.info("=" * 60)

    # Create required directories
    for dir_name in ["models", "voices", "outputs", "data"]:
        dir_path = project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)

    # Detect hardware on startup
    from backend.services.hardware_detector import get_hardware_detector
    detector = get_hardware_detector(force_device=config.hardware.force_device)
    profile = detector.detect()

    logger.info(f"  OS:     {profile.os_name}")
    logger.info(f"  CPU:    {profile.cpu.name}")
    logger.info(f"  RAM:    {profile.ram.total_gb} GB")
    logger.info(f"  GPU:    {profile.gpu.name}")
    if profile.gpu.detected:
        logger.info(f"  VRAM:   {profile.gpu.vram_total_gb} GB")
    logger.info(f"  CUDA:   {'Available' if profile.cuda.available else 'Not available'}")
    logger.info(f"  Device: {profile.recommended_device.upper()}")
    logger.info(f"  Tier:   {profile.recommended_model_tier}")
    logger.info("=" * 60)

    # Initialize model manager (scans cache)
    from backend.services.model_manager import get_model_manager
    manager = get_model_manager()
    installed = len(manager._registry.get_installed_models())
    logger.info(f"  Installed models: {installed}")

    # Initialize voice service (loads profiles)
    from backend.services.voice_clone_service import get_voice_clone_service
    voice_service = get_voice_clone_service()
    logger.info(f"  Voice profiles: {voice_service.get_voice_count()}")

    logger.info("=" * 60)
    logger.info(f"  Server: http://{config.server.host}:{config.server.port}")
    logger.info("=" * 60)

    yield  # Application runs here

    # Shutdown
    logger.info("Local AI Voice Studio — Shutting down")

    # Unload models
    from backend.services.tts_service import get_tts_service
    tts_service = get_tts_service()
    await tts_service.unload_all()


# Create FastAPI app
app = FastAPI(
    title="Local AI Voice Studio",
    description="Local AI-powered Text-to-Speech and Voice Cloning Studio",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
config = get_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(system_router)
app.include_router(model_router)
app.include_router(voice_router)
app.include_router(tts_router)
app.include_router(history_router)
app.include_router(audio_router)


@app.get("/")
async def root():
    return {
        "name": "Local AI Voice Studio",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app:app",
        host=config.server.host,
        port=config.server.port,
        reload=True,
    )
