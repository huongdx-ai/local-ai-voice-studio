"""
Model Registry for Local AI Voice Studio.
Defines all available TTS/voice-cloning models with metadata and capabilities.
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ModelEngine(str, Enum):
    CHATTERBOX = "chatterbox"
    KOKORO = "kokoro"
    PIPER = "piper"


class ModelStatus(str, Enum):
    NOT_INSTALLED = "not_installed"
    DOWNLOADING = "downloading"
    INSTALLED = "installed"
    ERROR = "error"


@dataclass
class ModelInfo:
    """Metadata for a TTS model."""
    id: str
    name: str
    language: str                  # ISO code: en, vi, ja
    engine: ModelEngine
    description: str = ""
    size_gb: float = 0.0
    min_ram_gb: float = 0.0
    recommended_ram_gb: float = 0.0
    min_vram_gb: float = 0.0
    recommended_vram_gb: float = 0.0
    cpu_supported: bool = True
    cuda_supported: bool = True
    voice_cloning: bool = False
    model_repo: str = ""           # HuggingFace repo or download URL
    model_files: list[str] = field(default_factory=list)
    pip_package: str = ""          # pip package name if installed via pip
    languages_supported: list[str] = field(default_factory=list)
    quality_score: int = 5         # 1-10 quality rating
    speed_score: int = 5           # 1-10 speed rating

    def to_dict(self) -> dict:
        d = asdict(self)
        d["engine"] = self.engine.value
        return d


# ─────────────────────────────────────────────────────────────────────
# Pre-defined Model Registry
# ─────────────────────────────────────────────────────────────────────

_BUILTIN_MODELS: list[ModelInfo] = [
    # ── Chatterbox V3 Multilingual (primary, all languages) ──
    ModelInfo(
        id="chatterbox-multilingual-v3",
        name="Chatterbox Multilingual V3",
        language="multi",
        engine=ModelEngine.CHATTERBOX,
        description="High-quality multilingual TTS with zero-shot voice cloning. Supports 23+ languages including English, Vietnamese, and Japanese.",
        size_gb=2.0,
        min_ram_gb=8,
        recommended_ram_gb=16,
        min_vram_gb=4,
        recommended_vram_gb=6,
        cpu_supported=True,
        cuda_supported=True,
        voice_cloning=True,
        pip_package="chatterbox-tts",
        languages_supported=["en", "vi", "ja", "zh", "ko", "fr", "de", "es", "it", "pt", "ru", "ar", "hi", "pl", "tr", "nl", "cs", "da", "fi", "el", "he", "no", "sv", "sw"],
        quality_score=9,
        speed_score=6,
    ),

    # ── Kokoro English (lightweight CPU fallback) ──
    ModelInfo(
        id="kokoro-en-v1",
        name="Kokoro English v1",
        language="en",
        engine=ModelEngine.KOKORO,
        description="Ultra-lightweight 82M parameter model. Extremely fast on CPU. Best for English narration when GPU is unavailable.",
        size_gb=0.3,
        min_ram_gb=4,
        recommended_ram_gb=8,
        min_vram_gb=0,
        recommended_vram_gb=2,
        cpu_supported=True,
        cuda_supported=True,
        voice_cloning=False,
        pip_package="kokoro",
        languages_supported=["en"],
        quality_score=8,
        speed_score=10,
    ),

    # ── Kokoro Japanese (lightweight CPU fallback) ──
    ModelInfo(
        id="kokoro-ja-v1",
        name="Kokoro Japanese v1",
        language="ja",
        engine=ModelEngine.KOKORO,
        description="Ultra-lightweight Japanese TTS. Extremely fast on CPU with natural prosody.",
        size_gb=0.3,
        min_ram_gb=4,
        recommended_ram_gb=8,
        min_vram_gb=0,
        recommended_vram_gb=2,
        cpu_supported=True,
        cuda_supported=True,
        voice_cloning=False,
        pip_package="kokoro",
        languages_supported=["ja"],
        quality_score=7,
        speed_score=10,
    ),

    # ── Piper Vietnamese (lightweight CPU fallback) ──
    ModelInfo(
        id="piper-vi-v1",
        name="Piper Vietnamese",
        language="vi",
        engine=ModelEngine.PIPER,
        description="Lightweight Vietnamese TTS optimized for CPU. Fast inference with acceptable quality.",
        size_gb=0.1,
        min_ram_gb=2,
        recommended_ram_gb=4,
        min_vram_gb=0,
        recommended_vram_gb=0,
        cpu_supported=True,
        cuda_supported=False,
        voice_cloning=False,
        pip_package="piper-tts",
        languages_supported=["vi"],
        quality_score=6,
        speed_score=10,
    ),
]


class ModelRegistry:
    """
    Registry of all available TTS models.
    Provides lookup, filtering, and metadata access.
    """

    def __init__(self):
        self._models: dict[str, ModelInfo] = {}
        self._status: dict[str, ModelStatus] = {}
        self._active_model_id: Optional[str] = None

        # Load built-in models
        for model in _BUILTIN_MODELS:
            self.register(model)

    def register(self, model: ModelInfo) -> None:
        """Register a model in the registry."""
        self._models[model.id] = model
        if model.id not in self._status:
            self._status[model.id] = ModelStatus.NOT_INSTALLED
        logger.debug(f"Registered model: {model.id}")

    def get_all(self) -> list[ModelInfo]:
        """Get all registered models."""
        return list(self._models.values())

    def get(self, model_id: str) -> Optional[ModelInfo]:
        """Get a model by ID."""
        return self._models.get(model_id)

    def get_by_language(self, language: str) -> list[ModelInfo]:
        """Get models that support a specific language."""
        results = []
        for model in self._models.values():
            if model.language == language or language in model.languages_supported:
                results.append(model)
        return results

    def get_by_engine(self, engine: ModelEngine) -> list[ModelInfo]:
        """Get models by engine type."""
        return [m for m in self._models.values() if m.engine == engine]

    def get_status(self, model_id: str) -> ModelStatus:
        """Get the installation status of a model."""
        return self._status.get(model_id, ModelStatus.NOT_INSTALLED)

    def set_status(self, model_id: str, status: ModelStatus) -> None:
        """Set the installation status of a model."""
        self._status[model_id] = status

    def get_active_model_id(self) -> Optional[str]:
        """Get the currently active model ID."""
        return self._active_model_id

    def set_active_model(self, model_id: str) -> None:
        """Set the active model."""
        if model_id in self._models:
            self._active_model_id = model_id
        else:
            raise ValueError(f"Model '{model_id}' not found in registry")

    def get_installed_models(self) -> list[ModelInfo]:
        """Get all installed models."""
        return [
            self._models[mid]
            for mid, status in self._status.items()
            if status == ModelStatus.INSTALLED and mid in self._models
        ]

    def get_cloning_models(self) -> list[ModelInfo]:
        """Get models that support voice cloning."""
        return [m for m in self._models.values() if m.voice_cloning]

    def to_dict_list(self) -> list[dict]:
        """Serialize all models with their status."""
        results = []
        for model in self._models.values():
            d = model.to_dict()
            d["status"] = self._status.get(model.id, ModelStatus.NOT_INSTALLED).value
            d["is_active"] = model.id == self._active_model_id
            results.append(d)
        return results


# Module-level singleton
_registry: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    """Get the global ModelRegistry singleton."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
