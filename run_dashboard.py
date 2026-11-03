"""
1-Click Master Application Runner for MAP Compliance Streamlit BI Dashboard
Author: Derin Girish
Usage: python run_dashboard.py
"""

import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def main():
    print("=" * 65)
    print("   ⚖️  MAP COMPLIANCE & BRAND PROTECTION BI DASHBOARD")
    print("   Interactive Executive Analytics & Reseller Surveillance")
    print("=" * 65)
    print("\n[STARTUP] Launching Streamlit Interactive Dashboard Server...")

    dashboard_script = BASE_DIR / "dashboard.py"
    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(dashboard_script), "--server.headless=true"],
            check=True,
        )
    except KeyboardInterrupt:
        print("\n[STOP] Dashboard stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Failed to run dashboard: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
