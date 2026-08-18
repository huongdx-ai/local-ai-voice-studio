"""
Hardware Detector for Local AI Voice Studio.
Accurately detects CPU, RAM, GPU, VRAM (Total, Free, Used), CUDA availability,
and system capabilities using PyTorch CUDA APIs and nvidia-smi.
"""

import os
import sys
import platform
import logging
import subprocess
import re
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
    usage_percent: float = 0.0


@dataclass
class RAMInfo:
    total_gb: float = 0.0
    available_gb: float = 0.0
    used_gb: float = 0.0
    used_percent: float = 0.0


@dataclass
class GPUInfo:
    name: str = "Not detected"
    vendor: str = "Unknown"
    vram_total_gb: float = 0.0
    vram_free_gb: float = 0.0
    vram_available_gb: float = 0.0
    vram_used_gb: float = 0.0
    vram_used_percent: float = 0.0
    gpu_utilization_percent: float = 0.0
    temperature_c: float = 0.0
    driver_version: str = "N/A"
    detected: bool = False


@dataclass
class CUDAInfo:
    available: bool = False
    version: str = "N/A"
    cudnn_version: str = "N/A"
    compute_capability: str = "N/A"
    device_count: int = 0


@dataclass
class DiskInfo:
    total_gb: float = 0.0
    free_gb: float = 0.0
    used_gb: float = 0.0
    used_percent: float = 0.0


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
    """Detects system hardware and generates a detailed HardwareProfile."""

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

        # GPU + CUDA + VRAM
        profile.gpu, profile.cuda, profile.pytorch_version = self._detect_gpu_cuda()

        # Disk
        profile.disk = self._detect_disk()

        # Determine recommended device and model tier
        profile.recommended_device = self._determine_device(profile)
        profile.recommended_model_tier = self._determine_model_tier(profile)

        self._profile = profile
        logger.info(
            f"Hardware detected: device={profile.recommended_device}, "
            f"GPU={profile.gpu.name} (VRAM: {profile.gpu.vram_free_gb:.1f}GB free / {profile.gpu.vram_total_gb:.1f}GB total)"
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
            info.usage_percent = psutil.cpu_percent(interval=None)

            if platform.system() == "Windows":
                try:
                    import winreg
                    key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
                    )
                    info.name = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
                    winreg.CloseKey(key)
                except Exception:
                    info.name = platform.processor() or "Unknown"
            elif platform.system() == "Linux":
                try:
                    with open("/proc/cpuinfo", "r") as f:
                        for line in f:
                            if "model name" in line:
                                info.name = line.split(":")[1].strip()
                                break
                except Exception:
                    info.name = platform.processor() or "Unknown"
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
            info.used_gb = round((mem.total - mem.available) / (1024 ** 3), 1)
            info.used_percent = round(mem.percent, 1)
        except Exception as e:
            logger.warning(f"RAM detection error: {e}")
        return info

    def _detect_gpu_cuda(self) -> tuple[GPUInfo, CUDAInfo, str]:
        """
        Accurately detect GPU, VRAM (Total/Free/Used), and CUDA version.
        Combines PyTorch CUDA APIs with nvidia-smi query.
        """
        gpu_info = GPUInfo()
        cuda_info = CUDAInfo()
        pytorch_version = "Not installed"

        # === 1. PyTorch CUDA Detection ===
        try:
            import torch
            pytorch_version = torch.__version__

            if torch.cuda.is_available():
                cuda_info.available = True
                cuda_info.version = torch.version.cuda or "Unknown"
                cuda_info.device_count = torch.cuda.device_count()

                try:
                    cudnn_ver = torch.backends.cudnn.version()
                    if cudnn_ver:
                        major = cudnn_ver // 1000
                        minor = (cudnn_ver % 1000) // 100
                        patch = cudnn_ver % 100
                        cuda_info.cudnn_version = f"{major}.{minor}.{patch}"
                except Exception:
                    pass

                gpu_info.detected = True
                gpu_info.name = torch.cuda.get_device_name(0)
                gpu_info.vendor = "NVIDIA"

                cap = torch.cuda.get_device_capability(0)
                cuda_info.compute_capability = f"{cap[0]}.{cap[1]}"

                # VRAM from torch.cuda
                props = torch.cuda.get_device_properties(0)
                total_mem_bytes = getattr(props, "total_memory", getattr(props, "total_mem", 0))
                gpu_info.vram_total_gb = round(total_mem_bytes / (1024 ** 3), 1)

                try:
                    free_bytes, total_bytes = torch.cuda.mem_get_info(0)
                    gpu_info.vram_free_gb = round(free_bytes / (1024 ** 3), 1)
                    used_bytes = total_bytes - free_bytes
                    gpu_info.vram_used_gb = round(used_bytes / (1024 ** 3), 1)
                    if total_bytes > 0:
                        gpu_info.vram_used_percent = round((used_bytes / total_bytes) * 100, 1)
                except Exception:
                    gpu_info.vram_free_gb = gpu_info.vram_total_gb
                    gpu_info.vram_used_gb = 0.0
                    gpu_info.vram_used_percent = 0.0

        except ImportError:
            logger.info("PyTorch not installed")
        except Exception as e:
            logger.warning(f"PyTorch GPU detection error: {e}")

        # === 2. Query nvidia-smi for real-time stats & fallback ===
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total,memory.free,memory.used,driver_version,utilization.gpu,temperature.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                line = result.stdout.strip().splitlines()[0]
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 5:
                    gpu_info.detected = True
                    gpu_info.vendor = "NVIDIA"
                    if not gpu_info.name or gpu_info.name == "Not detected":
                        gpu_info.name = parts[0]
                    
                    total_mb = float(parts[1])
                    free_mb = float(parts[2])
                    used_mb = float(parts[3])

                    gpu_info.vram_total_gb = round(total_mb / 1024, 1)
                    gpu_info.vram_free_gb = round(free_mb / 1024, 1)
                    gpu_info.vram_available_gb = gpu_info.vram_free_gb
                    gpu_info.vram_used_gb = round(used_mb / 1024, 1)
                    if total_mb > 0:
                        gpu_info.vram_used_percent = round((used_mb / total_mb) * 100, 1)

                    gpu_info.driver_version = parts[4]

                    if len(parts) >= 6 and parts[5].replace('.', '', 1).isdigit():
                        gpu_info.gpu_utilization_percent = float(parts[5])
                    if len(parts) >= 7 and parts[6].replace('.', '', 1).isdigit():
                        gpu_info.temperature_c = float(parts[6])

            # Also check CUDA driver version from header if not already detected
            if not cuda_info.available or cuda_info.version == "N/A":
                result2 = subprocess.run(
                    ["nvidia-smi"], capture_output=True, text=True, timeout=5,
                )
                if result2.returncode == 0:
                    match = re.search(r"CUDA Version:\s*([\d.]+)", result2.stdout)
                    if match:
                        cuda_info.version = match.group(1)

        except (FileNotFoundError, Exception) as e:
            logger.debug(f"nvidia-smi query skipped or failed: {e}")

        return gpu_info, cuda_info, pytorch_version

    def _detect_disk(self) -> DiskInfo:
        """Detect disk space on the project drive."""
        info = DiskInfo()
        try:
            project_path = os.path.abspath(os.path.dirname(__file__))
            usage = psutil.disk_usage(project_path)
            info.total_gb = round(usage.total / (1024 ** 3), 1)
            info.free_gb = round(usage.free / (1024 ** 3), 1)
            info.used_gb = round(usage.used / (1024 ** 3), 1)
            info.used_percent = round(usage.percent, 1)
        except Exception as e:
            logger.warning(f"Disk detection error: {e}")
        return info

    def _determine_device(self, profile: HardwareProfile) -> str:
        """Determine recommended device (cuda vs cpu)."""
        if self._force_device:
            return self._force_device

        if profile.cuda.available and profile.gpu.detected:
            if profile.gpu.vram_total_gb >= 2.0:
                return "cuda"

        return "cpu"

    def _determine_model_tier(self, profile: HardwareProfile) -> str:
        """Determine model tier."""
        if profile.recommended_device == "cuda":
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
    """Get or create global HardwareDetector."""
    global _detector
    if _detector is None:
        _detector = HardwareDetector(force_device=force_device)
    return _detector
