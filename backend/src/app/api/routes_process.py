from fastapi import APIRouter
from ..core.models import ProcessRequest
from ..core.jobs.queue import job_queue

router = APIRouter()

@router.post("/process")
async def start_process(request: ProcessRequest):
    job_id = await job_queue.enqueue(request)
    return {"jobId": job_id}
