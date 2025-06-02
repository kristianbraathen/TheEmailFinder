import os
import sys
import datetime

def write_log(message):
    log_file = "/home/LogFiles/testjob.log"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def main():
    write_log("Test WebJob Starting")
    
    # Check environment variables
    write_log("Checking environment variables:")
    for var in ['WEBSITE_HOSTNAME', 'WEBSITE_SITE_NAME', 'WEBSITE_INSTANCE_ID', 
                'PYTHONPATH', 'DATABASE_CONNECTION_STRING', 'CHROMEDRIVER_PATH']:
        value = os.getenv(var, 'Not set')
        write_log(f"{var}: {value}")
    
    # Check Python path
    write_log("\nPython path:")
    for path in sys.path:
        write_log(f"- {path}")
    
    # Check current directory
    write_log(f"\nCurrent directory: {os.getcwd()}")
    write_log("Directory contents:")
    for item in os.listdir('.'):
        write_log(f"- {item}")
    
    write_log("Test WebJob Completed Successfully")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        write_log(f"Error in test job: {str(e)}")
        sys.exit(1) 