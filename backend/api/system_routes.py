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
    profile = detector.detect()  # Re-detect for fresh data

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

    return {
        "cpu": {
            "name": profile.cpu.name,
            "cores_physical": profile.cpu.cores_physical,
            "cores_logical": profile.cpu.cores_logical,
            "architecture": profile.cpu.architecture,
        },
        "ram": {
            "total_gb": profile.ram.total_gb,
            "available_gb": profile.ram.available_gb,
            "used_percent": profile.ram.used_percent,
        },
        "gpu": {
            "name": profile.gpu.name,
            "vendor": profile.gpu.vendor,
            "vram_total_gb": profile.gpu.vram_total_gb,
            "vram_available_gb": profile.gpu.vram_available_gb,
            "detected": profile.gpu.detected,
        },
        "cuda": {
            "available": profile.cuda.available,
            "version": profile.cuda.version,
            "cudnn_version": profile.cuda.cudnn_version,
            "compute_capability": profile.cuda.compute_capability,
        },
        "disk": {
            "total_gb": profile.disk.total_gb,
            "free_gb": profile.disk.free_gb,
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
