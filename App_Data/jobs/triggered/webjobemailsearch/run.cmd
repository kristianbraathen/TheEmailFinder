@echo off
echo Starting WebJob execution...

IF EXIST "%PYTHON_EXE%" (
    echo Using Python from: %PYTHON_EXE%
) ELSE (
    echo Python not found at %PYTHON_EXE%, using system Python
    set PYTHON_EXE=python
)

echo Current directory: %CD%
echo Directory contents:
dir

echo Running WebJob...
cd %~dp0
%PYTHON_EXE% run_email_search.py

IF %ERRORLEVEL% NEQ 0 (
    echo WebJob failed with error code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo WebJob completed successfully 