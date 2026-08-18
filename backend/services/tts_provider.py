"""
Abstract TTS Provider for Local AI Voice Studio.
All TTS engines implement this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class TTSRequest:
    """Request parameters for speech generation."""
    text: str
    language: str = "en"
    speed: float = 1.0
    pitch: float = 0.0                      # semitones, 0 = no change
    volume: float = 1.0                     # 0.0 - 1.0
    speaker_id: Optional[str] = None
    voice_profile_path: Optional[Path] = None       # path to reference audio (.wav)
    voice_prompt_path: Optional[Path] = None        # path to pre-extracted prompt (.pt)
    ref_text: Optional[str] = None                  # transcript of reference audio
    instruct: Optional[str] = None                  # Voice design prompt (e.g. "warm calm female voice")
    num_step: int = 32                              # Diffusion steps (16-64)
    guidance_scale: float = 2.0                     # Classifier-free guidance scale
    denoise: bool = True                            # Enable post-denoising
    duration: Optional[float] = None                # Target audio duration in seconds
    output_format: str = "wav"
    sample_rate: int = 24000


@dataclass
class TTSResult:
    """Result from speech generation."""
    audio_path: Path
    duration_seconds: float = 0.0
    sample_rate: int = 24000
    model_used: str = ""
    language: str = ""
    success: bool = True
    error: str = ""


@dataclass
class ProviderCapabilities:
    """Declares what a provider can and cannot do."""
    languages: list[str] = field(default_factory=list)
    voice_cloning: bool = True
    voice_design: bool = True
    speed_control: bool = True
    pitch_control: bool = False
    streaming: bool = False
    max_text_length: int = 5000
    supported_sample_rates: list[int] = field(
        default_factory=lambda: [24000]
    )


class TTSProvider(ABC):
    """
    Abstract base class for TTS providers.
    The OmniVoice provider implements this interface.
    """

    @abstractmethod
    def get_name(self) -> str:
        """Return the display name of this provider."""
        ...

    @abstractmethod
    def get_engine_id(self) -> str:
        """Return the engine identifier (e.g., 'omnivoice')."""
        ...

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Return the capabilities of this provider."""
        ...

    @abstractmethod
    async def initialize(self, device: str = "cpu") -> None:
        """Initialize / load the model."""
        ...

    @abstractmethod
    async def generate(self, request: TTSRequest) -> TTSResult:
        """Generate speech from text."""
        ...

    @abstractmethod
    def is_loaded(self) -> bool:
        """Check if the model is currently loaded in memory."""
        ...

    @abstractmethod
    async def unload(self) -> None:
        """Unload the model from memory to free resources."""
        ...

    def supports_language(self, language: str) -> bool:
        """Check if this provider supports a given language."""
        return language in self.get_capabilities().languages or True

    def supports_cloning(self) -> bool:
        """Check if this provider supports voice cloning."""
        return self.get_capabilities().voice_cloning
