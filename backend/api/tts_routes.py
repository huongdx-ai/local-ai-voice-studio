"""
TTS API routes for Local AI Voice Studio.
Text-to-speech generation with background jobs and SSE progress.
"""

import json
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from fastapi.responses import StreamingResponse

from backend.services.tts_service import get_tts_service
from backend.services.tts_provider import TTSRequest
from backend.services.audio_service import get_audio_service
from backend.services.voice_clone_service import get_voice_clone_service
from backend.services.job_manager import get_job_manager
from pathlib import Path

router = APIRouter(prefix="/api/tts", tags=["tts"])


class TTSGenerateRequest(BaseModel):
    """Request body for TTS generation."""
    text: str = Field(..., min_length=1, max_length=5000)
    language: str = Field(default="en", pattern="^(en|vi|ja)$")
    voice_id: Optional[str] = None
    engine_id: Optional[str] = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-12.0, le=12.0)
    volume: float = Field(default=1.0, ge=0.0, le=1.0)
    output_format: str = Field(default="wav", pattern="^(wav|mp3)$")


@router.post("")
async def generate_speech(request: TTSGenerateRequest):
    """
    Start a TTS generation job.
    Returns a job ID that can be used to track progress via SSE.
    """
    job_manager = get_job_manager()
    job = job_manager.create_job()

    # Start generation in background
    asyncio.create_task(
        _run_generation(job.id, request)
    )

    return {
        "job_id": job.id,
        "status": "pending",
        "message": "Generation started. Use GET /api/tts/{job_id}/progress for SSE updates.",
    }


async def _run_generation(job_id: str, request: TTSGenerateRequest):
    """Background task for TTS generation."""
    job_manager = get_job_manager()
    tts_service = get_tts_service()
    audio_service = get_audio_service()
    voice_service = get_voice_clone_service()

    try:
        # Stage 1: Validate input
        await job_manager.update_progress(
            job_id, 0.05, "Preparing", "Validating input..."
        )
        await asyncio.sleep(0.2)

        # Stage 2: Determine voice profile
        voice_profile_path = None
        voice_name = "default"
        if request.voice_id:
            sample_path = voice_service.get_sample_path(request.voice_id)
            if sample_path:
                voice_profile_path = sample_path
                profile = voice_service.get_profile(request.voice_id)
                voice_name = profile.name if profile else request.voice_id

        await job_manager.update_progress(
            job_id, 0.10, "Loading model", "Selecting and loading TTS model..."
        )

        # Stage 3: Generate speech
        await job_manager.update_progress(
            job_id, 0.30, "Generating speech", "Synthesizing audio..."
        )

        tts_request = TTSRequest(
            text=request.text,
            language=request.language,
            speed=request.speed if request.pitch == 0.0 else 1.0,  # speed handled in post-processing if pitch also changes
            voice_profile_path=voice_profile_path,
            output_format=request.output_format,
        )

        result = await tts_service.generate(
            tts_request,
            engine_id=request.engine_id,
        )

        if not result.success:
            await job_manager.fail_job(job_id, result.error)
            return

        await job_manager.update_progress(
            job_id, 0.70, "Processing audio", "Applying post-processing..."
        )

        # Stage 4: Post-process and save
        output = audio_service.save_output(
            raw_audio_path=result.audio_path,
            language=request.language,
            model=result.model_used,
            text=request.text,
            voice_profile=voice_name,
            speed=request.speed,
            pitch=request.pitch,
            volume=request.volume,
            output_format=request.output_format,
        )

        await job_manager.update_progress(
            job_id, 0.90, "Converting", "Finalizing output..."
        )

        await asyncio.sleep(0.2)

        # Complete
        await job_manager.complete_job(job_id, {
            "output_id": output.id,
            "duration_seconds": output.duration_seconds,
            "wav_url": f"/api/audio/{output.id}?format=wav",
            "mp3_url": f"/api/audio/{output.id}?format=mp3",
            "download_wav_url": f"/api/audio/{output.id}/download?format=wav",
            "download_mp3_url": f"/api/audio/{output.id}/download?format=mp3",
            "model": output.model,
            "language": output.language,
        })

    except Exception as e:
        await job_manager.fail_job(job_id, str(e))


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    """Get the current status of a TTS job."""
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@router.get("/{job_id}/progress")
async def stream_job_progress(job_id: str):
    """
    SSE endpoint for real-time job progress updates.
    """
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_stream():
        async for progress in job_manager.stream_progress(job_id):
            data = json.dumps(progress.to_dict())
            yield f"data: {data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    """Cancel or delete a TTS job."""
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    success = await job_manager.cancel_job(job_id)
    if not success:
        await job_manager.delete_job(job_id)

    return {"message": "Job cancelled/deleted"}
