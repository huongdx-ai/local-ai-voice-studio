"""
Kokoro TTS Provider for Local AI Voice Studio.
Lightweight CPU-friendly engine for English and Japanese.
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Optional

from backend.services.tts_provider import (
    TTSProvider,
    TTSRequest,
    TTSResult,
    ProviderCapabilities,
)

logger = logging.getLogger(__name__)


class KokoroProvider(TTSProvider):
    """
    TTS Provider using Kokoro v1.
    Ultra-lightweight 82M parameters, extremely fast on CPU.
    Supports English and Japanese.
    """

    def __init__(self):
        self._pipeline = None
        self._device: str = "cpu"
        self._loaded: bool = False
        self._current_lang: Optional[str] = None

    def get_name(self) -> str:
        return "Kokoro v1"

    def get_engine_id(self) -> str:
        return "kokoro"

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            languages=["en", "ja"],
            voice_cloning=False,
            speed_control=True,
            pitch_control=False,
            streaming=False,
            max_text_length=5000,
            supported_sample_rates=[24000],
        )

    async def initialize(self, device: str = "cpu") -> None:
        """Load the Kokoro model."""
        if self._loaded:
            return

        self._device = device
        logger.info(f"Loading Kokoro model on {device}...")

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model)
            self._loaded = True
            logger.info("Kokoro model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Kokoro model: {e}")
            raise RuntimeError(f"Failed to load Kokoro: {e}")

    def _load_model(self) -> None:
        """Blocking model load."""
        try:
            from kokoro import KPipeline

            # Default to English; will switch per-request
            self._pipeline = KPipeline(lang_code="a")  # "a" = American English
            self._current_lang = "en"
        except ImportError as e:
            raise RuntimeError(
                "kokoro package not installed. "
                "Run: pip install kokoro soundfile misaki[ja]"
            ) from e

    def _ensure_lang(self, language: str) -> None:
        """Switch pipeline language if needed."""
        from kokoro import KPipeline

        lang_map = {
            "en": "a",   # American English
            "ja": "j",   # Japanese
        }
        code = lang_map.get(language, "a")

        if self._current_lang != language:
            self._pipeline = KPipeline(lang_code=code)
            self._current_lang = language
            logger.debug(f"Kokoro switched to language: {language}")

    async def generate(self, request: TTSRequest) -> TTSResult:
        """Generate speech using Kokoro."""
        if not self._loaded or self._pipeline is None:
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
            logger.error(f"Kokoro generation failed: {e}")
            return TTSResult(
                audio_path=Path(""),
                success=False,
                error=str(e),
                model_used=self.get_name(),
                language=request.language,
            )

    def _generate_sync(self, request: TTSRequest) -> TTSResult:
        """Blocking generation."""
        import soundfile as sf
        import numpy as np

        self._ensure_lang(request.language)

        output_path = Path(tempfile.mktemp(suffix=".wav"))

        # Kokoro generates via pipeline
        # The pipeline yields (graphemes, phonemes, audio) tuples
        all_audio = []
        sample_rate = 24000

        for _, _, audio in self._pipeline(
            request.text,
            speed=request.speed,
        ):
            if audio is not None:
                if hasattr(audio, "numpy"):
                    all_audio.append(audio.numpy())
                else:
                    all_audio.append(np.array(audio))

        if not all_audio:
            return TTSResult(
                audio_path=Path(""),
                success=False,
                error="No audio generated",
                model_used=self.get_name(),
                language=request.language,
            )

        # Concatenate all audio chunks
        full_audio = np.concatenate(all_audio)
        duration = len(full_audio) / sample_rate

        # Save
        sf.write(str(output_path), full_audio, sample_rate)

        return TTSResult(
            audio_path=output_path,
            duration_seconds=round(duration, 2),
            sample_rate=sample_rate,
            model_used=self.get_name(),
            language=request.language,
            success=True,
        )

    def is_loaded(self) -> bool:
        return self._loaded

    async def unload(self) -> None:
        """Unload model."""
        if self._pipeline is not None:
            del self._pipeline
            self._pipeline = None
            self._loaded = False
            self._current_lang = None
            logger.info("Kokoro model unloaded")
