@echo off
echo Setting up WebJob environment...

REM Install Python dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir

echo WebJob environment setup complete
exit /b 0 