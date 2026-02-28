import asyncio
from typing import List, Dict
from ..models import JobStatus

class EventManager:
    def __init__(self):
        # job_id -> list of queues
        self._listeners: Dict[str, List[asyncio.Queue]] = {}
        # Global listeners for jobs-list updates
        self._global_listeners: List[asyncio.Queue] = []

    async def subscribe(self, job_id: str) -> asyncio.Queue:
        if job_id not in self._listeners:
            self._listeners[job_id] = []
        q = asyncio.Queue()
        self._listeners[job_id].append(q)
        return q

    async def unsubscribe(self, job_id: str, q: asyncio.Queue):
        if job_id in self._listeners:
            if q in self._listeners[job_id]:
                self._listeners[job_id].remove(q)

    async def emit_update(self, job: JobStatus):
        if job.job_id in self._listeners:
            for q in self._listeners[job.job_id]:
                await q.put(job)

    async def subscribe_global(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self._global_listeners.append(q)
        return q

    async def unsubscribe_global(self, q: asyncio.Queue):
        if q in self._global_listeners:
            self._global_listeners.remove(q)

    async def emit_global(self, jobs: List[JobStatus]):
        for q in self._global_listeners:
            await q.put(jobs)

event_manager = EventManager()
