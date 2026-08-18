"""
History API routes for Local AI Voice Studio.
Generation history listing and management.
"""

from fastapi import APIRouter, HTTPException

from backend.services.audio_service import get_audio_service
from backend.services.voice_clone_service import get_voice_clone_service

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("")
async def list_history():
    """List all generation history, sorted by date descending."""
    service = get_audio_service()
    outputs = service.get_all_outputs()
    return {
        "history": [o.to_dict() for o in outputs],
        "count": len(outputs),
        "total_duration_seconds": service.get_total_duration(),
    }


@router.get("/stats")
async def get_stats():
    """Get generation statistics for the dashboard."""
    audio_service = get_audio_service()
    voice_service = get_voice_clone_service()

    total_duration = audio_service.get_total_duration()
    hours = int(total_duration // 3600)
    minutes = int((total_duration % 3600) // 60)

    return {
        "generated_count": audio_service.get_output_count(),
        "total_duration_seconds": total_duration,
        "total_duration_formatted": f"{hours}h {minutes}m",
        "voice_profiles_count": voice_service.get_voice_count(),
    }


@router.delete("")
async def clear_all_history():
    """Delete all generation history and audio files."""
    service = get_audio_service()
    count = await service.delete_all_outputs()
    return {"message": f"Deleted {count} history entries", "count": count}


@router.delete("/{output_id}")
async def delete_history_entry(output_id: str):
    """Delete a history entry and its audio files."""
    service = get_audio_service()
    success = await service.delete_output(output_id)
    if success:
        return {"message": "History entry deleted"}
    raise HTTPException(status_code=404, detail="History entry not found")
