"""
Model API routes for Local AI Voice Studio.
Model listing, download, and management.
"""

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.services.model_manager import get_model_manager
from backend.services.model_registry import get_model_registry

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
async def list_models():
    """List all available models with their status."""
    manager = get_model_manager()
    return {"models": manager.get_all_status()}


@router.get("/{model_id}")
async def get_model(model_id: str):
    """Get details for a specific model."""
    registry = get_model_registry()
    model = registry.get(model_id)
    if model is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

    d = model.to_dict()
    d["status"] = registry.get_status(model_id).value
    d["is_active"] = model.id == registry.get_active_model_id()
    return d


@router.post("/{model_id}/download")
async def download_model(model_id: str):
    """
    Download/install a model. Returns SSE stream with progress.
    """
    manager = get_model_manager()
    registry = get_model_registry()

    model = registry.get(model_id)
    if model is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

    async def event_stream():
        async for progress in manager.install_model(model_id):
            data = json.dumps({
                "model_id": progress.model_id,
                "status": progress.status,
                "progress": progress.progress,
                "progress_percent": round(progress.progress * 100, 1),
                "downloaded_mb": progress.downloaded_mb,
                "total_mb": progress.total_mb,
                "message": progress.message,
            })
            yield f"data: {data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.delete("/{model_id}")
async def delete_model(model_id: str):
    """Delete a model's cached files."""
    manager = get_model_manager()
    registry = get_model_registry()

    model = registry.get(model_id)
    if model is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

    success = await manager.delete_model(model_id)
    if success:
        return {"message": f"Model '{model_id}' deleted successfully"}
    raise HTTPException(status_code=500, detail="Failed to delete model")


@router.post("/{model_id}/activate")
async def activate_model(model_id: str):
    """Set a model as the active model."""
    registry = get_model_registry()

    model = registry.get(model_id)
    if model is None:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")

    try:
        registry.set_active_model(model_id)
        return {"message": f"Model '{model_id}' activated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
