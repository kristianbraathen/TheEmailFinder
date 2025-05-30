import os
import datetime

# Simple log file in the same directory
log_file = os.path.join(os.path.dirname(__file__), "test.log")

# Write a simple message
with open(log_file, "a") as f:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    f.write(f"[{timestamp}] Test WebJob ran successfully\n")
    f.write(f"Current directory: {os.getcwd()}\n")
    f.write(f"Directory contents: {os.listdir('.')}\n") 