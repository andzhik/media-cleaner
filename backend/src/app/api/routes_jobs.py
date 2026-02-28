from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
from ..core.jobs.store import job_store
from ..core.jobs.events import event_manager
from ..core.models import JobStatus
import asyncio
import json

router = APIRouter()

@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/jobs")
async def stream_jobs():
    async def event_generator():
        try:
            while True:
                jobs = job_store.list_jobs()
                active_jobs = [j.model_dump(mode='json') for j in jobs if j.status in ["pending", "processing"]]
                yield {"event": "jobs", "data": json.dumps(active_jobs)}
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
            
    return EventSourceResponse(event_generator())

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
            # clean up
        finally:
             await event_manager.unsubscribe(job_id, queue)

    return EventSourceResponse(event_generator())
