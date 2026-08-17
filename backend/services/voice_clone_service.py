"""
Voice Clone Service for Local AI Voice Studio.
Handles voice sample upload, validation, embedding extraction, and profile management.
"""

import json
import uuid
import shutil
import logging
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

from backend.config import get_config, get_project_root
from backend.services.audio_validator import AudioValidator, AudioAnalysis

logger = logging.getLogger(__name__)


@dataclass
class VoiceProfile:
    """A saved voice profile for cloning."""
    id: str
    name: str
    language: str
    duration_seconds: float
    sample_rate: int
    quality: str
    quality_score: float
    created_at: str
    file_format: str = "wav"

    def to_dict(self) -> dict:
        return asdict(self)


class VoiceCloneService:
    """
    Manages voice profiles for voice cloning.
    Handles upload, validation, conversion, and CRUD.
    """

    def __init__(self):
        self._config = get_config()
        self._voices_dir = get_project_root() / self._config.voices.storage_dir
        self._voices_dir.mkdir(parents=True, exist_ok=True)
        self._validator = AudioValidator(
            min_duration=self._config.voices.validation.min_duration,
            max_duration=self._config.voices.validation.max_duration,
            min_sample_rate=self._config.voices.validation.min_sample_rate,
        )
        self._profiles: dict[str, VoiceProfile] = {}
        self._load_existing_profiles()

    def _load_existing_profiles(self) -> None:
        """Load existing voice profiles from disk."""
        for voice_dir in self._voices_dir.iterdir():
            if voice_dir.is_dir():
                meta_path = voice_dir / "metadata.json"
                if meta_path.exists():
                    try:
                        with open(meta_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        profile = VoiceProfile(**data)
                        self._profiles[profile.id] = profile
                    except Exception as e:
                        logger.warning(f"Failed to load voice profile from {voice_dir}: {e}")

    async def upload_voice(
        self,
        file_data: bytes,
        filename: str,
        name: str,
        language: str = "en",
    ) -> tuple[VoiceProfile, AudioAnalysis]:
        """
        Upload and process a voice sample.
        Returns the created profile and analysis results.
        """
        # Validate file extension
        ext = Path(filename).suffix.lower()
        if ext not in self._config.voices.supported_formats:
            raise ValueError(
                f"Unsupported format '{ext}'. "
                f"Supported: {', '.join(self._config.voices.supported_formats)}"
            )

        # Check file size
        size_mb = len(file_data) / (1024 * 1024)
        if size_mb > self._config.voices.max_upload_size_mb:
            raise ValueError(
                f"File too large ({size_mb:.1f} MB). "
                f"Maximum: {self._config.voices.max_upload_size_mb} MB."
            )

        # Create voice directory
        voice_id = str(uuid.uuid4())[:8]
        voice_dir = self._voices_dir / voice_id
        voice_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Save original upload
            original_path = voice_dir / f"original{ext}"
            with open(original_path, "wb") as f:
                f.write(file_data)

            # Convert to WAV (standardized format for processing)
            sample_path = voice_dir / "sample.wav"
            self._convert_to_wav(original_path, sample_path)

            # Validate and analyze
            analysis = self._validator.analyze(sample_path)

            # Create profile
            profile = VoiceProfile(
                id=voice_id,
                name=name,
                language=language,
                duration_seconds=analysis.duration_seconds,
                sample_rate=analysis.sample_rate,
                quality=analysis.quality,
                quality_score=analysis.quality_score,
                created_at=datetime.now(timezone.utc).isoformat(),
            )

            # Save metadata
            meta_path = voice_dir / "metadata.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(profile.to_dict(), f, indent=2)

            self._profiles[profile.id] = profile

            logger.info(
                f"Voice profile created: id={voice_id}, name='{name}', "
                f"quality={analysis.quality}"
            )

            return profile, analysis

        except Exception as e:
            # Clean up on failure
            if voice_dir.exists():
                shutil.rmtree(voice_dir)
            raise

    def _convert_to_wav(self, input_path: Path, output_path: Path) -> None:
        """Convert any supported audio format to WAV 16kHz mono."""
        try:
            import librosa
            import soundfile as sf

            # Load and convert
            audio, sr = librosa.load(str(input_path), sr=16000, mono=True)

            # Normalize volume
            max_val = max(abs(audio.max()), abs(audio.min()))
            if max_val > 0:
                audio = audio / max_val * 0.95  # Leave headroom

            # Remove leading/trailing silence
            trimmed, _ = librosa.effects.trim(audio, top_db=30)

            # Save
            sf.write(str(output_path), trimmed, 16000)

        except Exception as e:
            # Fallback: try pydub
            try:
                from pydub import AudioSegment

                audio = AudioSegment.from_file(str(input_path))
                audio = audio.set_channels(1).set_frame_rate(16000)
                audio.export(str(output_path), format="wav")
            except Exception as e2:
                raise RuntimeError(
                    f"Failed to convert audio: {e}. Fallback also failed: {e2}"
                )

    def get_all_profiles(self) -> list[VoiceProfile]:
        """Get all voice profiles."""
        return list(self._profiles.values())

    def get_profile(self, voice_id: str) -> Optional[VoiceProfile]:
        """Get a voice profile by ID."""
        return self._profiles.get(voice_id)

    def get_sample_path(self, voice_id: str) -> Optional[Path]:
        """Get the path to a voice sample WAV file."""
        voice_dir = self._voices_dir / voice_id
        sample = voice_dir / "sample.wav"
        if sample.exists():
            return sample
        return None

    async def rename_voice(self, voice_id: str, new_name: str) -> Optional[VoiceProfile]:
        """Rename a voice profile."""
        profile = self._profiles.get(voice_id)
        if profile is None:
            return None

        profile.name = new_name

        # Update metadata on disk
        meta_path = self._voices_dir / voice_id / "metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, indent=2)

        return profile

    async def delete_voice(self, voice_id: str) -> bool:
        """Delete a voice profile and its files."""
        voice_dir = self._voices_dir / voice_id
        if voice_dir.exists():
            try:
                shutil.rmtree(voice_dir)
                self._profiles.pop(voice_id, None)
                logger.info(f"Deleted voice profile: {voice_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete voice {voice_id}: {e}")
                return False
        self._profiles.pop(voice_id, None)
        return True

    def get_voice_count(self) -> int:
        """Get the number of voice profiles."""
        return len(self._profiles)


# Module-level singleton
_service: Optional[VoiceCloneService] = None


def get_voice_clone_service() -> VoiceCloneService:
    """Get the global VoiceCloneService singleton."""
    global _service
    if _service is None:
        _service = VoiceCloneService()
    return _service
