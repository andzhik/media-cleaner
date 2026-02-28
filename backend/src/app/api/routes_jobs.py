from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
from ..core.jobs.store import job_store
from ..core.jobs.events import event_manager
from ..core.models import JobStatus
import asyncio
import json

router = APIRouter()

@router.get("/jobs/events")
async def jobs_list_events():
    queue = await event_manager.subscribe_global()

    async def event_generator():
        try:
            # Send current active jobs immediately
            active_jobs = job_store.list_active_jobs()
            payload = json.dumps([j.model_dump() for j in active_jobs])
            yield {"event": "jobs_list", "data": payload}

            while True:
                jobs = await queue.get()
                payload = json.dumps([j.model_dump() for j in jobs])
                yield {"event": "jobs_list", "data": payload}
        except asyncio.CancelledError:
            pass
        finally:
            await event_manager.unsubscribe_global(queue)

    return EventSourceResponse(event_generator())

@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/jobs/{job_id}/events")
async def job_events(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    queue = await event_manager.subscribe(job_id)

    async def event_generator():
        try:
            # Send initial status
            yield {"event": "status", "data": job.model_dump_json()}

            while True:
                # Wait for update
                update = await queue.get()
                yield {"event": "status", "data": update.model_dump_json()}

                # Close if finished
                if update.status in ["completed", "failed"]:
                     break
        except asyncio.CancelledError:
            await event_manager.unsubscribe(job_id, queue)
        finally:
             await event_manager.unsubscribe(job_id, queue)

    return EventSourceResponse(event_generator())
