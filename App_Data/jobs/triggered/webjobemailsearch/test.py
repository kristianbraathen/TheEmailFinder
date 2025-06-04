import sys
import os
import traceback
from datetime import datetime

def test_webjob():
    try:
        # Add the src directory to Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_path = os.path.join(current_dir, 'src')
        sys.path.append(src_path)
        print(f"Added to Python path: {src_path}")

        # Print all Python paths
        print("\nPython paths:")
        for path in sys.path:
            print(f"- {path}")

        # Check if PyFiles directory exists
        pyfiles_path = os.path.join(src_path, 'PyFiles')
        if os.path.exists(pyfiles_path):
            print(f"\nPyFiles directory exists at: {pyfiles_path}")
            print("Contents of PyFiles:")
            for item in os.listdir(pyfiles_path):
                print(f"- {item}")
        else:
            print(f"\nERROR: PyFiles directory not found at: {pyfiles_path}")
            return False

        print("\nAttempting to import modules...")
        try:
            from PyFiles.app import app
            print("Successfully imported app")
        except Exception as e:
            print(f"Failed to import app: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return False

        try:
            from PyFiles.GoogleKse import GoogleKse
            print("Successfully imported GoogleKse")
        except Exception as e:
            print(f"Failed to import GoogleKse: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return False

        try:
            from PyFiles.SearchResultHandler import search_emails_and_display
            print("Successfully imported search_emails_and_display")
        except Exception as e:
            print(f"Failed to import search_emails_and_display: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return False

        print("\nStarting test...")
        print(f"Python version: {sys.version}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Directory contents: {os.listdir('.')}")

        # Test database connection
        print("\nTesting database connection...")
        with app.app_context():
            try:
                from PyFiles.Db import db
                from sqlalchemy import text
                db.session.execute(text("SELECT 1"))
                print("Database connection successful!")
            except Exception as e:
                print(f"Database connection failed: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                return False

            # Test GoogleKse initialization
            print("\nTesting GoogleKse initialization...")
            try:
                search_provider = GoogleKse()
                print("GoogleKse initialization successful!")
            except Exception as e:
                print(f"GoogleKse initialization failed: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                return False

            # Test search_emails_and_display
            print("\nTesting search_emails_and_display...")
            try:
                result = search_emails_and_display(search_provider=search_provider)
                print(f"search_emails_and_display result: {result}")
                return True
            except Exception as e:
                print(f"search_emails_and_display failed: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                return False

    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_webjob()
    sys.exit(0 if success else 1) 