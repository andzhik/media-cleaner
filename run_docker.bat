@echo off
SET "PROJECT_ROOT=%~dp0"
REM Remove trailing backslash if present.
if "%PROJECT_ROOT:~-1%"=="\" SET "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

SET "INPUT_ROOT=%PROJECT_ROOT%\mnt\input"
SET "OUTPUT_ROOT=%PROJECT_ROOT%\mnt\output"
SET "JOB_DATA_ROOT=%PROJECT_ROOT%\mnt\job-data"

if not exist "%INPUT_ROOT%" mkdir "%INPUT_ROOT%"
if not exist "%OUTPUT_ROOT%" mkdir "%OUTPUT_ROOT%"
if not exist "%JOB_DATA_ROOT%" mkdir "%JOB_DATA_ROOT%"

echo Starting Docker services...
cd /d "%PROJECT_ROOT%"
docker compose up --build

if errorlevel 1 (
  echo Docker Compose exited with an error.
  pause
)
