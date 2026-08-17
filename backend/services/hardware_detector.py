"""
Hardware Detector for Local AI Voice Studio.
Detects CPU, RAM, GPU, VRAM, CUDA availability, and system capabilities.
Generates a HardwareProfile for model selection decisions.
"""

import os
import sys
import platform
import logging
from dataclasses import dataclass, asdict
from typing import Optional

import psutil

logger = logging.getLogger(__name__)


@dataclass
class CPUInfo:
    name: str = "Unknown"
    cores_physical: int = 0
    cores_logical: int = 0
    architecture: str = "Unknown"


@dataclass
class RAMInfo:
    total_gb: float = 0.0
    available_gb: float = 0.0
    used_percent: float = 0.0


@dataclass
class GPUInfo:
    name: str = "Not detected"
    vendor: str = "Unknown"
    vram_total_gb: float = 0.0
    vram_available_gb: float = 0.0
    detected: bool = False


@dataclass
class CUDAInfo:
    available: bool = False
    version: str = "N/A"
    cudnn_version: str = "N/A"
    compute_capability: str = "N/A"


@dataclass
class DiskInfo:
    total_gb: float = 0.0
    free_gb: float = 0.0


@dataclass
class HardwareProfile:
    os_name: str = "Unknown"
    os_version: str = ""
    cpu: CPUInfo = None
    ram: RAMInfo = None
    gpu: GPUInfo = None
    cuda: CUDAInfo = None
    disk: DiskInfo = None
    python_version: str = ""
    pytorch_version: str = "Not installed"
    recommended_device: str = "cpu"
    recommended_model_tier: str = "cpu_lightweight"

    def __post_init__(self):
        if self.cpu is None:
            self.cpu = CPUInfo()
        if self.ram is None:
            self.ram = RAMInfo()
        if self.gpu is None:
            self.gpu = GPUInfo()
        if self.cuda is None:
            self.cuda = CUDAInfo()
        if self.disk is None:
            self.disk = DiskInfo()

    def to_dict(self) -> dict:
        return asdict(self)


