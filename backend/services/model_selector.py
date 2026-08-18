"""
Model Selector for Local AI Voice Studio.
Simplified — OmniVoice is the single model for all languages.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from backend.services.model_registry import ModelInfo, ModelRegistry, get_model_registry
from backend.services.hardware_detector import HardwareProfile

logger = logging.getLogger(__name__)


@dataclass
class ModelScore:
    """Score result for a model."""
    model_id: str
    model_name: str
    total_score: float
    can_run: bool
    reason: str = ""


class ModelSelector:
    """
    Selects the best model based on hardware profile.
    With OmniVoice as the only model, this is simplified.
    """

    def __init__(self):
        self._registry = get_model_registry()

    def select_best(
        self,
        language: str,
        profile: HardwareProfile,
        require_cloning: bool = False,
    ) -> Optional[ModelInfo]:
        """Select the best model for the given language and hardware."""
        models = self._registry.get_by_language(language)
        if not models:
            return None

        # OmniVoice supports everything — return it
        return models[0]

    def recommend_all(
        self, profile: HardwareProfile
    ) -> dict[str, Optional[ModelInfo]]:
        """Get recommended models for all supported languages."""
        languages = ["en", "vi", "ja"]
        return {
            lang: self.select_best(lang, profile)
            for lang in languages
        }

    def score_all(
        self, language: str, profile: HardwareProfile
    ) -> list[ModelScore]:
        """Score all models for a given language."""
        models = self._registry.get_by_language(language)
        scores = []

        for model in models:
            can_run = True
            reason = "Compatible"

            # Check VRAM if GPU
            if profile.recommended_device == "cuda":
                if model.min_vram_gb > profile.gpu.vram_total_gb:
                    can_run = False
                    reason = f"Requires {model.min_vram_gb}GB VRAM, only {profile.gpu.vram_total_gb}GB available"
            else:
                # Check RAM for CPU mode
                if model.min_ram_gb > profile.ram.total_gb:
                    can_run = False
                    reason = f"Requires {model.min_ram_gb}GB RAM, only {profile.ram.total_gb}GB available"

            scores.append(ModelScore(
                model_id=model.id,
                model_name=model.name,
                total_score=model.quality_score if can_run else 0,
                can_run=can_run,
                reason=reason,
            ))

        scores.sort(key=lambda s: s.total_score, reverse=True)
        return scores


# Module-level singleton
_selector: Optional[ModelSelector] = None


def get_model_selector() -> ModelSelector:
    """Get the global ModelSelector."""
    global _selector
    if _selector is None:
        _selector = ModelSelector()
    return _selector
