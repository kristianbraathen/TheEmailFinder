#!/bin/bash
set -e

# Sett standardport hvis PORT ikke er definert
PORT=${PORT:-8080}
echo "Using PORT: $PORT"

# Oppdater Chromedriver
python -c "import chromedriver_autoinstaller; chromedriver_autoinstaller.install()"

# Start backend (Flask via Gunicorn)
cd /app
exec gunicorn --bind 0.0.0.0:$PORT  src.PyFiles.app:app
