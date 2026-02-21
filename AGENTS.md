# AGENTS.md — Video Cleaner Web

> Read this file before writing or modifying any code.

---

## Project Overview

**Video Cleaner Web** is a LAN-only web app for cleaning audio and subtitle tracks from video files. The user browses a directory tree, selects which streams to keep per-file, and submits a job. FFmpeg re-muxes each file into an output directory keeping only the selected streams.

**Stack:**

| Layer    | Technology                                       |
|----------|--------------------------------------------------|
| Frontend | Vue 3 + Vite + TypeScript + PrimeVue + PrimeFlex |
| Backend  | Python 3.12 + FastAPI + Uvicorn + SSE-Starlette  |
| Worker   | Python 3.12 + FFmpeg (subprocess)                |
| IPC      | Shared filesystem volume (`mnt/job-data/`)       |

---

## Repository Layout

```
video-cleaner-web/
├── backend/      # FastAPI REST API (Python)
├── worker/       # Background video processor (Python + FFmpeg)
├── frontend/     # Vue 3 SPA
├── mnt/
│   ├── input/    # Source video files (read-only for worker)
│   ├── output/   # Processed video files
│   └── job-data/ # IPC: pending/, processing/, completed/, failed/, status/
├── docker-compose.yml
├── run_all.bat   # Windows convenience launcher (all 3 services)
├── API.md        # Full API reference with request/response examples
└── MANUAL_RUN.md # Step-by-step Windows manual setup guide
```

---

## Architecture & Data Flow

```
Browser (Vue SPA)
  │  REST + SSE
  ▼
Backend (FastAPI)
  │  Writes job JSON → mnt/job-data/pending/
  ▼
Worker (polling loop)
  │  Reads pending/, runs ffmpeg on mnt/input/
  │  Writes output → mnt/output/
  │  Writes status JSON → mnt/job-data/status/
  ▼                      ▲
Backend (reads status/) ─┘  (shared volume)
  │  Emits SSE events to subscribed clients
  ▼
Browser (updates progress bar & logs)
```

**Key constraint**: The backend and worker share **only** the filesystem. There is no message broker, database, or direct HTTP calls between them.

### Job Lifecycle

1. User clicks **Process** → frontend `POST /api/process`.
2. Backend writes a `pending` job file and returns a `jobId`.
3. Frontend opens an SSE stream on `GET /api/jobs/{id}/events`.
4. Worker picks up the pending file, runs ffmpeg per-file, and atomically updates a status JSON file.
5. Backend SSE route reads status and fans out updates to subscribers.
6. Frontend closes the SSE stream on `completed` or `failed`.

---

## Services

### `backend/`
FastAPI server. Handles file-system browsing, job submission, and job status/SSE. Reads media metadata via `ffprobe`. See `API.md` for all endpoints and data models.

Notable behaviors:
- All user-supplied paths are validated against a root to prevent path traversal.
- `ffprobe` is run in a thread pool to avoid blocking the async event loop.
- Job status is read from files in `mnt/job-data/status/` (written by the worker).
- SSE event fan-out is in-process only — it does not watch files for changes.

### `worker/`
Long-running polling process. Checks `mnt/job-data/pending/` every 2 seconds. For each job, iterates over the file selections and runs `ffmpeg` with exact stream indices. Writes atomic status updates to `mnt/job-data/status/`. On finish, moves the job file to `completed/` or `failed/`.

Notable behaviors:
- Stream selection uses explicit stream IDs when provided by the UI (preferred), falling back to language-based filtering.
- Progress is parsed from ffmpeg's stderr (`Duration:` and `time=` fields).
- Uses `os.replace()` for atomic status file writes.

### `frontend/`
Single-page Vue 3 app. No client-side routing. Global state is managed with Vue `reactive()` objects (no Pinia). All API calls go through a single `api/client.ts` module.

- **Left panel**: folder tree (directories only, all nodes expanded by default).
- **Top toolbar**: batch language toggles, output folder input, Process button.
- **Main table**: per-file and per-stream checkboxes. All streams are selected by default.
- **Bottom panel**: job progress bar and auto-scrolling log view.

---

## Running the Application

See `MANUAL_RUN.md` for detailed steps. Quick reference:

**With Docker:**
```bash
docker compose up --build
# Frontend: http://localhost:5173  |  Backend: http://localhost:8000
```

**Without Docker (Windows):**
```bash
# Install deps once in each of backend/, worker/, frontend/
run_all.bat   # launches all 3 services in separate windows
```

**Required environment variables** (backend & worker):
```
INPUT_ROOT    — absolute path to source media directory
OUTPUT_ROOT   — absolute path to output media directory
JOB_DATA_ROOT — absolute path to job-data directory
```

**System prerequisites:** Python 3.12+, Node.js, FFmpeg (must be on PATH).

---

## Development Conventions

### Python
- Pydantic v2 models for all shared data shapes.
- New API routes go in `backend/` and must be registered in the main app.
- User-supplied paths must always be validated before use.
- Blocking I/O in async context must use `asyncio.to_thread()`.
- Status file writes must use atomic replacement (write `.tmp`, then `os.replace()`).

### TypeScript / Vue
- All components use `<script setup lang="ts">`.
- All API calls go through `api/client.ts`. Do not `fetch` directly in components.
- Global state uses Vue `reactive()`. Do not introduce Pinia without discussion.
- Use PrimeVue components; PrimeFlex for layout.

### Adding a New Feature — Checklist
1. Update the Pydantic data model if the API shape changes.
2. Add/update the backend route and register it.
3. Add the fetch wrapper in the frontend API client.
4. Update stores and components as needed.
5. Update `API.md` if any endpoint or model changed.

---

## Common Pitfalls

- **SSE gap**: The worker does not notify the backend's SSE queues directly. The backend must poll the status file and call the event emitter to push real-time updates to clients.
- **Windows asyncio**: `WindowsProactorEventLoopPolicy` is set in the backend entry point. Do not remove it — it is required for subprocess support.
- **Path separators**: Always normalize paths to forward slashes and strip leading `/` before joining with a root directory. Follow the established pattern in the codebase.
- **`.ts` extension**: The backend recognizes `.ts` video files; the worker's auto-scan fallback currently does not. Keep these lists in sync.
- **Job data directories**: `mnt/job-data/` and its subdirectories must exist before starting either service. Most are created automatically, but verify if you see "file not found" errors on startup.
