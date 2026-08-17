"""
Job Manager for Local AI Voice Studio.
Manages background TTS jobs with progress tracking via SSE.
"""

import asyncio
import uuid
import logging
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional, AsyncGenerator

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobProgress:
    """Progress update for a job."""
    job_id: str
    status: str
    progress: float     # 0.0 - 1.0
    stage: str = ""     # Current stage name
    message: str = ""
    result: Optional[dict] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["progress_percent"] = round(self.progress * 100, 1)
        return d


@dataclass
class Job:
    """A background TTS generation job."""
    id: str
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    stage: str = ""
    message: str = ""
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: str = ""
    completed_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status.value,
            "progress": self.progress,
            "progress_percent": round(self.progress * 100, 1),
            "stage": self.stage,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


class JobManager:
    """
    Manages background jobs with progress tracking.
    Supports SSE-based real-time progress updates.
    """

    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._listeners: dict[str, list[asyncio.Queue]] = {}

    def create_job(self) -> Job:
        """Create a new job."""
        job_id = str(uuid.uuid4())[:8]
        job = Job(id=job_id)
        self._jobs[job_id] = job
        self._listeners[job_id] = []
        logger.info(f"Created job: {job_id}")
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        return self._jobs.get(job_id)

    async def update_progress(
        self,
        job_id: str,
        progress: float,
        stage: str = "",
        message: str = "",
    ) -> None:
        """Update job progress and notify listeners."""
        job = self._jobs.get(job_id)
        if job is None:
            return

        job.progress = progress
        job.stage = stage
        job.message = message
        if job.status == JobStatus.PENDING:
            job.status = JobStatus.RUNNING

        # Notify SSE listeners
        update = JobProgress(
            job_id=job_id,
            status=job.status.value,
            progress=progress,
            stage=stage,
            message=message,
        )

        for queue in self._listeners.get(job_id, []):
            await queue.put(update)

    async def complete_job(
        self,
        job_id: str,
        result: dict,
    ) -> None:
        """Mark a job as completed with result data."""
        job = self._jobs.get(job_id)
        if job is None:
            return

        job.status = JobStatus.COMPLETED
        job.progress = 1.0
        job.stage = "Completed"
        job.message = "Generation complete!"
        job.result = result
        job.completed_at = datetime.now(timezone.utc).isoformat()

        update = JobProgress(
            job_id=job_id,
            status=JobStatus.COMPLETED.value,
            progress=1.0,
            stage="Completed",
            message="Generation complete!",
            result=result,
        )

        for queue in self._listeners.get(job_id, []):
            await queue.put(update)
            await queue.put(None)  # Signal stream end

    async def fail_job(self, job_id: str, error: str) -> None:
        """Mark a job as failed."""
        job = self._jobs.get(job_id)
        if job is None:
            return

        job.status = JobStatus.FAILED
        job.error = error
        job.stage = "Failed"
        job.message = error
        job.completed_at = datetime.now(timezone.utc).isoformat()

        update = JobProgress(
            job_id=job_id,
            status=JobStatus.FAILED.value,
            progress=job.progress,
            stage="Failed",
            message=error,
            error=error,
        )

        for queue in self._listeners.get(job_id, []):
            await queue.put(update)
            await queue.put(None)

    def subscribe(self, job_id: str) -> asyncio.Queue:
        """Subscribe to progress updates for a job."""
        queue = asyncio.Queue()
        if job_id not in self._listeners:
            self._listeners[job_id] = []
        self._listeners[job_id].append(queue)
        return queue

    def unsubscribe(self, job_id: str, queue: asyncio.Queue) -> None:
        """Unsubscribe from job updates."""
        if job_id in self._listeners:
            try:
                self._listeners[job_id].remove(queue)
            except ValueError:
                pass

    async def stream_progress(
        self, job_id: str
    ) -> AsyncGenerator[JobProgress, None]:
        """
        Async generator that yields job progress updates.
        Used for SSE streaming.
        """
        queue = self.subscribe(job_id)

        try:
            # Send current state first
            job = self.get_job(job_id)
            if job:
                yield JobProgress(
                    job_id=job_id,
                    status=job.status.value,
                    progress=job.progress,
                    stage=job.stage,
                    message=job.message,
                    result=job.result,
                    error=job.error,
                )

                # If already completed, stop
                if job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                    return

            while True:
                update = await queue.get()
                if update is None:
                    break
                yield update

        finally:
            self.unsubscribe(job_id, queue)

    def get_all_jobs(self) -> list[dict]:
        """Get all jobs."""
        return [job.to_dict() for job in self._jobs.values()]

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        job = self._jobs.get(job_id)
        if job and job.status in (JobStatus.PENDING, JobStatus.RUNNING):
            job.status = JobStatus.CANCELLED
            job.message = "Cancelled by user"
            job.completed_at = datetime.now(timezone.utc).isoformat()

            for queue in self._listeners.get(job_id, []):
                await queue.put(None)

            return True
        return False

    async def delete_job(self, job_id: str) -> bool:
        """Delete a job record."""
        if job_id in self._jobs:
            del self._jobs[job_id]
            self._listeners.pop(job_id, None)
            return True
        return False


# Module-level singleton
_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """Get the global JobManager singleton."""
    global _manager
    if _manager is None:
        _manager = JobManager()
    return _manager
