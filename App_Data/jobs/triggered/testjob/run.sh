#!/bin/bash

LOG_FILE="/home/LogFiles/testjob.log"
mkdir -p "$(dirname "$LOG_FILE")"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Test WebJob Starting" >> "$LOG_FILE"
echo "Hello World!" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Test WebJob Completed" >> "$LOG_FILE" 