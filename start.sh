#!/bin/bash
set -e

# Sett standardport hvis PORT ikke er definert
PORT=${PORT:-80}
echo "Using PORT: $PORT"

# Opprett /temp-mappen (om nødvendig) og sett riktige rettigheter
mkdir -p /app/temp
chmod -R 777 /app/temp

echo "Temp folder created and permissions set."

# (Valgfritt) Oppdater Chromedriver hvis det er nødvendig
# python3 -c "import chromedriver_autoinstaller; chromedriver_autoinstaller.install()"

# Start backend (Flask via Gunicorn)
echo "Starting Flask application via Gunicorn..."
cd /app
exec gunicorn --bind 0.0.0.0:$PORT src.PyFiles.app:app --timeout 120
