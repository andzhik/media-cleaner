import asyncio
import sys
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from .api import routes_tree, routes_list, routes_process, routes_jobs
from .core.jobs.events import event_manager
from .core.models import JobStatus

JOB_DATA_ROOT = Path(os.getenv("JOB_DATA_ROOT", "/job-data"))

async def _poll_status_files():
    """Background task: watch the status dir and push updates into SSE queues."""
    status_dir = JOB_DATA_ROOT / "status"
    seen_mtimes: dict = {}
    while True:
        try:
            if status_dir.exists():
                for path in status_dir.glob("*.json"):
                    mtime = path.stat().st_mtime
                    if seen_mtimes.get(path.name) != mtime:
                        seen_mtimes[path.name] = mtime
                        try:
                            with open(path, "r") as f:
                                data = json.load(f)
                            job = JobStatus(**data)
                            await event_manager.emit_update(job)
                        except Exception as e:
                            print(f"Status poll error for {path.name}: {e}")
        except Exception as e:
            print(f"Status poll loop error: {e}")
        await asyncio.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_poll_status_files())
    yield
    task.cancel()


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

