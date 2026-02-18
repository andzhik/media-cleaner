# Manual Run Guide (Windows CMD)

This guide explains how to run the Video Cleaner Web application components manually on Windows without using Docker.

## Quick Start (Batch Script)

A helper script `run_all.bat` has been created in the project root.
Before running it, you **must install dependencies first** (see below).

Once dependencies are installed, simply double-click `run_all.bat` to launch all services in separate windows.

## Prerequisites

1.  **Python 3.12+**: Ensure Python is installed and added to your PATH.

2.  **Node.js**: Required for the frontend.
3.  **FFmpeg**: Must be installed and available in your system PATH (type `ffmpeg -version` in cmd to verify).

## Setup Directories

The system requires three directories to function. You can use the existing `mnt` folder in the project root.

1.  Create a `job-data` directory inside `mnt` if you want to keep data together, or use any other location.
    *   Example structure:
        *   `C:\...\video-cleaner-web\mnt\input` (Source videos)
        *   `C:\...\video-cleaner-web\mnt\output` (Processed videos)
        *   `C:\...\video-cleaner-web\mnt\job-data` (Internal job status files)

## Component 1: Job Worker

This component processes the video files using FFmpeg.

1.  Open a new Command Prompt (cmd).
2.  Navigate to the `worker` directory:
    ```cmd
    cd c:\Users\Andrei\Documents\Projects\video-cleaner-web\worker
    ```
3.  Install the package in editable mode (run once):
    ```cmd
    pip install -e .
    ```
4.  Set environment variables and run:
    ```cmd
    set INPUT_ROOT=c:\Users\Andrei\Documents\Projects\video-cleaner-web\mnt\input
    set OUTPUT_ROOT=c:\Users\Andrei\Documents\Projects\video-cleaner-web\mnt\output
    set JOB_DATA_ROOT=c:\Users\Andrei\Documents\Projects\video-cleaner-web\mnt\job-data
    
    python -m worker.main
    ```

## Component 2: Backend API

This is the FastAPI server that the frontend communicates with.

1.  Open a new Command Prompt (cmd).
2.  Navigate to the `backend` directory:
    ```cmd
    cd c:\Users\Andrei\Documents\Projects\video-cleaner-web\backend
    ```
3.  Install the package in editable mode (run once):
    ```cmd
    pip install -e .
    ```
4.  Set environment variables and run:
    ```cmd
    set INPUT_ROOT=c:\Users\Andrei\Documents\Projects\video-cleaner-web\mnt\input
    set OUTPUT_ROOT=c:\Users\Andrei\Documents\Projects\video-cleaner-web\mnt\output
    set JOB_DATA_ROOT=c:\Users\Andrei\Documents\Projects\video-cleaner-web\mnt\job-data
    
    uvicorn app.main:app --reload --port 8000
    ```

## Component 3: Frontend

The web interface.

1.  Open a new Command Prompt (cmd).
2.  Navigate to the `frontend` directory:
    ```cmd
    cd c:\Users\Andrei\Documents\Projects\video-cleaner-web\frontend
    ```
3.  Install dependencies (run once):
    ```cmd
    npm install
    ```
4.  Run the development server:
    ```cmd
    npm run dev
    ```
5.  Open your browser and navigate to the URL shown (usually `http://localhost:5173`).

## Troubleshooting

*   **FFmpeg not found**: Ensure `ffmpeg` is in your Windows Environmental Variables PATH.
*   **Import Errors**: If Python complains about modules not found, ensure you ran `pip install -e .` in both `backend` and `worker` directories.
*   **Paths**: Ensure the paths in `set` commands are absolute and point to existing directories.
