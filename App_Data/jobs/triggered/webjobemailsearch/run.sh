#!/bin/bash

# Ensure script fails on any error
set -e

LOG_FILE="/home/LogFiles/webjob.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting WebJob execution..."

# Change to script directory
cd "$(dirname "$0")"
log "Current directory: $PWD"

# Set up Python environment
export PYTHONPATH="$PWD/src/PyFiles:/home/site/wwwroot/src/PyFiles:$PYTHONPATH"
log "PYTHONPATH: $PYTHONPATH"

# Activate Python virtual environment if it exists
if [ -d "/home/site/wwwroot/env" ]; then
    source /home/site/wwwroot/env/bin/activate
    log "Activated Python virtual environment"
fi

# Run Python script
log "Running Python script..."
if python3 run.py >> "$LOG_FILE" 2>&1; then
    log "Python script completed successfully"
    exit 0
else
    EXIT_CODE=$?
    log "Python script failed with error code $EXIT_CODE"
    exit $EXIT_CODE
fi

# Deactivate virtual environment if it was activated
if [ -d "/home/site/wwwroot/env" ]; then
    deactivate
fi 