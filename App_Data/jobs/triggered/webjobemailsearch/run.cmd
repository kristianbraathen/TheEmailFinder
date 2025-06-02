@echo off
echo [%date% %time%] Starting WebJob execution...

REM Change to script directory
cd %~dp0
echo [%date% %time%] Current directory: %CD%

REM Ensure PYTHONPATH includes our src directory
set PYTHONPATH=%CD%\src\PyFiles;%PYTHONPATH%
echo [%date% %time%] PYTHONPATH: %PYTHONPATH%

REM Run Python script with output redirection
echo [%date% %time%] Running Python script...
python run_email_search.py 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] Python script failed with error code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo [%date% %time%] Python script completed successfully 