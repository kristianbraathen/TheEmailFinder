@echo on
echo Installing Python requirements...
python -m pip install -r requirements.txt --no-cache-dir
if %ERRORLEVEL% NEQ 0 (
    echo Error installing requirements
    exit /b %ERRORLEVEL%
)
echo Requirements installed successfully 