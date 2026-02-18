@echo off
SET "PROJECT_ROOT=%~dp0"
REM Remove trailing backslash if present (though dp0 usually has it)
if "%PROJECT_ROOT:~-1%"=="\" SET "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

SET "INPUT_ROOT=%PROJECT_ROOT%\mnt\input"
SET "OUTPUT_ROOT=%PROJECT_ROOT%\mnt\output"
SET "JOB_DATA_ROOT=%PROJECT_ROOT%\mnt\job-data"

echo Starting Backend...
start "Backend" cmd /k "cd /d "%PROJECT_ROOT%\backend" && set "INPUT_ROOT=%INPUT_ROOT%" && set "OUTPUT_ROOT=%OUTPUT_ROOT%" && set "JOB_DATA_ROOT=%JOB_DATA_ROOT%" && python -m uvicorn --app-dir src app.main:app --port 8000 --reload"

@REM echo Starting Worker...
@REM start "Worker" cmd /k "cd /d "%PROJECT_ROOT%\worker" && set "INPUT_ROOT=%INPUT_ROOT%" && set "OUTPUT_ROOT=%OUTPUT_ROOT%" && set "JOB_DATA_ROOT=%JOB_DATA_ROOT%" && set "PYTHONPATH=src" && python -m worker.main"

@REM echo Starting Frontend...
@REM start "Frontend" cmd /k "cd /d "%PROJECT_ROOT%\frontend" && npm run dev"

echo All services launched.
