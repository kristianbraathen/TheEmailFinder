#!/bin/bash
set -e

# Set default port if PORT is not defined
PORT=${PORT:-80}
echo "Using PORT: $PORT"

# Function to start the Flask app
start_flask_app() {
    echo "Starting Flask application via Gunicorn..."
    cd /app
    gunicorn --workers 4 --bind 0.0.0.0:$PORT src.PyFiles.app:app --timeout 600 &
    GUNICORN_PID=$!
    echo "Gunicorn started with PID: $GUNICORN_PID"
}

# Function to handle WebJobs
setup_webjobs() {
    WEBJOBS_DIR=/app/App_Data/jobs/triggered/webjobemailsearch
    echo "Setting up WebJobs..."
    if [ -d "$WEBJOBS_DIR" ]; then
        echo "WebJobs directory found at $WEBJOBS_DIR"
        chmod +x $WEBJOBS_DIR/run.cmd
        chmod +x $WEBJOBS_DIR/setup.cmd
        echo "Made WebJob scripts executable"
        
        # Run setup if it hasn't been run yet
        if [ ! -f "$WEBJOBS_DIR/.setup_complete" ]; then
            echo "Running WebJob setup..."
            cd $WEBJOBS_DIR
            ./setup.cmd
            touch .setup_complete
            cd /app
        fi
    else
        echo "Warning: WebJobs directory not found at $WEBJOBS_DIR"
    fi
}

# Function to handle signals
handle_signal() {
    echo "Received signal to terminate..."
    if [ ! -z "$GUNICORN_PID" ]; then
        echo "Stopping Gunicorn (PID: $GUNICORN_PID)..."
        kill -TERM "$GUNICORN_PID"
    fi
    exit 0
}

# Set up signal handling
trap handle_signal SIGTERM SIGINT

# Set up environment
export PYTHONPATH=/app/src/PyFiles:/app/App_Data/jobs/triggered/webjobemailsearch/src/PyFiles

# Set up WebJobs
setup_webjobs

# Start the Flask app
start_flask_app

# Keep the container running
echo "Container is running..."
while true; do
    if ! kill -0 "$GUNICORN_PID" 2>/dev/null; then
        echo "Gunicorn process died, restarting..."
        start_flask_app
    fi
    sleep 10
done

