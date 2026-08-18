"""
System API routes for Local AI Voice Studio.
GET /api/system — hardware info and recommendations.
"""

from fastapi import APIRouter

from backend.services.hardware_detector import get_hardware_detector
from backend.services.model_selector import get_model_selector

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("")
async def get_system_info():
    """
    Get full system hardware profile and model recommendations.
    """
    detector = get_hardware_detector()
    profile = detector.detect()

    selector = get_model_selector()
    recommendations = selector.recommend_all(profile)

    rec_models = {}
    for lang, model in recommendations.items():
        if model:
            rec_models[lang] = {
                "id": model.id,
                "name": model.name,
                "engine": model.engine.value,
                "voice_cloning": model.voice_cloning,
            }
        else:
            rec_models[lang] = None

    vram_free = getattr(profile.gpu, "vram_free_gb", getattr(profile.gpu, "vram_available_gb", 0.0))

    return {
        "cpu": {
            "name": profile.cpu.name,
            "cores_physical": profile.cpu.cores_physical,
            "cores_logical": profile.cpu.cores_logical,
            "architecture": profile.cpu.architecture,
            "usage_percent": getattr(profile.cpu, "usage_percent", 0.0),
        },
        "ram": {
            "total_gb": profile.ram.total_gb,
            "available_gb": profile.ram.available_gb,
            "used_gb": getattr(profile.ram, "used_gb", round(profile.ram.total_gb - profile.ram.available_gb, 1)),
            "used_percent": profile.ram.used_percent,
        },
        "gpu": {
            "name": profile.gpu.name,
            "vendor": profile.gpu.vendor,
            "vram_total_gb": profile.gpu.vram_total_gb,
            "vram_free_gb": vram_free,
            "vram_available_gb": vram_free,
            "vram_used_gb": getattr(profile.gpu, "vram_used_gb", 0.0),
            "vram_used_percent": getattr(profile.gpu, "vram_used_percent", 0.0),
            "gpu_utilization_percent": getattr(profile.gpu, "gpu_utilization_percent", 0.0),
            "temperature_c": getattr(profile.gpu, "temperature_c", 0.0),
            "driver_version": getattr(profile.gpu, "driver_version", "N/A"),
            "detected": profile.gpu.detected,
        },
        "cuda": {
            "available": profile.cuda.available,
            "version": profile.cuda.version,
            "cudnn_version": profile.cuda.cudnn_version,
            "compute_capability": profile.cuda.compute_capability,
            "device_count": getattr(profile.cuda, "device_count", 1 if profile.cuda.available else 0),
        },
        "disk": {
            "total_gb": profile.disk.total_gb,
            "free_gb": profile.disk.free_gb,
            "used_gb": getattr(profile.disk, "used_gb", 0.0),
            "used_percent": getattr(profile.disk, "used_percent", 0.0),
        },
        "python_version": profile.python_version,
        "pytorch_version": profile.pytorch_version,
        "os": {
            "name": profile.os_name,
            "version": profile.os_version,
        },
        "recommended_device": profile.recommended_device,
        "recommended_model_tier": profile.recommended_model_tier,
        "recommended_models": rec_models,
    }
