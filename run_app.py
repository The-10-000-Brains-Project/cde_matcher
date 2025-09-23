#!/usr/bin/env python3
"""
CDE Matcher Application Launcher

This script launches the CDE Matcher Streamlit application with proper configuration
for either GCS or local storage.

Usage:
    python run_app.py                 # Use GCS bucket 'pathnd_cdes' (default)
    python run_app.py --local         # Use local data directories
    python run_app.py --bucket my-bucket  # Use custom GCS bucket
    python run_app.py --help          # Show help

Environment Variables:
    GCS_BUCKET_NAME: Override default bucket name
    GCP_PROJECT_ID: Set GCP project ID
    GOOGLE_APPLICATION_CREDENTIALS: Path to service account key
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path


def setup_environment(args):
    """Set up environment variables based on arguments."""
    if args.local:
        # Force local storage by removing GCS environment variables
        if 'GCS_BUCKET_NAME' in os.environ:
            del os.environ['GCS_BUCKET_NAME']
        print("🏠 Using local storage mode")
        print(f"📁 Data directory: {os.path.abspath('data')}/")
    else:
        # Set up GCS configuration
        bucket_name = args.bucket or os.getenv('GCS_BUCKET_NAME', 'pathnd_cdes')
        os.environ['GCS_BUCKET_NAME'] = bucket_name

        if args.project:
            os.environ['GCP_PROJECT_ID'] = args.project

        print(f"☁️  Using Google Cloud Storage")
        print(f"🪣 Bucket: gs://{bucket_name}/")

        # Check for authentication
        if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            print("💡 Tip: Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
            print("   or run 'gcloud auth application-default login' for authentication")


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import streamlit
        print(f"✅ Streamlit {streamlit.__version__}")
    except ImportError:
        print("❌ Streamlit not found. Install with: pip install streamlit")
        return False

    try:
        import pandas
        print(f"✅ Pandas {pandas.__version__}")
    except ImportError:
        print("❌ Pandas not found. Install with: pip install pandas")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Launch CDE Matcher with configurable storage backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    storage_group = parser.add_mutually_exclusive_group()
    storage_group.add_argument(
        '--local',
        action='store_true',
        help='Use local data directories instead of GCS'
    )
    storage_group.add_argument(
        '--bucket',
        type=str,
        help='GCS bucket name (default: pathnd_cdes)'
    )

    parser.add_argument(
        '--project',
        type=str,
        help='GCP project ID'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=8501,
        help='Streamlit port (default: 8501)'
    )

    parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='Streamlit host (default: localhost)'
    )

    args = parser.parse_args()

    print("🚀 CDE Matcher Application Launcher")
    print("=" * 40)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Set up environment
    setup_environment(args)

    # Check if browser app exists
    app_path = Path(__file__).parent / "ui" / "browser_app.py"
    if not app_path.exists():
        print(f"❌ Browser app not found at: {app_path}")
        sys.exit(1)

    # Prepare streamlit command
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.port", str(args.port),
        "--server.address", args.host,
        "--server.headless", "true",
        "--server.fileWatcherType", "none",
        "--browser.gatherUsageStats", "false"
    ]

    # Add any additional arguments to pass to the app
    if args.local:
        cmd.append("--local")

    print(f"🌐 Starting application at: http://{args.host}:{args.port}")
    print("=" * 40)

    try:
        # Run streamlit
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()