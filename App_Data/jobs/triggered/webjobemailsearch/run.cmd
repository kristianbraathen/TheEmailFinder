@echo on
echo Current directory: %CD%
echo Python path: %PATH%
echo Listing directory contents:
dir
echo.
echo Running Python script...
python -V
python run_email_search.py 2>> webjob_error.log
if %ERRORLEVEL% NEQ 0 (
    echo Error running script. Check webjob_error.log for details.
    exit /b %ERRORLEVEL%
) 
python test_run.py > webjob.log 2>&1 