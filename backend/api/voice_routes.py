"""
Voice API routes for Local AI Voice Studio.
Voice profile upload, listing, management.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from typing import Optional

from backend.services.voice_clone_service import get_voice_clone_service

router = APIRouter(prefix="/api/voices", tags=["voices"])


@router.get("")
async def list_voices():
    """List all voice profiles."""
    service = get_voice_clone_service()
    profiles = service.get_all_profiles()
    return {
        "voices": [p.to_dict() for p in profiles],
        "count": len(profiles),
    }


@router.post("")
async def upload_voice(
    file: UploadFile = File(...),
    name: str = Form(...),
    language: str = Form("en"),
    ref_text: Optional[str] = Form(None),
):
    """
    Upload a voice sample and create a voice profile with VoiceClonePrompt extraction.
    """
    service = get_voice_clone_service()

    try:
        file_data = await file.read()
        profile, analysis = await service.upload_voice(
            file_data=file_data,
            filename=file.filename or "upload.wav",
            name=name,
            language=language,
            ref_text=ref_text,
        )

        return {
            "profile": profile.to_dict(),
            "analysis": analysis.to_dict(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/{voice_id}")
async def get_voice(voice_id: str):
    """Get a voice profile by ID."""
    service = get_voice_clone_service()
    profile = service.get_profile(voice_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    return {"profile": profile.to_dict()}


@router.get("/{voice_id}/sample")
async def get_voice_sample(voice_id: str):
    """Get the audio sample for a voice profile."""
    service = get_voice_clone_service()
    path = service.get_sample_path(voice_id)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="Voice sample not found")

    return FileResponse(
        path=str(path),
        media_type="audio/wav",
        filename=f"voice_{voice_id}_sample.wav",
    )


@router.put("/{voice_id}")
async def rename_voice(voice_id: str, name: str = Form(...)):
    """Rename a voice profile."""
    service = get_voice_clone_service()
    profile = await service.rename_voice(voice_id, name)
    if profile is None:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    return {"profile": profile.to_dict()}


@router.delete("/{voice_id}")
async def delete_voice(voice_id: str):
    """Delete a voice profile."""
    service = get_voice_clone_service()
    success = await service.delete_voice(voice_id)
    if success:
        return {"message": "Voice profile deleted successfully"}
    raise HTTPException(status_code=500, detail="Failed to delete voice profile")
