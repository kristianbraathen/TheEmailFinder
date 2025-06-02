@echo off
echo [%date% %time%] Starting WebJob execution... >> D:\home\LogFiles\webjob.log 2>&1

REM Change to script directory
cd %~dp0
echo [%date% %time%] Current directory: %CD% >> D:\home\LogFiles\webjob.log 2>&1

REM Set PYTHONPATH to include both the WebJob's Python files and the app's Python files
set PYTHONPATH=%CD%\src\PyFiles;/app/src/PyFiles;%PYTHONPATH%
echo [%date% %time%] PYTHONPATH: %PYTHONPATH% >> D:\home\LogFiles\webjob.log 2>&1

REM Run Python script with output redirection
echo [%date% %time%] Running Python script... >> D:\home\LogFiles\webjob.log 2>&1
python run_email_search.py >> D:\home\LogFiles\webjob.log 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] Python script failed with error code %ERRORLEVEL% >> D:\home\LogFiles\webjob.log 2>&1
    exit /b %ERRORLEVEL%
)

echo [%date% %time%] Python script completed successfully >> D:\home\LogFiles\webjob.log 2>&1 