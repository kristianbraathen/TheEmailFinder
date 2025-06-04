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
        
        # Create WebJob registration file if it doesn't exist
        if [ ! -f "$WEBJOB_DIR/webjob-publish-settings.json" ]; then
            WEBJOB_NAME=$(basename "$WEBJOB_DIR")
            cat > "$WEBJOB_DIR/webjob-publish-settings.json" << EOF
{
    "webjob_name": "$WEBJOB_NAME",
    "webjob_type": "triggered",
    "webjob_url": "https://\$WEBSITE_HOSTNAME.scm.azurewebsites.net/api/triggeredwebjobs/$WEBJOB_NAME",
    "webjob_script_file": "run.sh",
    "webjob_script_arguments": "",
    "webjob_script_environment": {
        "WEBSITE_HOSTNAME": "\$WEBSITE_HOSTNAME",
        "WEBSITE_SITE_NAME": "\$WEBSITE_SITE_NAME",
        "WEBSITE_INSTANCE_ID": "\$WEBSITE_INSTANCE_ID"
    }
}
EOF
        fi
        
        echo "Made WebJob scripts executable in $WEBJOB_DIR"
fi
done

# (Valgfritt) Oppdater Chromedriver hvis det er ndvendig
# python3 -c "import chromedriver_autoinstaller; chromedriver_autoinstaller.install()"

# Start backend (Flask via Gunicorn)
echo "Starting Flask application via Gunicorn..."
cd /app
exec gunicorn --workers 4 --bind 0.0.0.0:$PORT src.PyFiles.app:app --timeout 600

