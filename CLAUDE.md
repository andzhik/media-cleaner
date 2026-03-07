# CLAUDE.md

## Rules

- Do NOT run `npm run build` in any directory: dev environment, hot reload.
- Never read files inside `node_modules/`.
- Ignore tests unless explicitly asked to run or modify.
- Use Windows PowerShell.

## Project Overview
LAN video library manager. Services: `frontend/` (Vue 3+TS+Vite+PrimeVue 4), `backend/` (FastAPI:8000), `worker/` (Python+FFmpeg), `mnt/` (shared volumes).

## Docs
`MANUAL_RUN.md`, `API.md`, `TESTS.md`
