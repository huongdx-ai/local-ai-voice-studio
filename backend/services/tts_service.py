"""
TTS Service for Local AI Voice Studio.
Orchestrates OmniVoice model loading and speech generation.
Uses OmniVoice as the single, unified TTS engine for all languages.
"""

import asyncio
import logging
from typing import Optional
from pathlib import Path

from backend.services.tts_provider import TTSProvider, TTSRequest, TTSResult
from backend.services.providers.omnivoice_provider import OmniVoiceProvider
from backend.services.hardware_detector import get_hardware_detector

logger = logging.getLogger(__name__)


class TTSService:
    """
    Central TTS service using OmniVoice for all languages.
    OmniVoice supports 600+ languages, voice cloning, and voice design.
    """

    def __init__(self):
        self._provider: OmniVoiceProvider = OmniVoiceProvider()
        self._device: str = "cpu"

    def get_provider(self, engine_id: str = None) -> Optional[TTSProvider]:
        """Get the OmniVoice provider (only engine available)."""
        return self._provider

    def get_all_providers(self) -> dict[str, TTSProvider]:
        """Get all registered providers."""
        return {"omnivoice": self._provider}

    def get_best_provider(
        self, language: str, require_cloning: bool = False
    ) -> Optional[TTSProvider]:
        """
        Return the OmniVoice provider.
        OmniVoice supports all languages and cloning natively.
        """
        return self._provider

    async def generate(
        self,
        request: TTSRequest,
        engine_id: Optional[str] = None,
    ) -> TTSResult:
        """
        Generate speech from text using OmniVoice.
        
        Args:
            request: The TTS request parameters
            engine_id: Ignored (OmniVoice is the only engine)
        """
        provider = self._provider

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
            f"Generating speech: engine=OmniVoice, "
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
        """Unload OmniVoice to free memory."""
        if self._provider.is_loaded():
            await self._provider.unload()
        logger.info("TTS service unloaded")


# Module-level singleton
_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    """Get the global TTSService singleton."""
    global _service
    if _service is None:
        _service = TTSService()
    return _service
