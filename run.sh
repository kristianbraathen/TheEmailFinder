#!/bin/bash

# Activate Python virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the Python script
python3 run.py 