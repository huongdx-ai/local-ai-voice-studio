"""
Configuration loader for Local AI Voice Studio.
Reads config.yaml and provides typed access to settings.
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


# Project root is two levels up from this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: list[str] = field(default_factory=lambda: [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ])


@dataclass
class TTSConfig:
    default_language: str = "en"
    default_format: str = "wav"
    max_text_length: int = 5000
    default_speed: float = 1.0
    default_volume: float = 1.0


@dataclass
class HardwareConfig:
    auto_detect: bool = True
    force_device: Optional[str] = None


@dataclass
class ModelThresholds:
    large_model_min_vram: int = 8
    medium_model_min_vram: int = 4
    small_model_min_vram: int = 2
    cpu_model_min_ram: int = 8


@dataclass
class ModelsConfig:
    auto_download: bool = True
    auto_select: bool = True
    cache_dir: str = "models"
    thresholds: ModelThresholds = field(default_factory=ModelThresholds)


@dataclass
class AudioConfig:
    sample_rate: int = 22050
    output_dir: str = "outputs"
    supported_formats: list[str] = field(default_factory=lambda: ["wav", "mp3"])


@dataclass
class VoiceValidation:
    min_duration: float = 3.0
    max_duration: float = 300.0
    min_sample_rate: int = 16000


@dataclass
class VoicesConfig:
    storage_dir: str = "voices"
    max_upload_size_mb: int = 50
    supported_formats: list[str] = field(
        default_factory=lambda: [".wav", ".mp3", ".m4a", ".flac"]
    )
    validation: VoiceValidation = field(default_factory=VoiceValidation)


@dataclass
class LoggingConfig:
    level: str = "INFO"
    safe_fields: list[str] = field(default_factory=lambda: [
        "job_id", "timestamp", "model", "language", "duration", "status", "error"
    ])


@dataclass
class AppConfig:
    server: ServerConfig = field(default_factory=ServerConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    models: ModelsConfig = field(default_factory=ModelsConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    voices: VoicesConfig = field(default_factory=VoicesConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


def _dict_to_dataclass(cls, data: dict):
    """Recursively convert a dict to a nested dataclass."""
    if not isinstance(data, dict):
        return data
    field_types = {f.name: f.type for f in cls.__dataclass_fields__.values()}
    kwargs = {}
    for key, value in data.items():
        if key in field_types:
            ft = field_types[key]
            # Check if the field type is itself a dataclass
            if isinstance(ft, type) and hasattr(ft, "__dataclass_fields__") and isinstance(value, dict):
                kwargs[key] = _dict_to_dataclass(ft, value)
            else:
                kwargs[key] = value
    return cls(**kwargs)


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """Load configuration from YAML file, falling back to defaults."""
    path = config_path or CONFIG_PATH
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        config = AppConfig()
        if "server" in raw:
            config.server = _dict_to_dataclass(ServerConfig, raw["server"])
        if "tts" in raw:
            config.tts = _dict_to_dataclass(TTSConfig, raw["tts"])
        if "hardware" in raw:
            config.hardware = _dict_to_dataclass(HardwareConfig, raw["hardware"])
        if "models" in raw:
            models_raw = raw["models"]
            config.models = ModelsConfig(
                auto_download=models_raw.get("auto_download", True),
                auto_select=models_raw.get("auto_select", True),
                cache_dir=models_raw.get("cache_dir", "models"),
                thresholds=_dict_to_dataclass(
                    ModelThresholds,
                    models_raw.get("thresholds", {}),
                ) if "thresholds" in models_raw else ModelThresholds(),
            )
        if "audio" in raw:
            config.audio = _dict_to_dataclass(AudioConfig, raw["audio"])
        if "voices" in raw:
            voices_raw = raw["voices"]
            config.voices = VoicesConfig(
                storage_dir=voices_raw.get("storage_dir", "voices"),
                max_upload_size_mb=voices_raw.get("max_upload_size_mb", 50),
                supported_formats=voices_raw.get(
                    "supported_formats", [".wav", ".mp3", ".m4a", ".flac"]
                ),
                validation=_dict_to_dataclass(
                    VoiceValidation,
                    voices_raw.get("validation", {}),
                ) if "validation" in voices_raw else VoiceValidation(),
            )
        if "logging" in raw:
            config.logging = _dict_to_dataclass(LoggingConfig, raw["logging"])
        return config
    return AppConfig()


# Singleton config instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global configuration singleton."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def get_project_root() -> Path:
    """Get the project root directory."""
    return PROJECT_ROOT
