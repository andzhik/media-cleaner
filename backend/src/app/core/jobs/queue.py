import asyncio
import json
import os
from pathlib import Path
from ..models import ProcessRequest, JobStatus
from .store import job_store
import uuid

JOB_DATA_ROOT = Path(os.getenv("JOB_DATA_ROOT", "/job-data"))

class JobQueue:
    def __init__(self):
        # We don't need an internal queue if using file-based handoff
        self.pending_dir = JOB_DATA_ROOT / "pending"
        self.pending_dir.mkdir(parents=True, exist_ok=True)

    async def enqueue(self, request: ProcessRequest) -> str:
        job_id = str(uuid.uuid4())
        
        # Determine the effective files list even if deprecated selections are used
        files_list = []
        if request.files:
            files_list = request.files
        elif request.selections:
            files_list = [s.rel_path for s in request.selections]

        job = JobStatus(
            job_id=job_id,
            status="pending",
            overall_percent=0.0,
            dir=request.dir,
            files=files_list
        )
        job_store.save_job(job)
        
        # Create job payload for worker
        payload = request.model_dump(mode='json')
        payload["job_id"] = job_id
        
        # Write to pending file
        job_file = self.pending_dir / f"{job_id}.json"
        with open(job_file, "w") as f:
            json.dump(payload, f)
            
        return job_id

job_queue = JobQueue()