class HardwareDetector:
    """Detects system hardware and generates a HardwareProfile."""

    def __init__(self, force_device: Optional[str] = None):
        self._force_device = force_device
        self._profile: Optional[HardwareProfile] = None

    def detect(self) -> HardwareProfile:
        """Run full hardware detection and return a HardwareProfile."""
        profile = HardwareProfile()

        # OS
        profile.os_name = platform.system()
        profile.os_version = platform.version()

        # Python
        profile.python_version = sys.version.split()[0]

        # CPU
        profile.cpu = self._detect_cpu()

        # RAM
        profile.ram = self._detect_ram()

        # GPU + CUDA
        profile.gpu, profile.cuda, profile.pytorch_version = self._detect_gpu_cuda()

        # Disk
        profile.disk = self._detect_disk()

        # Determine recommended device and model tier
        profile.recommended_device = self._determine_device(profile)
        profile.recommended_model_tier = self._determine_model_tier(profile)

        self._profile = profile
        logger.info(
            f"Hardware detected: device={profile.recommended_device}, "
            f"tier={profile.recommended_model_tier}"
        )
        return profile

    def get_profile(self) -> HardwareProfile:
        """Get the cached profile, or detect if not yet done."""
        if self._profile is None:
            return self.detect()
        return self._profile

    def _detect_cpu(self) -> CPUInfo:
        """Detect CPU information."""
        info = CPUInfo()
        try:
            info.cores_physical = psutil.cpu_count(logical=False) or 0
            info.cores_logical = psutil.cpu_count(logical=True) or 0
            info.architecture = platform.machine()

            # Try to get CPU name
            if platform.system() == "Windows":
                info.name = platform.processor() or "Unknown"
                # On Windows, platform.processor() often returns a generic string
                # Try WMI or registry for better name
                try:
                    import winreg
                    key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
                    )
                    info.name = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
                    winreg.CloseKey(key)
                except Exception:
                    pass
            else:
                info.name = platform.processor() or "Unknown"
        except Exception as e:
            logger.warning(f"CPU detection error: {e}")
        return info

    def _detect_ram(self) -> RAMInfo:
        """Detect RAM information."""
        info = RAMInfo()
        try:
            mem = psutil.virtual_memory()
            info.total_gb = round(mem.total / (1024 ** 3), 1)
            info.available_gb = round(mem.available / (1024 ** 3), 1)
            info.used_percent = mem.percent
        except Exception as e:
            logger.warning(f"RAM detection error: {e}")
        return info

    def _detect_gpu_cuda(self) -> tuple[GPUInfo, CUDAInfo, str]:
        """Detect GPU, CUDA, and PyTorch information."""
        gpu_info = GPUInfo()
        cuda_info = CUDAInfo()
        pytorch_version = "Not installed"

        try:
            import torch
            pytorch_version = torch.__version__

            if torch.cuda.is_available():
                cuda_info.available = True
                cuda_info.version = torch.version.cuda or "Unknown"

                try:
                    cuda_info.cudnn_version = str(torch.backends.cudnn.version())
                except Exception:
                    pass

                # GPU info from CUDA
                gpu_info.detected = True
                gpu_info.name = torch.cuda.get_device_name(0)
                gpu_info.vendor = "NVIDIA"

                # Compute capability
                cap = torch.cuda.get_device_capability(0)
                cuda_info.compute_capability = f"{cap[0]}.{cap[1]}"

                # VRAM
                total_vram = torch.cuda.get_device_properties(0).total_mem
                gpu_info.vram_total_gb = round(total_vram / (1024 ** 3), 1)

                try:
                    free_vram = torch.cuda.mem_get_info(0)[0]
                    gpu_info.vram_available_gb = round(free_vram / (1024 ** 3), 1)
                except Exception:
                    gpu_info.vram_available_gb = gpu_info.vram_total_gb

        except ImportError:
            logger.warning("PyTorch not installed — GPU detection unavailable")
        except Exception as e:
            logger.warning(f"GPU/CUDA detection error: {e}")

        # Fallback: try GPUtil for additional GPU info
        if not gpu_info.detected:
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_info.detected = True
                    gpu_info.name = gpu.name
                    gpu_info.vendor = "NVIDIA" if "NVIDIA" in gpu.name.upper() else "Unknown"
                    gpu_info.vram_total_gb = round(gpu.memoryTotal / 1024, 1)
                    gpu_info.vram_available_gb = round(gpu.memoryFree / 1024, 1)
            except Exception:
                pass

        return gpu_info, cuda_info, pytorch_version

    def _detect_disk(self) -> DiskInfo:
        """Detect disk space on the project drive."""
        info = DiskInfo()
        try:
            # Get disk for the current working directory
            usage = psutil.disk_usage(os.path.abspath(os.sep))
            info.total_gb = round(usage.total / (1024 ** 3), 1)
            info.free_gb = round(usage.free / (1024 ** 3), 1)
        except Exception as e:
            logger.warning(f"Disk detection error: {e}")
        return info

    def _determine_device(self, profile: HardwareProfile) -> str:
        """Determine the recommended compute device."""
        if self._force_device:
            return self._force_device

        if profile.cuda.available and profile.gpu.detected:
            # Only recommend CUDA if we have meaningful VRAM
            if profile.gpu.vram_total_gb >= 2.0:
                return "cuda"

        return "cpu"

    def _determine_model_tier(self, profile: HardwareProfile) -> str:
        """Determine the recommended model tier based on hardware."""
        device = profile.recommended_device

        if device == "cuda":
            vram = profile.gpu.vram_total_gb
            if vram >= 8:
                return "gpu_large"
            elif vram >= 4:
                return "gpu_medium"
            else:
                return "gpu_small"
        else:
            ram = profile.ram.total_gb
            if ram >= 16:
                return "cpu_standard"
            else:
                return "cpu_lightweight"


# Module-level singleton
_detector: Optional[HardwareDetector] = None


def get_hardware_detector(force_device: Optional[str] = None) -> HardwareDetector:
    """Get or create the global HardwareDetector."""
    global _detector
    if _detector is None:
        _detector = HardwareDetector(force_device=force_device)
    return _detector
