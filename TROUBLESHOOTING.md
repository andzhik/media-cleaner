# Troubleshooting Guide

This guide covers common issues you might encounter while setting up or running the Video Cleaner Web application.

## 🐳 Docker & Orchestration

### Services not starting
If one or more services fail to start, check the logs:
```bash
docker compose logs -f
```
Common causes include:
- **Port conflicts**: Port 8000 (API) or 5173 (Frontend) might already be in use.
- **Docker path mapping**: On Windows, ensure Docker has permission to access the project directory and the input/output folders.

### Volumes not showing files
If the folder tree is empty or files are missing:
1. Check if the `mnt/input` and `mnt/output` directories exist on your host machine.
2. Verify that `docker-compose.yml` correctly maps these paths.
3. If running on Windows with WSL2, ensure the files are accessible within the WSL2 environment.

---

## 🖥️ Backend (API)

### 403 Forbidden / Path Traversal Errors
The backend includes security checks to prevent accessing files outside the configured `INPUT_ROOT` and `OUTPUT_ROOT`.
- Ensure the paths you are requesting are children of the configured root.
- Check the `INPUT_ROOT` and `OUTPUT_ROOT` environment variables in `docker-compose.yml`.

### CORS Policy Errors
If you see errors in the browser console like `No 'Access-Control-Allow-Origin' header is present`:
- The backend should be configured with `CORSMiddleware`. Check `backend/src/app/main.py`.
- Ensure the frontend is accessing the API via the correct URL (configured in `VITE_API_URL`).

---

## ⚙️ Worker & FFmpeg

### No streams detected in video files
If the UI shows "No audio/subtitle streams" for a file:
- Ensure `ffprobe` is installed in the worker container (it is included in the default `Dockerfile`).
- Check the worker logs for `ffprobe` errors: `docker compose logs worker`.
- **JSON Parsing Errors**: If `ffprobe` returns an unexpected JSON structure, the backend might fail to parse it. Check for "Error probing file" logs in the `api` service.
- Try running `ffprobe` manually on the file to see if it's a valid video format.

### "Process" button does nothing or fails
- Check the `worker` service logs.
- Ensure the `OUTPUT_ROOT` is writable by the worker container.
- If the worker fails to start a task, verify that the `job-data` volume is correctly shared between the `api` and `worker` services.

---

## 🌐 Frontend (Vue/Vite)

### Frontend cannot connect to API
If the UI is stuck loading or shows network errors:
- Ensure the `api` service is running and accessible at `localhost:8000`.
- Verify the `VITE_API_URL` environment variable in `docker-compose.yml`.
- If accessing from another device on the LAN, change `localhost` to the host machine's LAN IP address.

### Vite Build Errors
If you are developing locally (outside Docker) and encounter build errors:
- Ensure you have Node.js 20+ installed.
- Delete `node_modules` and run `npm install` again.
- Clear Vite cache: `npm run dev -- --force`.

---

## 🛠️ Common Fixes

### Restarting the Environment
Sometimes a clean restart fixes networking or volume mapping issues:
```bash
docker compose down -v
docker compose up --build
```
*(The `-v` flag removes volumes, including the job queue state, which can help if the state is corrupted.)*

### Checking Input File Permissions
If the worker can read but not write, or cannot see files at all:
```bash
# Check permissions inside the container
docker compose exec worker ls -la /media/input
```
