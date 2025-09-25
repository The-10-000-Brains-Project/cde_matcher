"""
Main entry point for CDE Matcher application.

Supports both local development and cloud deployment with command-line arguments.
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path

# Import configuration
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cde_matcher.core.config import config

def setup_environment(local_mode: bool = False):
    """Set up environment variables based on mode."""
    global config

    if local_mode:
        os.environ['CDE_LOCAL_MODE'] = 'true'
        print("Running in LOCAL mode - using local data directories")
    else:
        os.environ['CDE_LOCAL_MODE'] = 'false'
        print(f"Running in CLOUD mode - using GCS bucket: {config.gcs_bucket}")

    # Reload config to pick up environment changes
    from cde_matcher.core.config import Config
    config = Config()


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description='CDE Matcher - Match variable names to Common Data Elements')
    parser.add_argument('--local', action='store_true',
                       help='Use local data paths instead of GCS bucket')
    parser.add_argument('--port', type=int,
                       default=config.port,
                       help=f'Port for Streamlit server (default: {config.port})')

    # Parse known args to handle Streamlit's own arguments
    args, unknown_args = parser.parse_known_args()

    # Set up environment
    setup_environment(args.local)


    # Prepare Streamlit command
    streamlit_args = [
        'streamlit', 'run', 'ui/browser_app.py',
        '--server.port', str(args.port),
        '--server.address', '0.0.0.0'
    ]

    # Add App Engine specific settings if not local
    if not args.local:
        streamlit_args.extend([
            '--server.enableCORS', 'false',
            '--server.enableXsrfProtection', 'false',
            '--server.enableWebsocketCompression', 'false'
        ])

    # Add any unknown arguments to Streamlit
    if unknown_args:
        streamlit_args.extend(unknown_args)

    # Change to the directory containing this script
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)

    print(f"🚀 Starting CDE Matcher...")
    print(f"📍 Working directory: {os.getcwd()}")
    print(f"🌐 Server will be available at: http://localhost:{args.port}")

    try:
        # Run Streamlit
        subprocess.run(streamlit_args, check=True)
    except KeyboardInterrupt:
        print("\n👋 CDE Matcher stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()