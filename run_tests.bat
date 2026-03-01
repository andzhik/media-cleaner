@echo off
SET "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" SET "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

SET FAILED=0

echo ============================================================
echo  Backend tests
echo ============================================================
cd /d "%PROJECT_ROOT%\backend"
python -m pytest %*
if errorlevel 1 SET FAILED=1

echo.
echo ============================================================
echo  Worker tests
echo ============================================================
cd /d "%PROJECT_ROOT%\worker"
python -m pytest %*
if errorlevel 1 SET FAILED=1

echo.
if %FAILED%==0 (
    echo All tests passed.
) else (
    echo One or more test suites failed.
    exit /b 1
)
