"""
Audio Validator for Local AI Voice Studio.
Analyzes uploaded voice samples for quality and compatibility.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class AudioAnalysis:
    """Results of voice sample analysis."""
    duration_seconds: float = 0.0
    sample_rate: int = 0
    channels: int = 0
    bit_depth: int = 16
    # Quality metrics
    rms_volume: float = 0.0          # Root mean square volume (0-1)
    peak_volume: float = 0.0         # Peak amplitude (0-1)
    silence_ratio: float = 0.0       # Ratio of silence in the sample
    clipping_detected: bool = False
    clipping_ratio: float = 0.0      # Ratio of clipped samples
    noise_level: str = "Unknown"     # "Low", "Medium", "High"
    noise_score: float = 0.0         # 0-1, lower is better
    # Overall quality
    quality: str = "Unknown"         # "Excellent", "Good", "Fair", "Poor"
    quality_score: float = 0.0       # 0-100
    warnings: list[str] = None
    is_usable: bool = True

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

    def to_dict(self) -> dict:
        return {
            "duration_seconds": self.duration_seconds,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "bit_depth": self.bit_depth,
            "rms_volume": round(self.rms_volume, 4),
            "peak_volume": round(self.peak_volume, 4),
            "silence_ratio": round(self.silence_ratio, 4),
            "clipping_detected": self.clipping_detected,
            "clipping_ratio": round(self.clipping_ratio, 4),
            "noise_level": self.noise_level,
            "noise_score": round(self.noise_score, 4),
            "quality": self.quality,
            "quality_score": round(self.quality_score, 1),
            "warnings": self.warnings,
            "is_usable": self.is_usable,
        }


class AudioValidator:
    """Validates and analyzes voice samples for quality."""

    def __init__(
        self,
        min_duration: float = 3.0,
        max_duration: float = 300.0,
        min_sample_rate: int = 16000,
    ):
        self._min_duration = min_duration
        self._max_duration = max_duration
        self._min_sample_rate = min_sample_rate

    def analyze(self, audio_path: Path) -> AudioAnalysis:
        """
        Analyze an audio file and return quality metrics.
        Does NOT block the file from being used — only provides warnings.
        """
        analysis = AudioAnalysis()

        try:
            import librosa
            import soundfile as sf

            # Load audio info without loading full data
            info = sf.info(str(audio_path))
            analysis.duration_seconds = round(info.duration, 2)
            analysis.sample_rate = info.samplerate
            analysis.channels = info.channels

            # Load audio data for analysis
            audio, sr = librosa.load(str(audio_path), sr=None, mono=True)

            # Normalize to float [-1, 1]
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            max_val = np.max(np.abs(audio))
            if max_val > 0:
                audio_norm = audio / max_val
            else:
                audio_norm = audio

            # Duration check
            if analysis.duration_seconds < self._min_duration:
                analysis.warnings.append(
                    f"Audio is too short ({analysis.duration_seconds}s). "
                    f"Minimum recommended: {self._min_duration}s."
                )
            if analysis.duration_seconds > self._max_duration:
                analysis.warnings.append(
                    f"Audio is very long ({analysis.duration_seconds}s). "
                    f"Consider trimming to under {self._max_duration}s."
                )

            # Sample rate check
            if analysis.sample_rate < self._min_sample_rate:
                analysis.warnings.append(
                    f"Sample rate ({analysis.sample_rate} Hz) is below "
                    f"recommended minimum ({self._min_sample_rate} Hz)."
                )

            # Volume analysis
            analysis.rms_volume = float(np.sqrt(np.mean(audio_norm ** 2)))
            analysis.peak_volume = float(np.max(np.abs(audio_norm)))

            if analysis.rms_volume < 0.01:
                analysis.warnings.append(
                    "Audio volume is very low. The recording may be too quiet."
                )

            # Clipping detection
            clip_threshold = 0.99
            clipped_samples = np.sum(np.abs(audio_norm) > clip_threshold)
            analysis.clipping_ratio = float(clipped_samples / len(audio_norm))
            analysis.clipping_detected = analysis.clipping_ratio > 0.001

            if analysis.clipping_detected:
                analysis.warnings.append(
                    f"Clipping detected ({analysis.clipping_ratio * 100:.2f}% of samples). "
                    "The audio may have distortion."
                )

            # Silence detection
            silence_threshold = 0.02
            silent_samples = np.sum(np.abs(audio_norm) < silence_threshold)
            analysis.silence_ratio = float(silent_samples / len(audio_norm))

            if analysis.silence_ratio > 0.7:
                analysis.warnings.append(
                    f"Audio contains {analysis.silence_ratio * 100:.0f}% silence. "
                    "Consider trimming silent portions."
                )

            # Noise estimation (simple spectral method)
            analysis.noise_score = self._estimate_noise(audio_norm, sr)
            if analysis.noise_score < 0.3:
                analysis.noise_level = "Low"
            elif analysis.noise_score < 0.6:
                analysis.noise_level = "Medium"
                analysis.warnings.append(
                    "Moderate background noise detected. "
                    "A cleaner recording may produce better results."
                )
            else:
                analysis.noise_level = "High"
                analysis.warnings.append(
                    "High background noise detected. "
                    "Please upload a cleaner recording for best results."
                )

            # Overall quality score
            analysis.quality_score = self._calculate_quality_score(analysis)
            if analysis.quality_score >= 80:
                analysis.quality = "Excellent"
            elif analysis.quality_score >= 60:
                analysis.quality = "Good"
            elif analysis.quality_score >= 40:
                analysis.quality = "Fair"
            else:
                analysis.quality = "Poor"

            # Usability — we don't block, just warn
            analysis.is_usable = (
                analysis.duration_seconds >= 1.0
                and analysis.rms_volume > 0.005
            )

        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            analysis.warnings.append(f"Analysis error: {str(e)}")
            analysis.quality = "Unknown"

        return analysis

    def _estimate_noise(self, audio: np.ndarray, sr: int) -> float:
        """
        Estimate background noise level using spectral flatness.
        Returns 0.0 (clean) to 1.0 (noisy).
        """
        try:
            import librosa

            # Spectral flatness: high = noise-like, low = tonal
            flatness = librosa.feature.spectral_flatness(y=audio)
            mean_flatness = float(np.mean(flatness))

            # Normalize to 0-1 range
            # Typical speech: 0.01-0.1, noise: 0.3-1.0
            noise_score = min(1.0, mean_flatness * 3.0)
            return noise_score
        except Exception:
            return 0.5  # Unknown

    def _calculate_quality_score(self, analysis: AudioAnalysis) -> float:
        """Calculate an overall quality score (0-100)."""
        score = 100.0

        # Duration penalty
        if analysis.duration_seconds < 3:
            score -= 20
        elif analysis.duration_seconds < 5:
            score -= 10

        # Volume penalty
        if analysis.rms_volume < 0.01:
            score -= 30
        elif analysis.rms_volume < 0.05:
            score -= 15

        # Clipping penalty
        if analysis.clipping_detected:
            score -= min(30, analysis.clipping_ratio * 1000)

        # Silence penalty
        if analysis.silence_ratio > 0.7:
            score -= 20
        elif analysis.silence_ratio > 0.5:
            score -= 10

        # Noise penalty
        score -= analysis.noise_score * 25

        # Sample rate bonus/penalty
        if analysis.sample_rate >= 44100:
            score += 5
        elif analysis.sample_rate < 16000:
            score -= 15

        return max(0, min(100, score))
