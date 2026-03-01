import json
import os
from pathlib import Path
from ..models import ProcessRequest, JobStatus
from .store import job_store
import uuid

JOB_DATA_ROOT = Path(os.getenv("JOB_DATA_ROOT", "/job-data"))

class JobQueue:
    def __init__(self):
        self.pending_dir = JOB_DATA_ROOT / "pending"

    def _ensure_dirs(self):
        self.pending_dir.mkdir(parents=True, exist_ok=True)

    async def enqueue(self, request: ProcessRequest) -> str:
        job_id = str(uuid.uuid4())
        first_file = None
        if request.selections and len(request.selections) == 1:
            first_file = request.selections[0].rel_path

        job = JobStatus(
            job_id=job_id,
            status="pending",
            overall_percent=0.0,
            dir=request.dir or "",
            first_file=first_file
        )
        job_store.save_job(job)
        
        # Create job payload for worker
        payload = request.model_dump(mode='json')
        payload["job_id"] = job_id
        
        # Write to pending file
        self._ensure_dirs()
        job_file = self.pending_dir / f"{job_id}.json"
        with open(job_file, "w") as f:
            json.dump(payload, f)
            
        return job_id

job_queue = JobQueue()

