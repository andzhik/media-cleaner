import json
import os
from pathlib import Path
from typing import Optional, List
from ..models import JobStatus

JOB_DATA_ROOT = Path(os.getenv("JOB_DATA_ROOT", "/job-data"))

class JobStore:
    def __init__(self):
        self.status_dir = JOB_DATA_ROOT / "status"

    def get_job(self, job_id: str) -> Optional[JobStatus]:
        status_file = self.status_dir / f"{job_id}.json"
        if status_file.exists():
            try:
                with open(status_file, "r") as f:
                    data = json.load(f)
                return JobStatus(**data)
            except Exception:
                return None
        # Fallback to check if it's pending?
        # Actually my queue implementation in 'backend...queue.py' writes to 'pending'.
        # But 'queue.py' ALSO called 'job_store.save_job' which was in-memory.
        # Keep in-memory as cache? Or strict file based?
        # Strict file based is better for persistence across restarts.
        # But 'queue.py' needs to write the initial status file then.
        return None

    def save_job(self, job: JobStatus):
        self.status_dir.mkdir(parents=True, exist_ok=True)
        status_file = self.status_dir / f"{job.job_id}.json"
        with open(status_file, "w") as f:
            f.write(job.model_dump_json())
    
    def list_jobs(self) -> List[JobStatus]:
        jobs = []
        if self.status_dir.exists():
            for f in self.status_dir.glob("*.json"):
                try:
                    with open(f, "r") as fp:
                        jobs.append(JobStatus(**json.load(fp)))
                except Exception:
                    pass
        return jobs

    def list_active_jobs(self) -> List[JobStatus]:
        return [j for j in self.list_jobs() if j.status in ("pending", "processing")]

job_store = JobStore()

