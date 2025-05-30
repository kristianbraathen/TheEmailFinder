import os
import sys
import datetime

# Write to a log file in the same directory as this script
log_file = os.path.join(os.path.dirname(__file__), "test_webjob.log")

def write_log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

try:
    write_log("Starting test WebJob")
    write_log(f"Python version: {sys.version}")
    write_log(f"Current directory: {os.getcwd()}")
    write_log(f"Script location: {os.path.dirname(__file__)}")
    write_log(f"Directory contents: {os.listdir(os.path.dirname(__file__))}")
    write_log(f"Environment variables: {dict(os.environ)}")
    write_log("Test WebJob completed successfully")
except Exception as e:
    write_log(f"Error occurred: {str(e)}")
    raise 