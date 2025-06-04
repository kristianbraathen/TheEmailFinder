import sys
import os
import traceback
import datetime

# Add the local src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.append(src_path)

from PyFiles.app import app

def write_log(message):
    try:
        # Try multiple possible log locations
        log_locations = [
            os.path.join(os.getcwd(), "webjobemailsearch.log"),  # Local log first
            "webjobemailsearch.log",
            "/home/LogFiles/webjobemailsearch.log"  # Azure log last
        ]
        
        for log_file in log_locations:
            try:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(log_file, "a") as f:
                    f.write(f"[{timestamp}] {message}\n")
                print(f"Successfully wrote to {log_file}")
                return
            except Exception as e:
                print(f"Failed to write to {log_file}: {str(e)}")
                continue
    except Exception as e:
        print(f"Error in write_log: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")

try:
    # Print Python version and path
    write_log(f"Python version: {sys.version}")
    write_log(f"Python path: {sys.path}")
    write_log(f"Current directory: {os.getcwd()}")
    write_log(f"Directory contents: {os.listdir('.')}")

    # Check if src directory exists and list its contents
    if os.path.exists(src_path):
        write_log(f"src directory exists. Contents: {os.listdir(src_path)}")
        if os.path.exists(os.path.join(src_path, 'PyFiles')):
            write_log(f"PyFiles directory exists. Contents: {os.listdir(os.path.join(src_path, 'PyFiles'))}")
    else:
        write_log(f"src directory does not exist at {src_path}")

    # Try to import the modules
    write_log("Attempting to import modules...")
    from PyFiles.GoogleKse import GoogleKse
    from PyFiles.SearchResultHandler import search_emails_and_display
    write_log("Successfully imported modules")

    if __name__ == "__main__":
        write_log("Starting email search WebJob...")
        try:
            write_log("Creating GoogleKse instance...")
            search_provider = GoogleKse()
            write_log("Calling search_emails_and_display()...")
            
            # Create application context
            with app.app_context():
                result = search_emails_and_display(search_provider=search_provider)
                if result:
                    write_log("Email search completed successfully")
                else:
                    write_log("Email search encountered an issue")
        except Exception as e:
            error_msg = f"Error in WebJob: {str(e)}"
            write_log(error_msg)
            write_log(f"Traceback: {traceback.format_exc()}")
            sys.exit(1)

except Exception as e:
    error_msg = f"Critical error in WebJob: {str(e)}"
    write_log(error_msg)
    write_log(f"Traceback: {traceback.format_exc()}")
    sys.exit(1) 