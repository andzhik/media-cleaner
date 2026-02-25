@echo off
SET "PROJECT_ROOT=%~dp0"
REM Remove trailing backslash if present (though dp0 usually has it)
if "%PROJECT_ROOT:~-1%"=="\" SET "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

@REM SET "INPUT_ROOT=%PROJECT_ROOT%\mnt\input"
SET "INPUT_ROOT=e:\video"
SET "OUTPUT_ROOT=e:\output"
SET "JOB_DATA_ROOT=%PROJECT_ROOT%\mnt\job-data"
SET "VITE_MEDIA_TYPES=tv show,movies"

echo Starting Backend...
start "Backend" cmd /k "cd /d "%PROJECT_ROOT%\backend" && set "INPUT_ROOT=%INPUT_ROOT%" && set "OUTPUT_ROOT=%OUTPUT_ROOT%" && set "JOB_DATA_ROOT=%JOB_DATA_ROOT%" && python -m uvicorn --app-dir src app.main:app --port 8000 --reload"

echo Starting Worker with Hot Reload...
start "Worker" cmd /k "cd /d "%PROJECT_ROOT%\worker" && set "INPUT_ROOT=%INPUT_ROOT%" && set "OUTPUT_ROOT=%OUTPUT_ROOT%" && set "JOB_DATA_ROOT=%JOB_DATA_ROOT%" && set "PYTHONPATH=src" && python -m watchfiles --target-type command "python -m worker.main" src"

echo Starting Frontend...
start "Frontend" cmd /k "cd /d "%PROJECT_ROOT%\frontend" && set "VITE_MEDIA_TYPES=%VITE_MEDIA_TYPES%" && npm run dev"

echo All services launched.
