import sys
import os

# Add the local src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'src'))

from PyFiles.GoogleKse import search_emails_and_display

if __name__ == "__main__":
    print("Starting email search WebJob...")
    try:
        result = search_emails_and_display()
        if result:
            print("Email search completed successfully")
        else:
            print("Email search encountered an issue")
    except Exception as e:
        print(f"Error in WebJob: {str(e)}")
        sys.exit(1) 