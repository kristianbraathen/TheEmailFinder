#!/bin/bash
set -e

# Bygg frontend
npm install
npm run build
# Flytt bygde filer til backend for å serve dem med Flask
mv dist /app/static

# Oppdater Chromedriver
python -c "import chromedriver_autoinstaller; chromedriver_autoinstaller.install()"

# Start backend (Gunicorn)
gunicorn --bind 0.0.0.0:8080 app:app
