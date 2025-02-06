#!/bin/bash
set -e

# Bygg frontend
cd /app/frontend
npm install
npm run build
# Flytt bygde filer til backend for å serve dem med Flask
mv dist /app/backend/static

# Start backend (Gunicorn)
cd /app/backend
gunicorn --bind 0.0.0.0:8080 app:app
