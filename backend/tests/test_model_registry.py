"""Tests for Model Registry and Model Selector."""
import pytest
from backend.services.model_registry import ModelRegistry, ModelInfo, ModelEngine, ModelStatus
from backend.services.model_selector import ModelSelector, ModelScore
from backend.services.hardware_detector import HardwareProfile, CPUInfo, RAMInfo, GPUInfo, CUDAInfo


class TestModelRegistry:
    def test_builtin_models_loaded(self):
        registry = ModelRegistry()
        models = registry.get_all()
        assert len(models) >= 4  # Chatterbox, Kokoro EN, Kokoro JA, Piper VI

    def test_get_by_id(self):
        registry = ModelRegistry()
        model = registry.get("chatterbox-multilingual-v3")
        assert model is not None
        assert model.name == "Chatterbox Multilingual V3"

    def test_get_nonexistent(self):
        registry = ModelRegistry()
        model = registry.get("nonexistent")
        assert model is None

    def test_get_by_language_english(self):
        registry = ModelRegistry()
        models = registry.get_by_language("en")
        assert len(models) >= 2  # Chatterbox + Kokoro

    def test_get_by_language_vietnamese(self):
        registry = ModelRegistry()
        models = registry.get_by_language("vi")
        assert len(models) >= 1  # Chatterbox + Piper

    def test_get_by_language_japanese(self):
        registry = ModelRegistry()
        models = registry.get_by_language("ja")
        assert len(models) >= 2  # Chatterbox + Kokoro

    def test_get_cloning_models(self):
        registry = ModelRegistry()
        cloning = registry.get_cloning_models()
        assert len(cloning) >= 1
        assert all(m.voice_cloning for m in cloning)

    def test_status_tracking(self):
        registry = ModelRegistry()
        model_id = "chatterbox-multilingual-v3"
        assert registry.get_status(model_id) == ModelStatus.NOT_INSTALLED

        registry.set_status(model_id, ModelStatus.INSTALLED)
        assert registry.get_status(model_id) == ModelStatus.INSTALLED

    def test_active_model(self):
        registry = ModelRegistry()
        assert registry.get_active_model_id() is None

        registry.set_active_model("chatterbox-multilingual-v3")
        assert registry.get_active_model_id() == "chatterbox-multilingual-v3"

    def test_set_active_invalid(self):
        registry = ModelRegistry()
        with pytest.raises(ValueError):
            registry.set_active_model("nonexistent")

    def test_to_dict_list(self):
        registry = ModelRegistry()
        items = registry.to_dict_list()
        assert isinstance(items, list)
        assert len(items) >= 4
        assert "status" in items[0]
        assert "is_active" in items[0]


class TestModelSelector:
    def _make_gpu_profile(self, vram_gb=12.0):
        return HardwareProfile(
            cpu=CPUInfo(name="Test CPU", cores_physical=8, cores_logical=16),
            ram=RAMInfo(total_gb=32.0, available_gb=24.0),
            gpu=GPUInfo(name="Test GPU", vendor="NVIDIA", vram_total_gb=vram_gb, detected=True),
            cuda=CUDAInfo(available=True, version="12.1"),
            recommended_device="cuda",
        )

    def _make_cpu_profile(self, ram_gb=16.0):
        return HardwareProfile(
            cpu=CPUInfo(name="Test CPU", cores_physical=4, cores_logical=8),
            ram=RAMInfo(total_gb=ram_gb, available_gb=ram_gb * 0.7),
            gpu=GPUInfo(detected=False),
            cuda=CUDAInfo(available=False),
            recommended_device="cpu",
        )

    def test_select_english_gpu(self):
        selector = ModelSelector()
        profile = self._make_gpu_profile(12.0)
        model = selector.select_best("en", profile)
        assert model is not None
        assert "en" in model.languages_supported or model.language in ("en", "multi")

    def test_select_japanese_gpu(self):
        selector = ModelSelector()
        profile = self._make_gpu_profile(8.0)
        model = selector.select_best("ja", profile)
        assert model is not None

    def test_select_vietnamese_gpu(self):
        selector = ModelSelector()
        profile = self._make_gpu_profile(8.0)
        model = selector.select_best("vi", profile)
        assert model is not None

    def test_select_with_cloning(self):
        selector = ModelSelector()
        profile = self._make_gpu_profile(12.0)
        model = selector.select_best("en", profile, require_cloning=True)
        assert model is not None
        assert model.voice_cloning is True

    def test_select_cpu_fallback(self):
        selector = ModelSelector()
        profile = self._make_cpu_profile(16.0)
        model = selector.select_best("en", profile)
        assert model is not None

    def test_recommend_all(self):
        selector = ModelSelector()
        profile = self._make_gpu_profile(12.0)
        recs = selector.recommend_all(profile)
        assert "en" in recs
        assert "vi" in recs
        assert "ja" in recs

    def test_score_all_returns_sorted(self):
        selector = ModelSelector()
        profile = self._make_gpu_profile(12.0)
        scores = selector.score_all("en", profile)
        assert len(scores) > 0
        # Should be sorted descending
        for i in range(len(scores) - 1):
            assert scores[i].total_score >= scores[i + 1].total_score

    def test_low_vram_excludes_large_models(self):
        selector = ModelSelector()
        profile = self._make_gpu_profile(2.0)
        scores = selector.score_all("en", profile)
        chatterbox_score = next(
            (s for s in scores if s.model_id == "chatterbox-multilingual-v3"), None
        )
        if chatterbox_score:
            # Chatterbox needs 4GB VRAM min, so with 2GB it shouldn't run
            assert not chatterbox_score.can_run
