# FFmpeg Log Lifecycle: Worker → Backend → Frontend

## Overview

Logs travel through four distinct layers: **Worker** (captures raw output) → **JSON status file** (shared filesystem) → **Backend SSE** (streams updates) → **Frontend store + component** (renders).

---

## Layer 1 — Worker: Reading stdout/stderr (`ffmpeg_runner.py`)

```
worker/src/worker/ffmpeg_runner.py
worker/src/worker/processor.py
```

**Subprocess creation** (ffmpeg_runner.py ~line 82):
- `stderr=subprocess.STDOUT` — merges stderr into stdout so all output is one stream
- Text mode + UTF-8 encoding
- `readline()` loop reads one line at a time until EOF

**Local emit function** (~line 71-79):
```python
log: List[str] = []

def emit(line: str):
    log.append(line)
    if log_callback:
        log_callback(line)   # fires live callback per line

emit(f"$ {cmd_str}")         # first entry: the command itself
```

**What goes into logs:**
- `"$ ffmpeg -y -i input.mkv ..."` — the command
- Progress lines: `"frame= 100 fps=25.0 q=28.0 size= 1024kB time=00:00:30 ..."`
- Duration: `"  Duration: 00:01:00.00, ..."`
- Separators: `"---"`
- Completion: `"Done: /path/input -> /path/output"`

**Progress parsing** — `PROGRESS_RE` regex on lines containing `"frame="`:
- Extracts structured dict: `{ frame, fps, q, size_bytes, time, bitrate, speed, percent, ... }`
- Calls `progress_callback(parsed_dict)` in addition to `log_callback(line)`

**Return:** `List[str]` of all emitted lines for that run.

---

## Layer 2 — Processor → Status File (`processor.py`)

```
worker/src/worker/processor.py
```

The processor maintains a **single `all_logs` list for the entire job** and writes it to a JSON file on every significant event:

```python
all_logs: list = []
log_callback=lambda line: all_logs.append(line)

# Called on job start, per-file start, per progress update, per-file done, job done:
self.update_status(job_id, "processing", percent, logs=all_logs, file_progress=file_progress)
```

**`update_status`** writes atomically to:
```
{JOB_DATA_ROOT}/status/{job_id}.json
```

File structure:
```json
{
  "job_id": "...",
  "status": "processing",
  "overall_percent": 42.0,
  "current_file": "video.mkv",
  "logs": ["$ ffmpeg ...", "frame= 100 fps=25.0 ..."],
  "file_progress": {
    "/path/video.mkv": {
      "status": "processing",
      "frame": 100, "fps": 25.0, "q": 28.0,
      "size_bytes": 1048576, "time": "00:00:30",
      "bitrate": "5000kbits/s", "speed": "1.0",
      "percent": 50.0,
      "cmd": "ffmpeg -y -i ...",
      "done_line": "/input -> /output"   ← added when done
    }
  }
}
```

**Important:** Logs are accumulated as the **full history** — every update replaces the file with all logs seen so far.

---

## Layer 3 — Backend: File Polling → SSE Stream

```
backend/src/app/main.py           (polling loop)
backend/src/app/core/jobs/events.py (EventManager)
backend/src/app/api/routes_jobs.py  (SSE endpoints)
backend/src/app/core/models.py      (JobStatus model)
```

**Polling loop** (`main.py`, every 1 second):
```
for each *.json file in {JOB_DATA_ROOT}/status/:
    if mtime changed:
        parse JobStatus from file
        event_manager.emit_update(job)   → puts into per-job async queues
```

**SSE endpoint** `GET /api/jobs/{job_id}/events`:
1. Subscribes to job's async queue
2. Immediately yields initial `JobStatus` (including full logs)
3. Yields each queued update as SSE `"status"` event
4. Auto-closes stream when status is `"completed"` or `"failed"`

**SSE message format:**
```
event: status
data: {"job_id":"...","status":"processing","overall_percent":42,"logs":[...],"file_progress":{...}}
```

Each SSE event carries the **entire** `logs` array (not a diff).

---

## Layer 4 — Frontend: Store → Component

```
frontend/src/stores/jobStore.ts
frontend/src/api/client.ts
frontend/src/components/JobLogs.vue
frontend/src/components/JobProgress.vue
```

### jobStore.ts

`connectEvents(jobId)` opens an `EventSource` to `/api/jobs/{jobId}/events` and on each `"status"` event:

```typescript
store.status        = data.status
store.progress      = data.overall_percent
store.currentFile   = data.current_file
store.logs          = data.logs            // full array replacement
store.fileProgress  = data.file_progress   // full object replacement
```

EventSource closes itself when status reaches `"completed"` or `"failed"`.

### JobLogs.vue

- **Does NOT use `store.logs`** (the raw string array)
- **Watches `jobStore.fileProgress` deeply** (computed `fileRows`)
- Builds ordered list of file rows:
  - Extracts basename from path
  - Shows `[queued]` / `[failed]` badge for those states
  - For `processing`/`done`: formats metrics (frame, fps, bitrate, size, time, speed)
  - Shows `cmd` field (the ffmpeg command) and `done_line` field if present
  - Caches last non-empty metrics in `lastMetrics` ref to keep them visible after completion
- Auto-scrolls container when `fileRows` changes

### JobProgress.vue

Reads `jobStore.activeJobId`, `jobStore.progress`, `jobStore.status`, `jobStore.currentFile` — shows progress bar only when a job is active.

---

## End-to-End Data Flow Diagram

```
User clicks Process
    │
    ▼
jobStore.startJob(payload)
    ├─ POST /api/process → { jobId }
    └─ jobStore.connectEvents(jobId)
           └─ EventSource → GET /api/jobs/{jobId}/events

Worker process (subprocess)
    │  ffmpeg stdout/stderr → readline() loop
    │  emit(line) → all_logs.append(line)
    │  progress_callback → file_progress dict updated
    │  update_status() → writes {job_id}.json atomically
    ▼
{JOB_DATA_ROOT}/status/{job_id}.json  (updated every ~second)

Backend polling loop (1s interval)
    │  mtime changed → parse JobStatus
    │  event_manager.emit_update(job)
    ▼
Per-job async queue
    │  SSE endpoint reads queue
    │  yields: event: status / data: {full JobStatus JSON}
    ▼
Browser EventSource
    │  'status' event received
    │  store.logs = data.logs             (full replacement)
    │  store.fileProgress = data.file_progress (full replacement)
    ▼
Vue reactivity
    ├─ JobLogs.vue: computed fileRows recomputes → re-renders metrics
    └─ JobProgress.vue: progress bar updates

EventSource closes when status = 'completed' | 'failed'
```

---

## Key Design Points

| Aspect | Detail |
|--------|--------|
| **logs array** | Full history accumulated, sent whole every update — no diffing |
| **fileProgress** | Structured per-file metrics dict, replaces entirely each update |
| **JobLogs.vue** | Renders from `fileProgress`, not from raw `logs` strings |
| **Polling cadence** | ~1 second (mtime-based, skips unchanged files) |
| **SSE closure** | Automatic on `completed`/`failed` — both server and client sides |
| **Storage** | File-based JSON, no database — worker writes, backend reads |
