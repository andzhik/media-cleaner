@echo off
SET "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" SET "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

SET FAILED=0

echo ============================================================
echo  Backend + Worker lint (ruff)
echo ============================================================
cd /d "%PROJECT_ROOT%"
python -m ruff check --fix .
if errorlevel 1 SET FAILED=1

echo.
echo ============================================================
echo  Frontend lint (eslint)
echo ============================================================
cd /d "%PROJECT_ROOT%\frontend"
npm run lint:fix
if errorlevel 1 SET FAILED=1

echo.
if %FAILED%==0 (
    echo All lint checks passed.
) else (
    echo One or more lint checks failed.
    exit /b 1
)
