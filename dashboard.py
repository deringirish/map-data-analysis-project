"""
Root Dashboard Launcher
Supports both direct Python execution (`python dashboard.py`) and
Streamlit Community Cloud deployment (`streamlit run dashboard.py`).
"""

import sys
from pathlib import Path

# Ensure root directory is on the module search path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import streamlit as st
from src.dashboard.app import main

if __name__ == "__main__":
    # If already running inside a Streamlit runner (e.g. Streamlit Community Cloud)
    if st.runtime.exists():
        main()
    else:
        # Launched directly via `python dashboard.py`
        import subprocess
        app_path = root_dir / "src" / "dashboard" / "app.py"
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])
