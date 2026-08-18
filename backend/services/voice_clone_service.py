"""
Voice Clone Service for Local AI Voice Studio.
Handles voice sample upload, universal format conversion (WAV, MP3, M4A, AAC, FLAC, OGG, WebM, WMA),
audio quality validation, VoiceClonePrompt extraction, and profile management.
"""

import gc
import json
import uuid
import shutil
import logging
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

import numpy as np
import soundfile as sf

from backend.config import get_config, get_project_root
from backend.services.audio_validator import AudioValidator, AudioAnalysis

logger = logging.getLogger(__name__)


@dataclass
class VoiceProfile:
    """A saved voice profile for zero-shot cloning."""
    id: str
    name: str
    language: str
    duration_seconds: float
    sample_rate: int
    quality: str
    quality_score: float
    created_at: str
    file_format: str = "wav"
    has_prompt: bool = False
    ref_text: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class VoiceCloneService:
    """
    Manages voice profiles for voice cloning with OmniVoice.
    Handles upload, universal decoding to 24kHz mono WAV, prompt extraction, and CRUD.
    """

    def __init__(self):
        self._config = get_config()
        self._voices_dir = get_project_root() / self._config.voices.storage_dir
        self._voices_dir.mkdir(parents=True, exist_ok=True)
        self._validator = AudioValidator(
            min_duration=1.0,
            max_duration=300.0,
            min_sample_rate=16000,
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
                        prompt_path = voice_dir / "prompt.pt"
                        data["has_prompt"] = prompt_path.exists()
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
        ref_text: Optional[str] = None,
    ) -> tuple[VoiceProfile, AudioAnalysis]:
        """
        Upload and process a voice sample.
        Converts any format (including .m4a) to 24kHz mono WAV, validates quality,
        and saves profile immediately without blocking or file locks.
        """
        supported = [".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm", ".aac", ".wma", ".mp4", ".opus"]
        ext = Path(filename).suffix.lower()
        if ext not in supported:
            raise ValueError(
                f"Unsupported audio format '{ext}'. Supported formats: {', '.join(supported)}"
            )

        # Check file size (max 50MB)
        size_mb = len(file_data) / (1024 * 1024)
        if size_mb > 50.0:
            raise ValueError(f"File too large ({size_mb:.1f} MB). Maximum allowed is 50 MB.")

        voice_id = str(uuid.uuid4())[:8]
        voice_dir = self._voices_dir / voice_id
        voice_dir.mkdir(parents=True, exist_ok=True)

        original_path = voice_dir / f"original{ext}"
        sample_path = voice_dir / "sample.wav"

        try:
            # 1. Save original file
            with open(original_path, "wb") as f:
                f.write(file_data)

            # 2. Universal decoding to normalized 24kHz mono WAV
            self._convert_to_wav_24k(original_path, sample_path)

            # 3. Analyze audio quality
            analysis = self._validator.analyze(sample_path)

            # 4. Attempt prompt extraction if ref_text provided and model in memory
            has_prompt = False
            extracted_text = (ref_text or "").strip()

            try:
                from backend.services.tts_service import get_tts_service
                tts = get_tts_service()
                provider = tts.get_provider("omnivoice")
                if provider and provider.is_loaded() and hasattr(provider, "extract_voice_clone_prompt"):
                    prompt = provider.extract_voice_clone_prompt(
                        sample_path,
                        ref_text=extracted_text if extracted_text else None,
                    )
                    if prompt:
                        prompt_path = voice_dir / "prompt.pt"
                        prompt.save(str(prompt_path))
                        has_prompt = True
                        if hasattr(prompt, "ref_text") and prompt.ref_text:
                            extracted_text = prompt.ref_text
            except Exception as e:
                logger.debug(f"Prompt pre-extraction skipped: {e}")

            # 5. Create voice profile
            profile = VoiceProfile(
                id=voice_id,
                name=name.strip(),
                language=language,
                duration_seconds=analysis.duration_seconds,
                sample_rate=24000,
                quality=analysis.quality,
                quality_score=analysis.quality_score,
                created_at=datetime.now(timezone.utc).isoformat(),
                file_format="wav",
                has_prompt=has_prompt,
                ref_text=extracted_text,
            )

            # 6. Save metadata
            meta_path = voice_dir / "metadata.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)

            self._profiles[profile.id] = profile
            logger.info(f"Voice profile created successfully: id={voice_id}, name='{name}'")

            return profile, analysis

        except Exception as e:
            gc.collect()
            if voice_dir.exists():
                try:
                    shutil.rmtree(voice_dir, ignore_errors=True)
                except Exception:
                    pass
            logger.error(f"Voice upload failed: {e}")
            raise ValueError(f"Could not process audio sample ({filename}): {e}")

    def _convert_to_wav_24k(self, input_path: Path, output_path: Path) -> None:
        """
        Universal converter to normalized 24kHz mono WAV.
        Uses PyAV (handles M4A, AAC, MP3, FLAC, OGG, WebM, WAV, WMA) with fallbacks.
        """
        audio_array = None

        # Method 1: PyAV (Universal decoder, works perfectly for .m4a and all formats)
        try:
            import av
            container = av.open(str(input_path))
            resampler = av.AudioResampler(format='fltp', layout='mono', rate=24000)
            frames = []
            for frame in container.decode(audio=0):
                for r_frame in resampler.resample(frame):
                    frames.append(r_frame.to_ndarray())
            container.close()

            if frames:
                audio_array = np.concatenate(frames, axis=1)[0]
        except Exception as e:
            logger.debug(f"PyAV decode fallback: {e}")

        # Method 2: Soundfile (WAV, FLAC, OGG, MP3)
        if audio_array is None:
            try:
                data, in_sr = sf.read(str(input_path))
                if data.ndim > 1:
                    data = np.mean(data, axis=1)
                if in_sr != 24000:
                    import librosa
                    data = librosa.resample(data.astype(np.float32), orig_sr=in_sr, target_sr=24000)
                audio_array = data
            except Exception:
                pass

        # Method 3: Librosa
        if audio_array is None:
            try:
                import librosa
                audio_array, _ = librosa.load(str(input_path), sr=24000, mono=True)
            except Exception:
                pass

        if audio_array is None or len(audio_array) == 0:
            raise RuntimeError(f"Unable to decode audio format from {input_path.name}")

        # Trim silence
        try:
            import librosa
            trimmed, _ = librosa.effects.trim(audio_array, top_db=30)
            if len(trimmed) > 0:
                audio_array = trimmed
        except Exception:
            pass

        # Normalize peak
        max_val = np.max(np.abs(audio_array))
        if max_val > 0:
            audio_array = audio_array / max_val * 0.95

        sf.write(str(output_path), audio_array.astype(np.float32), 24000)

    def get_all_profiles(self) -> list[VoiceProfile]:
        return list(self._profiles.values())

    def get_profile(self, voice_id: str) -> Optional[VoiceProfile]:
        return self._profiles.get(voice_id)

    def get_sample_path(self, voice_id: str) -> Optional[Path]:
        voice_dir = self._voices_dir / voice_id
        sample = voice_dir / "sample.wav"
        if sample.exists():
            return sample
        return None

    def get_prompt_path(self, voice_id: str) -> Optional[Path]:
        voice_dir = self._voices_dir / voice_id
        prompt = voice_dir / "prompt.pt"
        if prompt.exists():
            return prompt
        return None

    async def rename_voice(self, voice_id: str, new_name: str) -> Optional[VoiceProfile]:
        profile = self._profiles.get(voice_id)
        if profile is None:
            return None

        profile.name = new_name
        meta_path = self._voices_dir / voice_id / "metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)

        return profile

    async def delete_voice(self, voice_id: str) -> bool:
        gc.collect()
        voice_dir = self._voices_dir / voice_id
        if voice_dir.exists():
            try:
                shutil.rmtree(voice_dir, ignore_errors=True)
                self._profiles.pop(voice_id, None)
                logger.info(f"Deleted voice profile: {voice_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete voice {voice_id}: {e}")
                return False
        self._profiles.pop(voice_id, None)
        return True

    def get_voice_count(self) -> int:
        return len(self._profiles)


# Module-level singleton
_service: Optional[VoiceCloneService] = None


def get_voice_clone_service() -> VoiceCloneService:
    global _service
    if _service is None:
        _service = VoiceCloneService()
    return _service
