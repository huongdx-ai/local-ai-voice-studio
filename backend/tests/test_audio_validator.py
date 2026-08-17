"""Tests for Audio Validator."""
import pytest
import numpy as np
import tempfile
from pathlib import Path


class TestAudioValidator:
    def _create_test_wav(self, duration=5.0, sr=22050, noise_level=0.01):
        """Create a test WAV file with a sine wave."""
        import soundfile as sf

        t = np.linspace(0, duration, int(sr * duration), dtype=np.float32)
        # 440 Hz sine wave + optional noise
        audio = 0.5 * np.sin(2 * np.pi * 440 * t) + noise_level * np.random.randn(len(t)).astype(np.float32)
        audio = np.clip(audio, -1.0, 1.0)

        path = Path(tempfile.mktemp(suffix=".wav"))
        sf.write(str(path), audio, sr)
        return path

    def test_clean_audio_excellent(self):
        from backend.services.audio_validator import AudioValidator

        path = self._create_test_wav(duration=10.0, noise_level=0.01)
        validator = AudioValidator()
        analysis = validator.analyze(path)

        assert analysis.duration_seconds > 0
        assert analysis.sample_rate == 22050
        assert analysis.quality in ("Excellent", "Good")
        assert analysis.is_usable is True
        assert analysis.quality_score > 60

        path.unlink()

    def test_short_audio_warning(self):
        from backend.services.audio_validator import AudioValidator

        path = self._create_test_wav(duration=1.0)
        validator = AudioValidator(min_duration=3.0)
        analysis = validator.analyze(path)

        assert any("too short" in w.lower() for w in analysis.warnings)
        assert analysis.is_usable is True  # Still usable, just warned

        path.unlink()

    def test_noisy_audio_warning(self):
        from backend.services.audio_validator import AudioValidator

        path = self._create_test_wav(duration=5.0, noise_level=0.5)
        validator = AudioValidator()
        analysis = validator.analyze(path)

        assert analysis.noise_level in ("Medium", "High")
        assert analysis.is_usable is True

        path.unlink()

    def test_silent_audio(self):
        """Test with nearly silent audio."""
        import soundfile as sf
        from backend.services.audio_validator import AudioValidator

        sr = 22050
        audio = np.zeros(sr * 5, dtype=np.float32)  # 5s silence
        path = Path(tempfile.mktemp(suffix=".wav"))
        sf.write(str(path), audio, sr)

        validator = AudioValidator()
        analysis = validator.analyze(path)

        assert analysis.silence_ratio > 0.9
        assert analysis.is_usable is False  # Silent audio not usable

        path.unlink()

    def test_analysis_to_dict(self):
        from backend.services.audio_validator import AudioValidator

        path = self._create_test_wav()
        validator = AudioValidator()
        analysis = validator.analyze(path)
        d = analysis.to_dict()

        assert isinstance(d, dict)
        assert "duration_seconds" in d
        assert "quality" in d
        assert "warnings" in d

        path.unlink()
