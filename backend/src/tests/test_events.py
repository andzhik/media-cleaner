import asyncio

from app.core.jobs.events import EventManager
from app.core.models import JobStatus


def _make_job(job_id="job-1", status="pending"):
    return JobStatus(job_id=job_id, status=status, overall_percent=0.0)


# --- per-job subscribe / emit_update / unsubscribe ---

async def test_subscribe_returns_queue():
    mgr = EventManager()
    q = await mgr.subscribe("job-1")
    assert isinstance(q, asyncio.Queue)


async def test_subscribe_creates_separate_queues_per_job():
    mgr = EventManager()
    q1 = await mgr.subscribe("job-A")
    q2 = await mgr.subscribe("job-B")
    assert q1 is not q2
    assert len(mgr._listeners["job-A"]) == 1
    assert len(mgr._listeners["job-B"]) == 1


async def test_subscribe_multiple_times_same_job():
    mgr = EventManager()
    q1 = await mgr.subscribe("job-1")
    q2 = await mgr.subscribe("job-1")
    assert q1 is not q2
    assert len(mgr._listeners["job-1"]) == 2


async def test_unsubscribe_removes_queue():
    mgr = EventManager()
    q = await mgr.subscribe("job-1")
    await mgr.unsubscribe("job-1", q)
    assert q not in mgr._listeners.get("job-1", [])


async def test_unsubscribe_only_removes_target_queue():
    mgr = EventManager()
    q1 = await mgr.subscribe("job-1")
    q2 = await mgr.subscribe("job-1")
    await mgr.unsubscribe("job-1", q1)
    assert q1 not in mgr._listeners["job-1"]
    assert q2 in mgr._listeners["job-1"]


async def test_unsubscribe_nonexistent_job_does_not_raise():
    mgr = EventManager()
    q = asyncio.Queue()
    await mgr.unsubscribe("nonexistent", q)  # should not raise


async def test_unsubscribe_queue_not_in_list_does_not_raise():
    mgr = EventManager()
    await mgr.subscribe("job-1")
    stray_q = asyncio.Queue()
    await mgr.unsubscribe("job-1", stray_q)  # stray_q was never subscribed


async def test_emit_update_delivers_to_subscriber():
    mgr = EventManager()
    job = _make_job("job-1")
    q = await mgr.subscribe("job-1")
    await mgr.emit_update(job)
    result = q.get_nowait()
    assert result.job_id == "job-1"


async def test_emit_update_delivers_to_all_subscribers_of_job():
    mgr = EventManager()
    job = _make_job("job-1")
    q1 = await mgr.subscribe("job-1")
    q2 = await mgr.subscribe("job-1")
    await mgr.emit_update(job)
    assert q1.get_nowait().job_id == "job-1"
    assert q2.get_nowait().job_id == "job-1"


async def test_emit_update_only_delivers_to_matching_job():
    mgr = EventManager()
    job_a = _make_job("job-A")
    q_a = await mgr.subscribe("job-A")
    q_b = await mgr.subscribe("job-B")
    await mgr.emit_update(job_a)
    assert not q_a.empty()
    assert q_b.empty()


async def test_emit_update_with_no_listeners_does_not_raise():
    mgr = EventManager()
    job = _make_job("no-listeners")
    await mgr.emit_update(job)  # should not raise


# --- global subscribe / emit_global / unsubscribe_global ---

async def test_subscribe_global_returns_queue():
    mgr = EventManager()
    q = await mgr.subscribe_global()
    assert isinstance(q, asyncio.Queue)


async def test_subscribe_global_appends_to_list():
    mgr = EventManager()
    q1 = await mgr.subscribe_global()
    q2 = await mgr.subscribe_global()
    assert q1 in mgr._global_listeners
    assert q2 in mgr._global_listeners


async def test_unsubscribe_global_removes_queue():
    mgr = EventManager()
    q = await mgr.subscribe_global()
    await mgr.unsubscribe_global(q)
    assert q not in mgr._global_listeners


async def test_unsubscribe_global_nonexistent_queue_does_not_raise():
    mgr = EventManager()
    q = asyncio.Queue()
    await mgr.unsubscribe_global(q)  # should not raise


async def test_emit_global_delivers_to_all_global_subscribers():
    mgr = EventManager()
    jobs = [_make_job("j1"), _make_job("j2")]
    q1 = await mgr.subscribe_global()
    q2 = await mgr.subscribe_global()
    await mgr.emit_global(jobs)
    result1 = q1.get_nowait()
    result2 = q2.get_nowait()
    assert len(result1) == 2
    assert len(result2) == 2
    assert {j.job_id for j in result1} == {"j1", "j2"}


async def test_emit_global_with_empty_list():
    mgr = EventManager()
    q = await mgr.subscribe_global()
    await mgr.emit_global([])
    result = q.get_nowait()
    assert result == []


async def test_emit_global_with_no_listeners_does_not_raise():
    mgr = EventManager()
    await mgr.emit_global([_make_job()])  # should not raise
