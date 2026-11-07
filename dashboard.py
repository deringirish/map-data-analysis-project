"""
Root Dashboard Launcher
Executes the interactive Streamlit BI application.
"""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    app_path = Path(__file__).resolve().parent / "src" / "dashboard" / "app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])
