@echo off
echo [%date% %time%] Setting up WebJob environment...

REM Change to script directory
cd %~dp0
echo [%date% %time%] Current directory: %CD%

REM Ensure Python is available
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] Error: Python not found in PATH
    exit /b 1
)

REM Create log directory if it doesn't exist
if not exist logs mkdir logs

REM Install WebJob's Python dependencies
echo [%date% %time%] Installing WebJob dependencies...
if exist requirements.txt (
    python -m pip install --upgrade pip
    pip install -r requirements.txt --no-cache-dir
)

REM Install main app's Python dependencies
echo [%date% %time%] Installing main app dependencies...
if exist /app/src/PyFiles/requirements.txt (
    pip install -r /app/src/PyFiles/requirements.txt --no-cache-dir
)

echo [%date% %time%] WebJob environment setup complete
exit /b 0 