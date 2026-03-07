from fastapi import APIRouter
from ..core.models import ProcessRequest
from ..core.jobs.queue import job_queue
from ..core.jobs.store import job_store
from ..core.jobs.events import event_manager

router = APIRouter()

@router.post("/process")
async def start_process(request: ProcessRequest):
    job_id = await job_queue.enqueue(request)
    await event_manager.emit_global(job_store.list_active_jobs())
    return {"jobId": job_id}
