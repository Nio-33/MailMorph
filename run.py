#!/usr/bin/env python3
"""
MailMorph - Development Server
Run this script to start the Flask development server
"""

import os
import sys
from app import app

if __name__ == '__main__':
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Print startup information
    print("🚀 Starting MailMorph Development Server...")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python version: {sys.version}")
    print("=" * 50)
    print("📧 MailMorph - Email Domain Replacer Tool")
    print("🌐 Access the application at: http://localhost:5001")
    print("🔧 Debug mode: ON")
    print("=" * 50)
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        # Start the Flask development server
        app.run(
            host='0.0.0.0',  # Listen on all interfaces
            port=5001,       # Port 5001 (avoiding conflicts)
            debug=True,      # Enable debug mode
            use_reloader=True,  # Auto-reload on file changes
            use_debugger=True,  # Enable debugger
            threaded=True    # Handle multiple requests
        )
    except KeyboardInterrupt:
        print("\n👋 MailMorph server stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)