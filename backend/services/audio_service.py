"""
Audio Service for Local AI Voice Studio.
Handles post-processing (speed, pitch, volume), format conversion, and output management.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

from backend.config import get_config, get_project_root

logger = logging.getLogger(__name__)


@dataclass
class AudioOutput:
    """Metadata for a generated audio output."""
    id: str
    language: str
    model: str
    voice_profile: str
    text: str
    duration_seconds: float
    format: str
    wav_path: str
    mp3_path: str
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)


class AudioService:
    """
    Manages audio post-processing, format conversion, and output storage.
    """

    def __init__(self):
        self._config = get_config()
        self._output_dir = get_project_root() / self._config.audio.output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._outputs: dict[str, AudioOutput] = {}
        self._load_existing_outputs()

    def _load_existing_outputs(self) -> None:
        """Load existing output metadata from disk."""
        for out_dir in self._output_dir.iterdir():
            if out_dir.is_dir():
                meta_path = out_dir / "metadata.json"
                if meta_path.exists():
                    try:
                        with open(meta_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        output = AudioOutput(**data)
                        self._outputs[output.id] = output
                    except Exception as e:
                        logger.warning(f"Failed to load output from {out_dir}: {e}")

    def apply_post_processing(
        self,
        audio_path: Path,
        output_path: Path,
        speed: float = 1.0,
        pitch: float = 0.0,
        volume: float = 1.0,
    ) -> Path:
        """
        Apply post-processing effects to an audio file.
        Only applies effects that the model didn't handle natively.
        """
        try:
            import librosa
            import soundfile as sf
            import numpy as np

            # Load audio
            audio, sr = librosa.load(str(audio_path), sr=None, mono=True)

            # Speed adjustment (time stretch without pitch change)
            if speed != 1.0 and 0.5 <= speed <= 2.0:
                audio = librosa.effects.time_stretch(audio, rate=speed)

            # Pitch adjustment (in semitones)
            if pitch != 0.0 and -12 <= pitch <= 12:
                audio = librosa.effects.pitch_shift(audio, sr=sr, n_steps=pitch)

            # Volume adjustment
            if volume != 1.0 and 0.0 <= volume <= 1.0:
                audio = audio * volume

            # Prevent clipping
            max_val = np.max(np.abs(audio))
            if max_val > 0.99:
                audio = audio * (0.99 / max_val)

            # Save
            sf.write(str(output_path), audio, sr)
            return output_path

        except Exception as e:
            logger.error(f"Post-processing failed: {e}")
            # Fallback: copy original
            import shutil
            shutil.copy2(str(audio_path), str(output_path))
            return output_path

    def convert_to_mp3(self, wav_path: Path, mp3_path: Path) -> Path:
        """Convert WAV to MP3."""
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_wav(str(wav_path))
            audio.export(str(mp3_path), format="mp3", bitrate="192k")
            return mp3_path

        except Exception as e:
            logger.error(f"MP3 conversion failed: {e}")
            raise RuntimeError(f"Failed to convert to MP3: {e}")

    def save_output(
        self,
        raw_audio_path: Path,
        language: str,
        model: str,
        text: str,
        voice_profile: str = "default",
        speed: float = 1.0,
        pitch: float = 0.0,
        volume: float = 1.0,
        output_format: str = "wav",
    ) -> AudioOutput:
        """
        Process and save a generation output.
        Creates output directory with WAV, MP3, and metadata.
        """
        # Create output directory with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        output_id = timestamp
        out_dir = self._output_dir / output_id

        # Handle duplicate timestamps
        counter = 1
        while out_dir.exists():
            output_id = f"{timestamp}_{counter}"
            out_dir = self._output_dir / output_id
            counter += 1

        out_dir.mkdir(parents=True, exist_ok=True)

        wav_path = out_dir / "audio.wav"
        mp3_path = out_dir / "audio.mp3"

        # Apply post-processing
        needs_processing = speed != 1.0 or pitch != 0.0 or volume != 1.0
        if needs_processing:
            self.apply_post_processing(
                raw_audio_path, wav_path,
                speed=speed, pitch=pitch, volume=volume,
            )
        else:
            import shutil
            shutil.copy2(str(raw_audio_path), str(wav_path))

        # Get duration from processed WAV
        duration = 0.0
        try:
            import librosa
            audio, sr = librosa.load(str(wav_path), sr=None)
            duration = len(audio) / sr
        except Exception:
            pass

        # Convert to MP3
        try:
            self.convert_to_mp3(wav_path, mp3_path)
        except Exception as e:
            logger.warning(f"MP3 conversion failed, WAV only: {e}")
            mp3_path = wav_path  # Fallback

        # Create metadata
        output = AudioOutput(
            id=output_id,
            language=language,
            model=model,
            voice_profile=voice_profile,
            text=text[:500],  # Truncate for storage
            duration_seconds=round(duration, 2),
            format=output_format,
            wav_path=str(wav_path),
            mp3_path=str(mp3_path),
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # Save metadata
        meta_path = out_dir / "metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(output.to_dict(), f, indent=2, ensure_ascii=False)

        self._outputs[output.id] = output

        logger.info(
            f"Output saved: id={output_id}, duration={duration:.1f}s"
        )

        # Clean up temp raw audio
        try:
            if raw_audio_path.exists() and raw_audio_path != wav_path:
                raw_audio_path.unlink()
        except Exception:
            pass

        return output

    def get_all_outputs(self) -> list[AudioOutput]:
        """Get all outputs, sorted by date descending."""
        outputs = list(self._outputs.values())
        outputs.sort(key=lambda o: o.created_at, reverse=True)
        return outputs

    def get_output(self, output_id: str) -> Optional[AudioOutput]:
        """Get output by ID."""
        return self._outputs.get(output_id)

    def get_audio_path(self, output_id: str, format: str = "wav") -> Optional[Path]:
        """Get the path to an audio file."""
        output = self._outputs.get(output_id)
        if output is None:
            return None

        if format == "mp3":
            path = Path(output.mp3_path)
        else:
            path = Path(output.wav_path)

        return path if path.exists() else None

    async def delete_output(self, output_id: str) -> bool:
        """Delete an output and its files."""
        output = self._outputs.get(output_id)
        if output is None:
            return False

        import shutil
        out_dir = self._output_dir / output_id
        if out_dir.exists():
            try:
                shutil.rmtree(out_dir)
            except Exception as e:
                logger.error(f"Failed to delete output {output_id}: {e}")
                return False

        self._outputs.pop(output_id, None)
        return True

    def get_total_duration(self) -> float:
        """Get total duration of all generated audio in seconds."""
        return sum(o.duration_seconds for o in self._outputs.values())

    def get_output_count(self) -> int:
        """Get total number of generated outputs."""
        return len(self._outputs)


# Module-level singleton
_service: Optional[AudioService] = None


def get_audio_service() -> AudioService:
    """Get the global AudioService singleton."""
    global _service
    if _service is None:
        _service = AudioService()
    return _service
