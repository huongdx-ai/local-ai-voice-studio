"""
Model Registry for Local AI Voice Studio.
Manages available TTS models and their metadata.
Now uses OmniVoice as the single model for all languages.
"""

import logging
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional

logger = logging.getLogger(__name__)


class ModelEngine(str, Enum):
    OMNIVOICE = "omnivoice"


class ModelStatus(str, Enum):
    NOT_INSTALLED = "not_installed"
    DOWNLOADING = "downloading"
    INSTALLED = "installed"
    ERROR = "error"


@dataclass
class ModelInfo:
    id: str
    name: str
    language: str
    engine: ModelEngine
    description: str = ""
    size_gb: float = 0.0
    min_ram_gb: float = 0.0
    recommended_ram_gb: float = 0.0
    min_vram_gb: float = 0.0
    recommended_vram_gb: float = 0.0
    cpu_supported: bool = True
    cuda_supported: bool = True
    voice_cloning: bool = True
    languages_supported: list[str] = field(default_factory=list)
    quality_score: int = 0
    speed_score: int = 0
    huggingface_id: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["engine"] = self.engine.value
        return d


class ModelRegistry:
    """Registry of available TTS models."""

    def __init__(self):
        self._models: dict[str, ModelInfo] = {}
        self._status: dict[str, ModelStatus] = {}
        self._active_model_id: Optional[str] = None
        self._register_builtin_models()

    def _register_builtin_models(self) -> None:
        """Register OmniVoice as the primary TTS model."""

        # OmniVoice — 600+ languages, voice cloning, voice design
        self._register(ModelInfo(
            id="omnivoice-multilingual",
            name="OmniVoice",
            language="multi",
            engine=ModelEngine.OMNIVOICE,
            description=(
                "High-quality multilingual TTS with zero-shot voice cloning. "
                "Supports 600+ languages including English, Vietnamese, Japanese. "
                "Powered by Diffusion Language Models with RTF ~0.025."
            ),
            size_gb=2.4,
            min_ram_gb=8,
            recommended_ram_gb=16,
            min_vram_gb=4,
            recommended_vram_gb=6,
            cpu_supported=True,
            cuda_supported=True,
            voice_cloning=True,
            languages_supported=[
                "en", "vi", "ja", "zh", "ko", "fr", "de", "es", "it",
                "pt", "ru", "ar", "th", "hi", "id", "ms", "tl",
            ],
            quality_score=10,
            speed_score=9,
            huggingface_id="k2-fsa/OmniVoice",
        ))

        # Set OmniVoice as active by default
        self._active_model_id = "omnivoice-multilingual"

    def _register(self, model: ModelInfo) -> None:
        """Register a model."""
        self._models[model.id] = model
        self._status[model.id] = ModelStatus.NOT_INSTALLED

    def get(self, model_id: str) -> Optional[ModelInfo]:
        """Get model info by ID."""
        return self._models.get(model_id)

    def get_all(self) -> list[ModelInfo]:
        """Get all registered models."""
        return list(self._models.values())

    def get_by_language(self, language: str) -> list[ModelInfo]:
        """Get models that support a specific language."""
        results = []
        for model in self._models.values():
            if model.language == "multi" or model.language == language:
                results.append(model)
            elif language in model.languages_supported:
                results.append(model)
        return results

    def get_cloning_models(self) -> list[ModelInfo]:
        """Get models that support voice cloning."""
        return [m for m in self._models.values() if m.voice_cloning]

    def get_status(self, model_id: str) -> ModelStatus:
        """Get the installation status of a model."""
        return self._status.get(model_id, ModelStatus.NOT_INSTALLED)

    def set_status(self, model_id: str, status: ModelStatus) -> None:
        """Update the status of a model."""
        if model_id in self._models:
            self._status[model_id] = status

    def get_active_model_id(self) -> Optional[str]:
        """Get the currently active model ID."""
        return self._active_model_id

    def set_active_model(self, model_id: str) -> None:
        """Set the active model."""
        if model_id not in self._models:
            raise ValueError(f"Model '{model_id}' not found in registry")
        self._active_model_id = model_id

    def get_installed_models(self) -> list[ModelInfo]:
        """Get all installed models."""
        return [
            m for m in self._models.values()
            if self._status.get(m.id) == ModelStatus.INSTALLED
        ]

    def to_dict_list(self) -> list[dict]:
        """Get all models as a list of dicts with status."""
        result = []
        for model in self._models.values():
            d = model.to_dict()
            d["status"] = self._status.get(model.id, ModelStatus.NOT_INSTALLED).value
            d["is_active"] = model.id == self._active_model_id
            result.append(d)
        return result


# Module-level singleton
_registry: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    """Get the global ModelRegistry."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
