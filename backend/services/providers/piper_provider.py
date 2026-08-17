"""
Piper TTS Provider for Local AI Voice Studio.
Ultra-lightweight CPU engine for Vietnamese fallback.
"""

import asyncio
import logging
import tempfile
import wave
from pathlib import Path
from typing import Optional

from backend.services.tts_provider import (
    TTSProvider,
    TTSRequest,
    TTSResult,
    ProviderCapabilities,
)

logger = logging.getLogger(__name__)


class PiperProvider(TTSProvider):
    """
    TTS Provider using Piper TTS.
    Ultra-lightweight, CPU-optimized, ideal for Vietnamese.
    """

    def __init__(self):
        self._voice = None
        self._device: str = "cpu"
        self._loaded: bool = False

    def get_name(self) -> str:
        return "Piper Vietnamese"

    def get_engine_id(self) -> str:
        return "piper"

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            languages=["vi"],
            voice_cloning=False,
            speed_control=True,
            pitch_control=False,
            streaming=False,
            max_text_length=5000,
            supported_sample_rates=[22050],
        )

    async def initialize(self, device: str = "cpu") -> None:
        """Load Piper voice."""
        if self._loaded:
            return

        self._device = "cpu"  # Piper is CPU-only
        logger.info("Loading Piper TTS model...")

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model)
            self._loaded = True
            logger.info("Piper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Piper model: {e}")
            raise RuntimeError(f"Failed to load Piper: {e}")

    def _load_model(self) -> None:
        """Blocking model load."""
        try:
            from piper import PiperVoice

            # Piper downloads voice on first use
            # We'll use the Vietnamese voice
            # The voice model is auto-downloaded when referenced
            self._piper_available = True
        except ImportError as e:
            raise RuntimeError(
                "piper-tts package not installed. "
                "Run: pip install piper-tts"
            ) from e

    async def generate(self, request: TTSRequest) -> TTSResult:
        """Generate speech using Piper."""
        if not self._loaded:
            return TTSResult(
                audio_path=Path(""),
                success=False,
                error="Model not loaded. Call initialize() first.",
            )

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._generate_sync, request
            )
            return result
        except Exception as e:
            logger.error(f"Piper generation failed: {e}")
            return TTSResult(
                audio_path=Path(""),
                success=False,
                error=str(e),
                model_used=self.get_name(),
                language=request.language,
            )

    def _generate_sync(self, request: TTSRequest) -> TTSResult:
        """Blocking generation."""
        import subprocess
        import json

        output_path = Path(tempfile.mktemp(suffix=".wav"))

        try:
            # Use piper CLI for generation
            cmd = [
                "piper",
                "--model", "vi_VN-vivos-x_low",
                "--output_file", str(output_path),
            ]

            if request.speed != 1.0:
                cmd.extend(["--length-scale", str(1.0 / request.speed)])

            proc = subprocess.run(
                cmd,
                input=request.text,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if proc.returncode != 0:
                # Fallback: try Python API
                return self._generate_with_python_api(request, output_path)

            # Get duration from wav file
            duration = 0.0
            sample_rate = 22050
            if output_path.exists():
                with wave.open(str(output_path), "r") as wf:
                    frames = wf.getnframes()
                    sample_rate = wf.getframerate()
                    duration = frames / sample_rate

            return TTSResult(
                audio_path=output_path,
                duration_seconds=round(duration, 2),
                sample_rate=sample_rate,
                model_used=self.get_name(),
                language=request.language,
                success=True,
            )

        except subprocess.TimeoutExpired:
            return TTSResult(
                audio_path=Path(""),
                success=False,
                error="Piper generation timed out",
                model_used=self.get_name(),
                language=request.language,
            )
        except FileNotFoundError:
            return self._generate_with_python_api(request, output_path)

    def _generate_with_python_api(
        self, request: TTSRequest, output_path: Path
    ) -> TTSResult:
        """Fallback: generate using Piper Python API."""
        try:
            from piper import PiperVoice
            import wave as wave_mod
            import numpy as np

            # PiperVoice needs model path; attempt auto-download
            voice = PiperVoice.load("vi_VN-vivos-x_low")

            with wave_mod.open(str(output_path), "wb") as wf:
                voice.synthesize(request.text, wf)

            # Read back for duration
            with wave_mod.open(str(output_path), "r") as wf:
                frames = wf.getnframes()
                sr = wf.getframerate()
                duration = frames / sr

            return TTSResult(
                audio_path=output_path,
                duration_seconds=round(duration, 2),
                sample_rate=sr,
                model_used=self.get_name(),
                language=request.language,
                success=True,
            )
        except Exception as e:
            return TTSResult(
                audio_path=Path(""),
                success=False,
                error=f"Piper Python API failed: {e}",
                model_used=self.get_name(),
                language=request.language,
            )

    def is_loaded(self) -> bool:
        return self._loaded

    async def unload(self) -> None:
        """Unload model."""
        self._voice = None
        self._loaded = False
        logger.info("Piper model unloaded")
