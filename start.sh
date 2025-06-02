#!/bin/bash
set -e

# Set default port if PORT is not defined
PORT=${PORT:-80}
echo "Using PORT: $PORT"

# Set up WebJobs directory
WEBJOBS_BASE_DIR=/app/App_Data/jobs/triggered
echo "Setting up WebJobs..."

# Process all WebJobs in the triggered directory
for WEBJOB_DIR in $WEBJOBS_BASE_DIR/*/; do
    if [ -d "$WEBJOB_DIR" ]; then
        echo "Processing WebJob in $WEBJOB_DIR"
        # Make all .sh and .cmd files executable
        find "$WEBJOB_DIR" -type f \( -name "*.sh" -o -name "*.cmd" \) -exec chmod +x {} \;
        # Convert line endings for Windows files
        find "$WEBJOB_DIR" -type f -name "*.cmd" -exec dos2unix {} \;
        echo "Made WebJob scripts executable in $WEBJOB_DIR"
    fi
done

# (Valgfritt) Oppdater Chromedriver hvis det er ndvendig
# python3 -c "import chromedriver_autoinstaller; chromedriver_autoinstaller.install()"

# Start backend (Flask via Gunicorn)
echo "Starting Flask application via Gunicorn..."
cd /app
exec gunicorn --workers 4 --bind 0.0.0.0:$PORT src.PyFiles.app:app --timeout 600

