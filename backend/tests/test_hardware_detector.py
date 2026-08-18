"""Tests for Hardware Detector."""
import pytest
from backend.services.hardware_detector import HardwareDetector, HardwareProfile


class TestHardwareDetector:
    def test_detect_returns_profile(self):
        detector = HardwareDetector()
        profile = detector.detect()
        assert isinstance(profile, HardwareProfile)

    def test_cpu_detection(self):
        detector = HardwareDetector()
        profile = detector.detect()
        assert profile.cpu.cores_logical > 0
        assert profile.cpu.cores_physical > 0
        assert profile.cpu.name != ""
        assert profile.cpu.name != "Unknown"

    def test_ram_detection(self):
        detector = HardwareDetector()
        profile = detector.detect()
        assert profile.ram.total_gb > 0
        assert profile.ram.available_gb > 0
        assert 0 <= profile.ram.used_percent <= 100

    def test_disk_detection(self):
        detector = HardwareDetector()
        profile = detector.detect()
        assert profile.disk.total_gb > 0
        assert profile.disk.free_gb >= 0

    def test_python_version(self):
        detector = HardwareDetector()
        profile = detector.detect()
        assert profile.python_version != ""
        assert "." in profile.python_version

    def test_os_detection(self):
        detector = HardwareDetector()
        profile = detector.detect()
        assert profile.os_name in ("Windows", "Linux", "Darwin")

    def test_recommended_device(self):
        detector = HardwareDetector()
        profile = detector.detect()
        assert profile.recommended_device in ("cpu", "cuda")

    def test_recommended_model_tier(self):
        detector = HardwareDetector()
        profile = detector.detect()
        valid_tiers = [
            "gpu_large", "gpu_medium", "gpu_small",
            "cpu_standard", "cpu_lightweight",
        ]
        assert profile.recommended_model_tier in valid_tiers

    def test_force_device_cpu(self):
        detector = HardwareDetector(force_device="cpu")
        profile = detector.detect()
        assert profile.recommended_device == "cpu"

    def test_profile_to_dict(self):
        detector = HardwareDetector()
        profile = detector.detect()
        d = profile.to_dict()
        assert isinstance(d, dict)
        assert "cpu" in d
        assert "ram" in d
        assert "gpu" in d
        assert "cuda" in d

    def test_get_profile_caching(self):
        detector = HardwareDetector()
        p1 = detector.detect()
        p2 = detector.get_profile()
        assert p1 is p2

    def test_gpu_info_structure(self):
        detector = HardwareDetector()
        profile = detector.detect()
        # GPU fields should always be present
        assert hasattr(profile.gpu, 'detected')
        assert hasattr(profile.gpu, 'name')
        assert hasattr(profile.gpu, 'vram_total_gb')
        assert isinstance(profile.gpu.detected, bool)
