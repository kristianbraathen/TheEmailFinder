#!/bin/bash
set -e

# Set default port if PORT is not defined
PORT=${PORT:-80}
echo "Using PORT: $PORT"

# Set up WebJobs directory
WEBJOBS_DIR=/app/App_Data/jobs/triggered/webjobemailsearch
echo "Setting up WebJobs..."
if [ -d "$WEBJOBS_DIR" ]; then
    echo "WebJobs directory found at $WEBJOBS_DIR"
    chmod +x $WEBJOBS_DIR/run.cmd
    chmod +x $WEBJOBS_DIR/setup.cmd
    echo "Made WebJob scripts executable"
else
    echo "Warning: WebJobs directory not found at $WEBJOBS_DIR"
fi

# (Valgfritt) Oppdater Chromedriver hvis det er ndvendig
# python3 -c "import chromedriver_autoinstaller; chromedriver_autoinstaller.install()"

# Start backend (Flask via Gunicorn)
echo "Starting Flask application via Gunicorn..."
cd /app
exec gunicorn --workers 4 --bind 0.0.0.0:$PORT src.PyFiles.app:app --timeout 600

