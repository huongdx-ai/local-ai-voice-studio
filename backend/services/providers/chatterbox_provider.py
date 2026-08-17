"""
Chatterbox TTS Provider for Local AI Voice Studio.
Primary engine supporting EN/VI/JA with zero-shot voice cloning.
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


class ChatterboxProvider(TTSProvider):
    """
    TTS Provider using Chatterbox Multilingual V3.
    Supports 23+ languages, zero-shot voice cloning, GPU/CPU.
    """

    def __init__(self):
        self._model = None
        self._device: str = "cpu"
        self._loaded: bool = False

    def get_name(self) -> str:
        return "Chatterbox Multilingual V3"

    def get_engine_id(self) -> str:
        return "chatterbox"

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            languages=[
                "en", "vi", "ja", "zh", "ko", "fr", "de", "es", "it",
                "pt", "ru", "ar", "hi", "pl", "tr", "nl", "cs", "da",
                "fi", "el", "he", "no", "sv", "sw",
            ],
            voice_cloning=True,
            speed_control=True,
            pitch_control=False,  # handled via audio post-processing
            streaming=False,
            max_text_length=5000,
            supported_sample_rates=[22050, 24000, 44100],
        )

    async def initialize(self, device: str = "cpu") -> None:
        """Load the Chatterbox model."""
        if self._loaded:
            return

        self._device = device
        logger.info(f"Loading Chatterbox model on {device}...")

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model)
            self._loaded = True
            logger.info("Chatterbox model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Chatterbox model: {e}")
            raise RuntimeError(f"Failed to load Chatterbox: {e}")

    def _load_model(self) -> None:
        """Blocking model load — runs in executor."""
        try:
            import torch
            from chatterbox.tts import ChatterboxTTS

            self._model = ChatterboxTTS.from_pretrained(
                device=self._device
            )
        except ImportError as e:
            raise RuntimeError(
                "chatterbox-tts package not installed. "
                "Run: pip install chatterbox-tts"
            ) from e

    async def generate(self, request: TTSRequest) -> TTSResult:
        """Generate speech using Chatterbox."""
        if not self._loaded or self._model is None:
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
            error_msg = str(e)
            if "CUDA out of memory" in error_msg:
                error_msg = (
                    "CUDA Out Of Memory. The selected model requires more VRAM. "
                    "Try using a smaller model or switch to CPU mode."
                )
            logger.error(f"Chatterbox generation failed: {error_msg}")
            return TTSResult(
                audio_path=Path(""),
                success=False,
                error=error_msg,
                model_used=self.get_name(),
                language=request.language,
            )

    def _generate_sync(self, request: TTSRequest) -> TTSResult:
        """Blocking generation — runs in executor."""
        import torch
        import torchaudio

        # Determine output path
        output_path = Path(tempfile.mktemp(suffix=".wav"))

        # Build generation kwargs
        gen_kwargs = {}

        # Voice cloning: use reference audio
        if request.voice_profile_path and request.voice_profile_path.exists():
            audio_prompt, sr = torchaudio.load(str(request.voice_profile_path))
            gen_kwargs["audio_prompt"] = audio_prompt
        
        # Generate
        wav = self._model.generate(
            text=request.text,
            **gen_kwargs,
        )

        # Handle speed via post-processing if needed (basic approach)
        # Chatterbox may support speed natively via exaggeration param

        # Save output
        if isinstance(wav, torch.Tensor):
            if wav.dim() == 1:
                wav = wav.unsqueeze(0)
            sample_rate = 24000  # Chatterbox default
            torchaudio.save(str(output_path), wav.cpu(), sample_rate)
            duration = wav.shape[-1] / sample_rate
        else:
            # If it returns something else, try to handle
            sample_rate = 24000
            duration = 0.0
            torchaudio.save(str(output_path), wav.cpu(), sample_rate)

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
        """Unload model from memory."""
        if self._model is not None:
            del self._model
            self._model = None
            self._loaded = False

            # Free GPU memory
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass

            logger.info("Chatterbox model unloaded")
