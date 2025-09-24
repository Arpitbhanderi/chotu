import subprocess
import os

# Go to your project directory
os.chdir(r"C:\Users\arpit\chotu")

# Path to Python inside your venv
venv_python = r"C:\Users\arpit\chotu\venv\Scripts\python.exe"

# Run waitress using venv's python
subprocess.run([venv_python, "-m", "waitress", "--port=8000", "app:app"])
