import asyncio
import sys
import json
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from .api import routes_tree, routes_list, routes_process, routes_jobs
from .core.jobs.events import event_manager
from .core.jobs.store import job_store
from .core.models import JobStatus

JOB_DATA_ROOT = Path(os.getenv("JOB_DATA_ROOT", "/job-data"))

async def _poll_status_files():
    """Background task: watch the status dir and push updates into SSE queues."""
    status_dir = JOB_DATA_ROOT / "status"
    seen_mtimes: dict = {}
    prev_active_ids: set = set()
    while True:
        try:
            changed = False
            if status_dir.exists():
                for path in status_dir.glob("*.json"):
                    mtime = path.stat().st_mtime
                    if seen_mtimes.get(path.name) != mtime:
                        seen_mtimes[path.name] = mtime
                        changed = True
                        try:
                            with open(path, "r") as f:
                                data = json.load(f)
                            job = JobStatus(**data)
                            await event_manager.emit_update(job)
                        except Exception as e:
                            print(f"Status poll error for {path.name}: {e}")
            if changed:
                active_jobs = job_store.list_active_jobs()
                active_ids = {j.job_id for j in active_jobs}
                if active_ids != prev_active_ids or changed:
                    prev_active_ids = active_ids
                    await event_manager.emit_global(active_jobs)
        except Exception as e:
            print(f"Status poll loop error: {e}")
        await asyncio.sleep(1)

async def _cleanup_old_jobs():
    """Background task: delete old completed/failed jobs and their status files."""
    COMPLETED_TTL = 86400        # 1 day
    FAILED_TTL    = 86400 * 28   # 4 weeks
    while True:
        await asyncio.sleep(3600)  # check every hour
        try:
            now = time.time()
            for subdir, ttl in (("completed", COMPLETED_TTL), ("failed", FAILED_TTL)):
                job_dir = JOB_DATA_ROOT / subdir
                if not job_dir.exists():
                    continue
                for path in job_dir.glob("*.json"):
                    if now - path.stat().st_mtime > ttl:
                        job_id = path.stem
                        path.unlink(missing_ok=True)
                        status_file = JOB_DATA_ROOT / "status" / f"{job_id}.json"
                        status_file.unlink(missing_ok=True)
                        print(f"Cleaned up old job: {job_id}")
        except Exception as e:
            print(f"Cleanup error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    task1 = asyncio.create_task(_poll_status_files())
    task2 = asyncio.create_task(_cleanup_old_jobs())
    yield
    task1.cancel()
    task2.cancel()


app = FastAPI(title="Video Cleaner API", lifespan=lifespan)

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_tree.router, prefix="/api")
app.include_router(routes_list.router, prefix="/api")
app.include_router(routes_process.router, prefix="/api")
app.include_router(routes_jobs.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Video Cleaner API is running"}

