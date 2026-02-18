# Video Cleaner Web

A LAN-only web application for managing your video library. Clean up audio/subtitles and organize your collection efficiently.

## Running Manually (Without Docker)

For Windows users who prefer not to use Docker, see [MANUAL_RUN.md](MANUAL_RUN.md) for detailed instructions.
A convenience script `run_all.bat` is also provided.

## Running with Docker

## 🚀 Quick Start

1. **Install Docker Desktop** (Windows/Mac) or Docker Engine (Linux).
2. **Setup Folders**: Create `mnt/input` and `mnt/output` directories in the project root (or map your own in `docker-compose.yml`).
3. **Run the App**:
   ```bash
   docker compose up --build
   ```
4. **Access the UI**: Open [http://localhost:5173](http://localhost:5173) in your browser.

## 🛠️ Project Structure

- `frontend/`: Vue 3 + Vite frontend.
- `backend/`: FastAPI backend for file exploration and job management.
- `worker/`: Python worker for processing videos with FFmpeg.
- `mnt/`: Shared volume for input/output media files.

## ❓ Troubleshooting

Facing issues? Check our [Troubleshooting Guide](./TROUBLESHOOTING.md) for solutions to common problems.

## 📝 Implementation Details

For technical details, see the [Implementation Plan](./implementation-plan.md).
