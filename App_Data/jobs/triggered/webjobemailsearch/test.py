import sys
import os
import time

print("TEST SCRIPT STARTING", flush=True)
print(f"Python Version: {sys.version}", flush=True)
print(f"Current Directory: {os.getcwd()}", flush=True)
print(f"Directory Contents: {os.listdir()}", flush=True)

# Write to a file to verify file system access
with open("test_output.txt", "w") as f:
    f.write("Test successful\n")

print("TEST SCRIPT COMPLETED", flush=True) 