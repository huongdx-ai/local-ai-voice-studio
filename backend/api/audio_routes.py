"""
Audio API routes for Local AI Voice Studio.
Audio playback and download endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Optional

from backend.services.audio_service import get_audio_service

router = APIRouter(prefix="/api/audio", tags=["audio"])


@router.get("/{output_id}")
async def get_audio(
    output_id: str,
    format: str = Query(default="wav", regex="^(wav|mp3)$"),
):
    """Stream an audio file for playback."""
    service = get_audio_service()
    path = service.get_audio_path(output_id, format=format)

    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    media_type = "audio/wav" if format == "wav" else "audio/mpeg"

    return FileResponse(
        path=str(path),
        media_type=media_type,
    )


@router.get("/{output_id}/download")
async def download_audio(
    output_id: str,
    format: str = Query(default="wav", regex="^(wav|mp3)$"),
):
    """Download an audio file."""
    service = get_audio_service()
    output = service.get_output(output_id)
    if output is None:
        raise HTTPException(status_code=404, detail="Audio not found")

    path = service.get_audio_path(output_id, format=format)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    media_type = "audio/wav" if format == "wav" else "audio/mpeg"
    ext = "wav" if format == "wav" else "mp3"

    return FileResponse(
        path=str(path),
        media_type=media_type,
        filename=f"voice_{output_id}.{ext}",
        headers={"Content-Disposition": f'attachment; filename="voice_{output_id}.{ext}"'},
    )


@router.get("/{output_id}/info")
async def get_audio_info(output_id: str):
    """Get metadata for an audio output."""
    service = get_audio_service()
    output = service.get_output(output_id)
    if output is None:
        raise HTTPException(status_code=404, detail="Audio not found")
    return output.to_dict()
