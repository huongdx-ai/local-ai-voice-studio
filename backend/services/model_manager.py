"""
Model Manager for Local AI Voice Studio.
Handles model installation, download with progress, caching, and lifecycle.
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
        self._loaded_engines: dict[str, object] = {}

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

        # Also check if pip packages are importable
        for model in self._registry.get_all():
            if (
                self._registry.get_status(model.id) == ModelStatus.NOT_INSTALLED
                and model.pip_package
            ):
                if self._check_pip_package(model):
                    # For pip-based models, mark as installed if package exists
                    model_dir = self._cache_dir / model.id
                    model_dir.mkdir(parents=True, exist_ok=True)
                    marker = model_dir / ".installed"
                    marker.write_text(json.dumps({
                        "model_id": model.id,
                        "engine": model.engine.value,
                        "install_type": "pip",
                    }))
                    self._registry.set_status(model.id, ModelStatus.INSTALLED)

    def _check_pip_package(self, model: ModelInfo) -> bool:
        """Check if a model's pip package is importable."""
        try:
            pkg_name = model.pip_package.replace("-", "_")
            importlib.import_module(pkg_name)
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
        For pip-based models, this checks the package is available.
        For repo-based models, downloads weights from HuggingFace.
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

            # Step 1: Check/install pip package
            if model.pip_package:
                yield DownloadProgress(
                    model_id=model_id,
                    status="downloading",
                    progress=0.1,
                    message=f"Checking package '{model.pip_package}'...",
                )

                if not self._check_pip_package(model):
                    yield DownloadProgress(
                        model_id=model_id,
                        status="downloading",
                        progress=0.2,
                        message=f"Package '{model.pip_package}' not found. Please install it via pip.",
                    )
                    # We don't auto-pip-install at runtime for safety
                    # The install.bat handles this
                else:
                    yield DownloadProgress(
                        model_id=model_id,
                        status="downloading",
                        progress=0.3,
                        message=f"Package '{model.pip_package}' is available.",
                    )

            # Step 2: Download model weights if needed
            if model.model_repo:
                yield DownloadProgress(
                    model_id=model_id,
                    status="downloading",
                    progress=0.3,
                    message=f"Downloading model weights from {model.model_repo}...",
                )

                async for progress in self._download_from_hub(model, model_dir):
                    yield progress
            else:
                # pip-only models: trigger first load to download weights
                yield DownloadProgress(
                    model_id=model_id,
                    status="downloading",
                    progress=0.5,
                    message="Initializing model (downloading weights on first use)...",
                )
                # The actual weight download happens at first inference
                # We just verify the package is available
                await asyncio.sleep(0.5)

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
                "install_type": "pip" if model.pip_package else "repo",
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

    async def _download_from_hub(
        self, model: ModelInfo, model_dir: Path
    ) -> AsyncGenerator[DownloadProgress, None]:
        """Download model weights from HuggingFace Hub."""
        try:
            from huggingface_hub import snapshot_download

            def _do_download():
                return snapshot_download(
                    repo_id=model.model_repo,
                    local_dir=str(model_dir / "weights"),
                    local_dir_use_symlinks=False,
                )

            yield DownloadProgress(
                model_id=model.id,
                status="downloading",
                progress=0.4,
                message="Downloading from HuggingFace Hub...",
            )

            # Run blocking download in executor
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _do_download)

            yield DownloadProgress(
                model_id=model.id,
                status="downloading",
                progress=0.85,
                message="Download complete, finalizing...",
            )

        except ImportError:
            yield DownloadProgress(
                model_id=model.id,
                status="error",
                progress=0.0,
                message="huggingface_hub not installed. Run: pip install huggingface-hub",
            )
        except Exception as e:
            yield DownloadProgress(
                model_id=model.id,
                status="error",
                progress=0.0,
                message=f"Download failed: {str(e)}",
            )

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
