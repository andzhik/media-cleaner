# Implementation Plan

## Project overview and description

A LAN-only web application for managing a video library and producing “stream-pruned” copies of media files. The UI lets the user browse an **input folder** (restricted root), list video files, inspect **audio/subtitle streams**, and bulk-select streams to keep **by language** (including `unknown`). When the user clicks **Process**, the backend runs **ffmpeg** to generate copies in a restricted **output folder**, excluding unselected streams, while streaming **overall progress** and **ffmpeg logs** to the UI.

Core goals:

- Simple, local-first workflow (no auth, LAN-only).
- Fast iteration and maintainable code.
- Safe filesystem access restricted to configured roots.

Out of scope:

- Remote/public access, multi-user tenancy.
- Complex per-file progress UI (overall progress only).
- Transcoding (prefer stream-copy; re-encode only if needed later).

## Requirements

### 1) Scope and deployment

- LAN-only.
- Backend exposes filesystem access only within two configured roots:
  - **Input root** (media download folder)
  - **Output root**
- Runtime: Docker Compose on Linux.
- Development: Windows (with Docker).

### 2) Backend API

#### 2.1 Folder tree

- `GET /api/tree` returns the full folder structure under the **input root**.
- Prevent path traversal; never expose outside configured roots.

#### 2.2 List directory contents + probe

- `GET /api/list?dir=...` returns files for the selected directory under input root.
- When a folder is clicked, backend **ffprobes all video files in that folder** and returns stream metadata.

Stream metadata per video file:

- Audio streams: `language`, `title`, and internal `id`.
- Subtitle streams: `language`, `title`, and internal `id`.
- Missing language is treated as `unknown`.

#### 2.3 Start processing job

- `POST /api/process` starts processing.
- Request includes:
  - Selected directory or explicit file list
  - Per-file selections of languages to keep for audio and subtitles (including `unknown`)
  - Output folder path (default from backend env, optionally overridden)

#### 2.4 Progress + logs

- Backend provides **overall progress** for the active job.
- Backend streams **ffmpeg logs** for display below the table.
- Delivery via WebSocket or SSE.

### 3) UI requirements

#### 3.1 Layout

- Left side panel: folder tree from `GET /api/tree`.
- Main area: table listing files for selected folder from `GET /api/list?dir=...`.

#### 3.2 Files table

- One row per file.
- Columns:
  1. File selection checkbox + file name
  2. Audio languages for that file (checkbox per stream/language entry), show title where available
  3. Subtitle languages for that file (checkbox per stream/language entry), show title where available
- `unknown` must appear where applicable.

#### 3.3 Batch language toggles

- Above the table, show a checkbox for each language found across the folder (including `unknown`).
- Behavior:
  - Checking a language selects all matching audio and subtitle selections across all rows.
  - Unchecking deselects all matching across all rows.

#### 3.4 Output folder + Process

- Above the table:
  - Output folder path input (default from backend env)
  - “Process” button

#### 3.5 Progress and logs

- Overall progress bar for active job.
- Log area streaming ffmpeg output (below the table).

### 4) Processing behavior

- Processing creates copies into output folder.
- Output includes:
  - Original video stream(s)
  - Only selected audio streams (by language selection)
  - Only selected subtitle streams (by language selection)
- Implemented via ffmpeg mapping (exclude unselected).

### 5) Non-functional requirements

- Strict root restrictions for read (input) and write (output).
- Clear errors surfaced to UI and in log stream.

## Tools and technology choices

### Backend

- **Python 3.12+**
- **FastAPI** for REST API and WebSocket/SSE endpoints
- `ffprobe` + `ffmpeg` executed via `subprocess` (direct CLI invocation)
- Job runner:
  - Initial: in-process queue (single worker) OR separate worker container (recommended)
  - Option to add Redis/RQ later if concurrency grows

### Frontend

- **Vue 3** + **Vite**
- **PrimeVue** component library
  - Tree, DataTable, Checkbox, Button, Sidebar/Drawer, ProgressBar, Textarea/Terminal-like log panel

### Runtime orchestration

- **Docker Compose**
- Two containers:
  1. `api` (FastAPI)
  2. `worker` (ffmpeg/ffprobe processing)
- Shared volumes for input/output and (optionally) job state.
- Progress channel: WebSocket or SSE from API to UI.

## Proposed project structure

### Repository layout

