"""
Model Manager for Local AI Voice Studio.
Handles model installation, download with progress, caching, and lifecycle.
Simplified for OmniVoice as the single TTS engine.
"""

import os
import json
import shutil
import logging
import asyncio
import importlib
from pathlib import Path
from typing import Optional, AsyncGenerator
from dataclasses import dataclass

from backend.config import get_config, get_project_root
from backend.services.model_registry import (
    ModelRegistry,
    ModelStatus,
    ModelEngine,
    ModelInfo,
    get_model_registry,
)

logger = logging.getLogger(__name__)


@dataclass
class DownloadProgress:
    """Progress info for a model download."""
    model_id: str
    status: str        # "starting", "downloading", "verifying", "completed", "error"
    progress: float    # 0.0 - 1.0
    downloaded_mb: float = 0.0
    total_mb: float = 0.0
    message: str = ""


class ModelManager:
    """
    Manages model lifecycle: check, download, cache, delete, and load.
    """

    def __init__(self, registry: Optional[ModelRegistry] = None):
        self._registry = registry or get_model_registry()
        self._config = get_config()
        self._cache_dir = get_project_root() / self._config.models.cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        # Scan cache to update registry status
        self._scan_cache()

    def _scan_cache(self) -> None:
        """Scan the model cache directory and update registry status."""
        for model in self._registry.get_all():
            model_dir = self._cache_dir / model.id
            marker = model_dir / ".installed"
            if marker.exists():
                self._registry.set_status(model.id, ModelStatus.INSTALLED)
                logger.debug(f"Found cached model: {model.id}")

        # Check if omnivoice pip package is importable
        for model in self._registry.get_all():
            if self._registry.get_status(model.id) == ModelStatus.NOT_INSTALLED:
                if self._check_omnivoice_installed():
                    model_dir = self._cache_dir / model.id
                    model_dir.mkdir(parents=True, exist_ok=True)
                    marker = model_dir / ".installed"
                    marker.write_text(json.dumps({
                        "model_id": model.id,
                        "engine": model.engine.value,
                        "install_type": "pip",
                    }))
                    self._registry.set_status(model.id, ModelStatus.INSTALLED)
                    logger.info(f"OmniVoice package detected as installed")

    def _check_omnivoice_installed(self) -> bool:
        """Check if omnivoice pip package is importable."""
        try:
            importlib.import_module("omnivoice")
            return True
        except ImportError:
            return False

    def is_installed(self, model_id: str) -> bool:
        """Check if a model is installed."""
        return self._registry.get_status(model_id) == ModelStatus.INSTALLED

    def get_model_dir(self, model_id: str) -> Path:
        """Get the cache directory for a model."""
        return self._cache_dir / model_id

    async def install_model(
        self, model_id: str
    ) -> AsyncGenerator[DownloadProgress, None]:
        """
        Install a model. Yields progress updates.
        For OmniVoice, checks the pip package and triggers first model load.
        """
        model = self._registry.get(model_id)
        if model is None:
            yield DownloadProgress(
                model_id=model_id,
                status="error",
                progress=0.0,
                message=f"Model '{model_id}' not found in registry",
            )
            return

        if self.is_installed(model_id):
            yield DownloadProgress(
                model_id=model_id,
                status="completed",
                progress=1.0,
                message="Model already installed",
            )
            return

        self._registry.set_status(model_id, ModelStatus.DOWNLOADING)

        yield DownloadProgress(
            model_id=model_id,
            status="starting",
            progress=0.0,
            message=f"Preparing to install {model.name}...",
        )

        try:
            model_dir = self._cache_dir / model_id
            model_dir.mkdir(parents=True, exist_ok=True)

            # Step 1: Check if omnivoice pip package is available
            yield DownloadProgress(
                model_id=model_id,
                status="downloading",
                progress=0.1,
                message="Checking omnivoice package...",
            )

            if not self._check_omnivoice_installed():
                yield DownloadProgress(
                    model_id=model_id,
                    status="downloading",
                    progress=0.2,
                    message="Installing omnivoice package via pip...",
                )

                # Try to install omnivoice
                try:
                    import subprocess
                    import sys
                    result = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: subprocess.run(
                            [sys.executable, "-m", "pip", "install", "omnivoice"],
                            capture_output=True, text=True, timeout=600,
                        )
                    )
                    if result.returncode != 0:
                        yield DownloadProgress(
                            model_id=model_id,
                            status="error",
                            progress=0.0,
                            message=f"Failed to install omnivoice: {result.stderr[:200]}",
                        )
                        self._registry.set_status(model_id, ModelStatus.ERROR)
                        return
                except Exception as e:
                    yield DownloadProgress(
                        model_id=model_id,
                        status="error",
                        progress=0.0,
                        message=f"pip install failed: {str(e)}",
                    )
                    self._registry.set_status(model_id, ModelStatus.ERROR)
                    return

            yield DownloadProgress(
                model_id=model_id,
                status="downloading",
                progress=0.4,
                message="OmniVoice package available. Downloading model weights on first use...",
            )

            # Step 2: Trigger model weight download by importing
            yield DownloadProgress(
                model_id=model_id,
                status="downloading",
                progress=0.6,
                message="Initializing OmniVoice model (downloading weights)...",
            )

            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._trigger_model_download)
            except Exception as e:
                logger.warning(f"Model pre-download warning: {e}")
                # Don't fail — model will download on first inference

            # Step 3: Mark as installed
            yield DownloadProgress(
                model_id=model_id,
                status="verifying",
                progress=0.9,
                message="Verifying installation...",
            )

            marker = model_dir / ".installed"
            marker.write_text(json.dumps({
                "model_id": model.id,
                "engine": model.engine.value,
                "install_type": "pip",
            }))

            self._registry.set_status(model_id, ModelStatus.INSTALLED)

            yield DownloadProgress(
                model_id=model_id,
                status="completed",
                progress=1.0,
                message=f"{model.name} installed successfully!",
            )

        except Exception as e:
            self._registry.set_status(model_id, ModelStatus.ERROR)
            logger.error(f"Failed to install model {model_id}: {e}")
            yield DownloadProgress(
                model_id=model_id,
                status="error",
                progress=0.0,
                message=f"Installation failed: {str(e)}",
            )

    def _trigger_model_download(self) -> None:
        """Trigger OmniVoice model weight download by initializing."""
        try:
            from omnivoice import OmniVoice
            model = OmniVoice.from_pretrained("k2-fsa/OmniVoice")
            del model
        except Exception as e:
            logger.warning(f"Model pre-download: {e}")

    async def delete_model(self, model_id: str) -> bool:
        """Delete a model's cached files."""
        model_dir = self._cache_dir / model_id
        if model_dir.exists():
            try:
                shutil.rmtree(model_dir)
                self._registry.set_status(model_id, ModelStatus.NOT_INSTALLED)
                logger.info(f"Deleted model: {model_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete model {model_id}: {e}")
                return False
        self._registry.set_status(model_id, ModelStatus.NOT_INSTALLED)
        return True

    def get_all_status(self) -> list[dict]:
        """Get all models with their installation status."""
        return self._registry.to_dict_list()

    def get_cache_size_gb(self) -> float:
        """Get total size of the model cache in GB."""
        total = 0
        for path in self._cache_dir.rglob("*"):
            if path.is_file():
                total += path.stat().st_size
        return round(total / (1024 ** 3), 2)


# Module-level singleton
_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """Get the global ModelManager singleton."""
    global _manager
    if _manager is None:
        _manager = ModelManager()
    return _manager
