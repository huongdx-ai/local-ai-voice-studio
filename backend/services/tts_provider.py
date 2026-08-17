"""
Abstract TTS Provider for Local AI Voice Studio.
All TTS engines must implement this interface.
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
    pitch: float = 0.0       # semitones, 0 = no change
    volume: float = 1.0      # 0.0 - 1.0
    speaker_id: Optional[str] = None
    voice_profile_path: Optional[Path] = None  # path to voice sample for cloning
    output_format: str = "wav"
    sample_rate: int = 22050


@dataclass
class TTSResult:
    """Result from speech generation."""
    audio_path: Path
    duration_seconds: float = 0.0
    sample_rate: int = 22050
    model_used: str = ""
    language: str = ""
    success: bool = True
    error: str = ""


@dataclass
class ProviderCapabilities:
    """Declares what a provider can and cannot do."""
    languages: list[str] = field(default_factory=list)
    voice_cloning: bool = False
    speed_control: bool = True
    pitch_control: bool = False  # via model; post-processing always available
    streaming: bool = False
    max_text_length: int = 5000
    supported_sample_rates: list[int] = field(
        default_factory=lambda: [22050, 44100]
    )


class TTSProvider(ABC):
    """
    Abstract base class for TTS providers.
    Each engine (Chatterbox, Kokoro, Piper) implements this interface.
    The TTS service uses this abstraction — never calls engines directly.
    """

    @abstractmethod
    def get_name(self) -> str:
        """Return the display name of this provider."""
        ...

    @abstractmethod
    def get_engine_id(self) -> str:
        """Return the engine identifier (e.g., 'chatterbox', 'kokoro')."""
        ...

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Return the capabilities of this provider."""
        ...

    @abstractmethod
    async def initialize(self, device: str = "cpu") -> None:
        """
        Initialize / load the model.
        Called once before first generation.
        device: "cpu" or "cuda"
        """
        ...

    @abstractmethod
    async def generate(self, request: TTSRequest) -> TTSResult:
        """
        Generate speech from text.
        Returns a TTSResult with the path to the generated audio.
        """
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
        return language in self.get_capabilities().languages

    def supports_cloning(self) -> bool:
        """Check if this provider supports voice cloning."""
        return self.get_capabilities().voice_cloning