```
repo/
  docker-compose.yml
  .env.example
  README.md

  backend/
    Dockerfile
    pyproject.toml
    src/
      app/
        main.py
        api/
          routes_tree.py
          routes_list.py
          routes_process.py
          routes_jobs.py
        core/
          config.py
          security_paths.py
          models.py
          ffprobe.py
          ffmpeg_cmd.py
          jobs/
            queue.py
            store.py
            events.py
        tests/

  worker/
    Dockerfile
    src/
      worker/
        main.py
        processor.py
        ffmpeg_runner.py
        progress_parser.py

  frontend/
    Dockerfile
    index.html
    vite.config.ts
    package.json
    src/
      main.ts
      app.vue
      api/
        client.ts
      components/
        FolderTree.vue
        MediaTable.vue
        BatchLanguageBar.vue
        OutputControls.vue
        JobProgress.vue
        JobLogs.vue
      stores/
        mediaStore.ts
        jobStore.ts
```

### Notes on responsibilities

- `backend/app/api/*`: HTTP endpoints.
- `backend/app/core/security_paths.py`: canonical path join + root restriction checks.
- `backend/app/core/ffprobe.py`: probes files and normalizes language=`unknown`.
- `worker/worker/processor.py`: performs ffmpeg mapping and writes output.
- `events.py`: job events fan-out to WS/SSE subscribers.

## Data model (high-level)

### Folder tree node

- `name`, `relPath`, `children[]`

### File row

- `name`, `relPath`, `isVideo`
- `audio[]`: `{ id, language, title }`
- `subs[]`: `{ id, language, title }`

### Selection state

- Per file:
  - `includeFile: bool`
  - `audioSelectedLanguages: set<string>` (or per-stream selection if multiple same-language streams are treated independently later)
  - `subsSelectedLanguages: set<string>`

### Job state

- `jobId`, `status`, `overallPercent`, `currentFile`, `logs[]`

## API contract proposal (v1)

### `GET /api/tree`

Returns folder structure under input root.

### `GET /api/list?dir=<relPath>`

Returns:

- `dir`: relPath
- `files[]`: file rows; for videos includes `audio[]` and `subs[]` from ffprobe.
- `languages[]`: aggregate languages across all files including `unknown`.

### `POST /api/process`

Body:

- `dir`: relPath OR `files[]`: relPaths
- `outputDir`: relPath under output root
- `selections`: per-file selection payload
  Returns:
- `{ jobId }`

### Progress/log streaming

Choose one:

- **SSE**: `GET /api/jobs/<jobId>/events` (event stream with progress/log entries)
- **WebSocket**: `WS /api/jobs/<jobId>/ws`

### `GET /api/jobs/<jobId>`

Returns current snapshot status.

## Processing design

### Stream selection rule

- User selects **languages to keep** for audio and subtitles.
- Backend translates language selections into ffmpeg mapping:
  - Always keep video stream(s)
  - Keep only audio/sub streams whose language (or `unknown`) is selected

### ffprobe strategy

- On folder click:
  - Identify likely video files by extension (configurable list)
  - Run ffprobe on each video in that folder
  - Normalize language tags (missing => `unknown`)

### ffmpeg execution

- Prefer `-c copy` for speed (no re-encode) where possible.
- Capture and stream logs.
- Compute progress by:
  - ffprobe duration, plus ffmpeg progress output parsing
  - If duration unavailable, provide indeterminate progress (optional fallback)

## Dev and runtime environment

### Runtime (Linux)

- Docker Compose spins up:
  - `api` (FastAPI)
  - `worker` (ffmpeg/ffprobe tools installed)
  - Optionally `frontend` (served via Nginx) OR run frontend separately and proxy
- Volumes:
  - `/media/input` mounted into containers (read-only recommended)
  - `/media/output` mounted (read-write)

### Development (Windows)

- Recommended dev loop:
  - Frontend: `npm run dev` (Vite) on Windows
  - Backend/worker: run via Docker Compose (or run backend locally with Python if preferred)
- Use `.env` to point to Windows paths mapped into Docker (via WSL2 or Docker Desktop settings)

## Milestones

1. Skeleton: Compose, API health check, Vue app shell.
2. Folder tree + list endpoint + UI tree/table.
3. ffprobe integration and stream display.
4. Language batch toggles + output folder controls.
5. Process endpoint + worker mapping + output generation.
6. Progress + log streaming.
7. Hardening: path restriction tests, error handling, UX polish.

