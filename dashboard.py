"""
Root Dashboard Launcher
Author: Derin Girish D G
Description: Unified entrypoint supporting direct Python execution (`python dashboard.py`)
and Streamlit Community Cloud deployment (`streamlit run dashboard.py`).
"""

import sys
from pathlib import Path

# Ensure root directory is on the module search path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

if __name__ == "__main__":
    try:
        import streamlit as st
        is_streamlit = st.runtime.exists()
    except Exception:
        is_streamlit = False

    if is_streamlit:
        # Running inside an active Streamlit server context (e.g. Streamlit Cloud)
        from src.dashboard.app import main
        main()
    else:
        # Launched directly via `python dashboard.py`
        import subprocess
        app_path = root_dir / "src" / "dashboard" / "app.py"
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])
