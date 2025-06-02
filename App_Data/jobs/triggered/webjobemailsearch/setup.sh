#!/bin/bash

# Ensure script fails on any error
set -e

LOG_FILE="/home/LogFiles/webjob-setup.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Setting up WebJob environment..."

# Change to script directory
cd "$(dirname "$0")"
log "Current directory: $PWD"

# Create log directory if it doesn't exist
mkdir -p logs
log "Created logs directory"

# Activate Python virtual environment if it exists
if [ -d "/home/site/wwwroot/env" ]; then
    source /home/site/wwwroot/env/bin/activate
    log "Activated Python virtual environment"
fi

# Install Python dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    log "Installing Python dependencies..."
    pip install --no-cache-dir -r requirements.txt >> "$LOG_FILE" 2>&1
    log "Python dependencies installed"
fi

# Make run.sh executable
chmod +x run.sh
log "Made run.sh executable"

log "WebJob environment setup complete"
exit 0 