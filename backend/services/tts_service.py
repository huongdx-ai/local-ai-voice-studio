"""
TTS Service for Local AI Voice Studio.
Orchestrates provider selection, model loading, and speech generation.
"""

import asyncio
import logging
from typing import Optional
from pathlib import Path

from backend.services.tts_provider import TTSProvider, TTSRequest, TTSResult
from backend.services.providers.chatterbox_provider import ChatterboxProvider
from backend.services.providers.kokoro_provider import KokoroProvider
from backend.services.providers.piper_provider import PiperProvider
from backend.services.model_registry import ModelEngine, get_model_registry
from backend.services.hardware_detector import get_hardware_detector

logger = logging.getLogger(__name__)


class TTSService:
    """
    Central TTS service that manages providers and generates speech.
    Uses the adapter pattern — never calls engines directly.
    """

    def __init__(self):
        self._providers: dict[str, TTSProvider] = {}
        self._active_provider: Optional[TTSProvider] = None
        self._device: str = "cpu"

        # Register all providers
        self._register_providers()

    def _register_providers(self) -> None:
        """Register all available TTS providers."""
        self._providers["chatterbox"] = ChatterboxProvider()
        self._providers["kokoro"] = KokoroProvider()
        self._providers["piper"] = PiperProvider()

    def get_provider(self, engine_id: str) -> Optional[TTSProvider]:
        """Get a provider by engine ID."""
        return self._providers.get(engine_id)

    def get_all_providers(self) -> dict[str, TTSProvider]:
        """Get all registered providers."""
        return self._providers

    def get_best_provider(
        self, language: str, require_cloning: bool = False
    ) -> Optional[TTSProvider]:
        """
        Select the best provider for a language.
        Considers hardware capabilities and model availability.
        """
        detector = get_hardware_detector()
        profile = detector.get_profile()
        device = profile.recommended_device

        # Priority order for each language
        priority = {
            "en": ["chatterbox", "kokoro"],
            "vi": ["chatterbox", "piper"],
            "ja": ["chatterbox", "kokoro"],
        }

        candidates = priority.get(language, ["chatterbox"])

        for engine_id in candidates:
            provider = self._providers.get(engine_id)
            if provider is None:
                continue

            # Check language support
            if not provider.supports_language(language):
                continue

            # Check cloning requirement
            if require_cloning and not provider.supports_cloning():
                continue

            # Check hardware compatibility
            if device == "cpu":
                # For CPU, prefer lightweight models
                if engine_id in ("kokoro", "piper"):
                    return provider
                # Chatterbox can run on CPU but it's slow
                return provider
            else:
                # For GPU, prefer Chatterbox (best quality)
                return provider

        # Fallback: return any provider that supports the language
        for provider in self._providers.values():
            if provider.supports_language(language):
                if require_cloning and not provider.supports_cloning():
                    continue
                return provider

        return None

    async def generate(
        self,
        request: TTSRequest,
        engine_id: Optional[str] = None,
    ) -> TTSResult:
        """
        Generate speech from text.
        
        Args:
            request: The TTS request parameters
            engine_id: Optional specific engine to use. 
                       If None, auto-selects based on language and hardware.
        """
        # Select provider
        if engine_id:
            provider = self.get_provider(engine_id)
            if provider is None:
                return TTSResult(
                    audio_path=Path(""),
                    success=False,
                    error=f"Unknown engine: {engine_id}",
                )
        else:
            has_cloning = request.voice_profile_path is not None
            provider = self.get_best_provider(
                request.language, require_cloning=has_cloning
            )
            if provider is None:
                return TTSResult(
                    audio_path=Path(""),
                    success=False,
                    error=f"No TTS provider available for language '{request.language}'",
                )

        # Ensure provider is initialized
        if not provider.is_loaded():
            detector = get_hardware_detector()
            device = detector.get_profile().recommended_device
            try:
                await provider.initialize(device=device)
            except RuntimeError as e:
                return TTSResult(
                    audio_path=Path(""),
                    success=False,
                    error=str(e),
                )

        # Generate
        logger.info(
            f"Generating speech: engine={provider.get_engine_id()}, "
            f"lang={request.language}, text_len={len(request.text)}"
        )

        result = await provider.generate(request)

        if result.success:
            logger.info(
                f"Generation complete: duration={result.duration_seconds}s, "
                f"model={result.model_used}"
            )
        else:
            logger.error(f"Generation failed: {result.error}")

        return result

    async def unload_all(self) -> None:
        """Unload all providers to free memory."""
        for provider in self._providers.values():
            if provider.is_loaded():
                await provider.unload()
        logger.info("All TTS providers unloaded")


# Module-level singleton
_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    """Get the global TTSService singleton."""
    global _service
    if _service is None:
        _service = TTSService()
    return _service
