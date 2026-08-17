"""
Model Selector for Local AI Voice Studio.
Scores and ranks models based on hardware profile and config thresholds.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from backend.services.hardware_detector import HardwareProfile
from backend.services.model_registry import ModelInfo, ModelRegistry, get_model_registry
from backend.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class ModelScore:
    """Score breakdown for a model selection candidate."""
    model_id: str
    total_score: float
    compatibility_score: float   # Can it run at all?
    quality_score: float         # Voice quality rating
    performance_score: float     # Speed / efficiency
    cloning_score: float         # Voice cloning capability
    language_match: bool         # Does it support the target language?
    can_run: bool                # Is hardware sufficient?
    reason: str = ""


class ModelSelector:
    """
    Selects the best model for a given language and hardware profile.
    Uses a scoring algorithm with config-driven thresholds.
    """

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
    ):
        self._registry = registry or get_model_registry()
        self._config = get_config()

    def select_best(
        self,
        language: str,
        hardware: HardwareProfile,
        require_cloning: bool = False,
    ) -> Optional[ModelInfo]:
        """
        Select the best model for the given language and hardware.
        Returns None if no suitable model found.
        """
        scores = self.score_all(language, hardware, require_cloning)
        runnable = [s for s in scores if s.can_run and s.language_match]

        if not runnable:
            logger.warning(
                f"No suitable model found for language='{language}', "
                f"cloning={require_cloning}"
            )
            return None

        best = max(runnable, key=lambda s: s.total_score)
        model = self._registry.get(best.model_id)
        logger.info(
            f"Selected model '{best.model_id}' for language='{language}' "
            f"(score={best.total_score:.1f}, reason='{best.reason}')"
        )
        return model

    def recommend_all(
        self,
        hardware: HardwareProfile,
    ) -> dict[str, Optional[ModelInfo]]:
        """
        Recommend the best model for each supported language.
        Returns a dict: { "en": ModelInfo, "vi": ModelInfo, "ja": ModelInfo }
        """
        languages = ["en", "vi", "ja"]
        result = {}
        for lang in languages:
            result[lang] = self.select_best(lang, hardware)
        return result

    def score_all(
        self,
        language: str,
        hardware: HardwareProfile,
        require_cloning: bool = False,
    ) -> list[ModelScore]:
        """Score all models for the given language and hardware."""
        models = self._registry.get_all()
        scores = []
        for model in models:
            score = self._score_model(model, language, hardware, require_cloning)
            scores.append(score)
        return sorted(scores, key=lambda s: s.total_score, reverse=True)

    def _score_model(
        self,
        model: ModelInfo,
        language: str,
        hardware: HardwareProfile,
        require_cloning: bool,
    ) -> ModelScore:
        """Score a single model against hardware and requirements."""
        thresholds = self._config.models.thresholds
        device = hardware.recommended_device

        # Language match
        lang_match = (
            model.language == language
            or model.language == "multi"
            or language in model.languages_supported
        )

        # Hardware compatibility
        can_run = True
        compat_score = 0.0
        reason_parts = []

        if device == "cuda" and model.cuda_supported:
            vram = hardware.gpu.vram_total_gb
            if vram < model.min_vram_gb:
                can_run = False
                reason_parts.append(f"Need {model.min_vram_gb}GB VRAM, have {vram}GB")
            elif vram >= model.recommended_vram_gb:
                compat_score = 10.0
                reason_parts.append("Excellent VRAM match")
            else:
                compat_score = 7.0
                reason_parts.append("Adequate VRAM")
        elif device == "cpu" and model.cpu_supported:
            ram = hardware.ram.total_gb
            if ram < model.min_ram_gb:
                can_run = False
                reason_parts.append(f"Need {model.min_ram_gb}GB RAM, have {ram}GB")
            elif ram >= model.recommended_ram_gb:
                compat_score = 8.0
                reason_parts.append("Good RAM for CPU mode")
            else:
                compat_score = 5.0
                reason_parts.append("Minimal RAM")
        elif device == "cuda" and not model.cuda_supported:
            # Model doesn't support CUDA but we have GPU — can still run on CPU
            if model.cpu_supported:
                compat_score = 4.0
                reason_parts.append("CPU-only model (GPU available but unused)")
                ram = hardware.ram.total_gb
                if ram < model.min_ram_gb:
                    can_run = False
            else:
                can_run = False
                reason_parts.append("Incompatible with available hardware")
        else:
            can_run = False
            reason_parts.append("Incompatible with available hardware")

        # Quality score (from model metadata, normalized to 0-10)
        quality = float(model.quality_score)

        # Performance score
        perf = float(model.speed_score)
        # Bonus for GPU models when GPU is available
        if device == "cuda" and model.cuda_supported:
            perf = min(10.0, perf + 1.0)

        # Cloning capability
        cloning = 0.0
        if model.voice_cloning:
            cloning = 10.0
        if require_cloning and not model.voice_cloning:
            can_run = False
            reason_parts.append("Voice cloning required but not supported")

        # Weighted total score
        # Quality is most important, then compatibility, then cloning, then performance
        total = (
            quality * 0.35
            + compat_score * 0.25
            + cloning * 0.25
            + perf * 0.15
        )

        if not lang_match:
            total = 0.0
            reason_parts.append("Language not supported")

        return ModelScore(
            model_id=model.id,
            total_score=round(total, 2),
            compatibility_score=compat_score,
            quality_score=quality,
            performance_score=perf,
            cloning_score=cloning,
            language_match=lang_match,
            can_run=can_run,
            reason="; ".join(reason_parts) if reason_parts else "Good match",
        )


# Module-level singleton
_selector: Optional[ModelSelector] = None


def get_model_selector() -> ModelSelector:
    """Get the global ModelSelector singleton."""
    global _selector
    if _selector is None:
        _selector = ModelSelector()
    return _selector
