#!/bin/bash
npm run server &  # Starter frontend eller en annen server
gunicorn --bind 0.0.0.0:8080 app:app  # Starter Flask-appen
