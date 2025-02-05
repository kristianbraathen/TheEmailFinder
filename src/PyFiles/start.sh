#!/bin/bash
set -e

# Start the frontend or another server
npm run server &

# Start the Flask app
gunicorn --bind 0.0.0.0:8080 app:app
