"""Tests for Model Registry and Model Selector."""
import pytest
from backend.services.model_registry import ModelRegistry, ModelInfo, ModelEngine, ModelStatus
from backend.services.model_selector import ModelSelector, ModelScore
from backend.services.hardware_detector import HardwareProfile, CPUInfo, RAMInfo, GPUInfo, CUDAInfo


class TestModelRegistry:
    def test_omnivoice_model_loaded(self):
        registry = ModelRegistry()
        models = registry.get_all()
        assert len(models) >= 1

    def test_get_omnivoice(self):
        registry = ModelRegistry()
        model = registry.get("omnivoice-multilingual")
        assert model is not None
        assert model.name == "OmniVoice"
        assert model.engine == ModelEngine.OMNIVOICE

    def test_get_nonexistent(self):
        registry = ModelRegistry()
        model = registry.get("nonexistent")
        assert model is None

    def test_omnivoice_supports_english(self):
        registry = ModelRegistry()
        models = registry.get_by_language("en")
        assert len(models) >= 1
        assert any(m.id == "omnivoice-multilingual" for m in models)

    def test_omnivoice_supports_vietnamese(self):
        registry = ModelRegistry()
        models = registry.get_by_language("vi")
        assert len(models) >= 1

    def test_omnivoice_supports_japanese(self):
        registry = ModelRegistry()
        models = registry.get_by_language("ja")
        assert len(models) >= 1

    def test_omnivoice_supports_cloning(self):
        registry = ModelRegistry()
        cloning = registry.get_cloning_models()
        assert len(cloning) >= 1
        assert all(m.voice_cloning for m in cloning)

    def test_status_tracking(self):
        registry = ModelRegistry()
        model_id = "omnivoice-multilingual"
        # Default should be NOT_INSTALLED or INSTALLED depending on pip
        status = registry.get_status(model_id)
        assert status in (ModelStatus.NOT_INSTALLED, ModelStatus.INSTALLED)

    def test_active_model_default(self):
        registry = ModelRegistry()
        # OmniVoice should be active by default
        assert registry.get_active_model_id() == "omnivoice-multilingual"

    def test_set_active_invalid(self):
        registry = ModelRegistry()
        with pytest.raises(ValueError):
            registry.set_active_model("nonexistent")

    def test_to_dict_list(self):
        registry = ModelRegistry()
        items = registry.to_dict_list()
        assert isinstance(items, list)
        assert len(items) >= 1
        assert "status" in items[0]
        assert "is_active" in items[0]

    def test_omnivoice_has_huggingface_id(self):
        registry = ModelRegistry()
        model = registry.get("omnivoice-multilingual")
        assert model.huggingface_id == "k2-fsa/OmniVoice"


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

    def test_select_returns_omnivoice(self):
        selector = ModelSelector()
        profile = self._make_gpu_profile(12.0)
        model = selector.select_best("en", profile)
        assert model is not None
        assert model.id == "omnivoice-multilingual"

    def test_select_all_languages(self):
        selector = ModelSelector()
        profile = self._make_gpu_profile(8.0)
        for lang in ["en", "vi", "ja"]:
            model = selector.select_best(lang, profile)
            assert model is not None
            assert model.id == "omnivoice-multilingual"

    def test_recommend_all(self):
        selector = ModelSelector()
        profile = self._make_gpu_profile(12.0)
        recs = selector.recommend_all(profile)
        assert "en" in recs
        assert "vi" in recs
        assert "ja" in recs
        # All should be OmniVoice
        for lang, model in recs.items():
            assert model is not None
            assert model.id == "omnivoice-multilingual"

    def test_cpu_mode_works(self):
        selector = ModelSelector()
        profile = self._make_cpu_profile(16.0)
        model = selector.select_best("en", profile)
        assert model is not None
