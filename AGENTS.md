# Video Cleaner Web Agent Guide

## Scope

LAN-only video cleanup app:

- `frontend/`: Vue 3, TypeScript, Vite, PrimeVue.
- `backend/`: FastAPI API on `:8000`.
- `worker/`: Python FFmpeg job runner.

Shared roots are `mnt/input`, `mnt/output`, and `mnt/job-data`.

## Rules

- Use Windows PowerShell.
- Keep media paths confined to configured roots.
- Prefer small local changes over new abstractions.

## Work Map

- UI and client state: `frontend/src/`.
- API and backend domain logic: `backend/src/app/`.
- Job execution and FFmpeg commands: `worker/src/worker/`.

If a name is unclear, search with PowerShell tools such as `Get-ChildItem` and `Select-String`. Rename only when the change improves code you are already touching.

## Commands

Run all services:

```powershell
.\run_all.bat
```

Docker:

```powershell
docker compose up --build
```

Lint:

```powershell
.\run_lint.bat
```

Tests:

```powershell
.\run_tests.bat
```

Use `MANUAL_RUN.md`, `TESTS.md`, `API.md`, and `frontend/UI.md` for details instead of duplicating them here.

## Notes

Backend changes should preserve the API contract in `API.md`.

Worker changes should preserve requested audio/subtitle selections exactly.

Frontend changes should stay compact and task-focused; this is a media management tool, not a landing page.
