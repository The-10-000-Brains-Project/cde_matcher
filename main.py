"""
App Engine entry point for CDE Matcher Streamlit application.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main entry point for App Engine."""
    # Set up environment for Streamlit
    os.environ.setdefault('STREAMLIT_SERVER_PORT', '8080')
    os.environ.setdefault('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')
    os.environ.setdefault('STREAMLIT_SERVER_HEADLESS', 'true')
    os.environ.setdefault('STREAMLIT_BROWSER_GATHER_USAGE_STATS', 'false')

    # Path to the Streamlit app
    app_path = project_root / "ui" / "browser_app.py"

    # Build the command to run Streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(app_path),
        "--server.port", os.environ.get('STREAMLIT_SERVER_PORT', '8080'),
        "--server.address", os.environ.get('STREAMLIT_SERVER_ADDRESS', '0.0.0.0'),
        "--server.headless", os.environ.get('STREAMLIT_SERVER_HEADLESS', 'true'),
        "--browser.gatherUsageStats", os.environ.get('STREAMLIT_BROWSER_GATHER_USAGE_STATS', 'false'),
        "--server.fileWatcherType", "none"  # Disable file watching in production
    ]

    print(f"Starting Streamlit app: {' '.join(cmd)}")

    # Run Streamlit
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()