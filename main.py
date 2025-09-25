"""
Main entry point for CDE Matcher application.

Supports both local development and cloud deployment with command-line arguments.
"""

import argparse
import os
import sys
import subprocess
import threading
import time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

def setup_environment(local_mode: bool = False):
    """Set up environment variables based on mode."""
    if local_mode:
        os.environ['CDE_LOCAL_MODE'] = 'true'
        print("🏠 Running in LOCAL mode - using local data directories")
    else:
        os.environ['CDE_LOCAL_MODE'] = 'false'
        bucket = os.getenv('CDE_GCS_BUCKET', 'pathnd_cdes')
        print(f"☁️  Running in CLOUD mode - using GCS bucket: {bucket}")

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple health check handler for App Engine."""

    def do_GET(self):
        if self.path == '/healthz':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default logging
        pass

def start_health_check_server(port: int = 8080):
    """Start a simple health check server for App Engine."""
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        server.serve_forever()
    except Exception as e:
        print(f"Health check server error: {e}")

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description='CDE Matcher - Match variable names to Common Data Elements')
    parser.add_argument('--local', action='store_true',
                       help='Use local data paths instead of GCS bucket')
    parser.add_argument('--port', type=int,
                       default=int(os.getenv('PORT', '8080')),
                       help='Port for Streamlit server (default: 8080, or $PORT if set)')

    # Parse known args to handle Streamlit's own arguments
    args, unknown_args = parser.parse_known_args()

    # Set up environment
    setup_environment(args.local)

    # Start health check server in background for App Engine
    if not args.local and os.getenv('GAE_ENV'):
        health_thread = threading.Thread(
            target=start_health_check_server,
            args=(8080,),
            daemon=True
        )
        health_thread.start()
        print("🏥 Started health check server on port 8080")

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