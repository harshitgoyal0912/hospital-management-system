#!/usr/bin/env python3
"""
Simple static file server for PDF reports
Serves files from the reports directory on port 3000
"""

import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse
from pathlib import Path

class ReportFileHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Set the directory to serve from
        self.reports_directory = Path(__file__).parent / "reports"
        super().__init__(*args, directory=str(self.reports_directory), **kwargs)
    
    def end_headers(self):
        # Add CORS headers to allow cross-origin requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        # Custom logging for clarity
        print(f"📁 [{self.address_string()}] {format % args}")

def start_pdf_server(port=3000):
    """Start the PDF file server"""
    server_address = ('', port)
    
    try:
        httpd = HTTPServer(server_address, ReportFileHandler)
        print(f"🚀 PDF Report Server starting on http://localhost:{port}")
        print(f"📂 Serving files from: {Path(__file__).parent / 'reports'}")
        print("📋 Available endpoints:")
        print(f"   • http://localhost:{port}/discharge/downloads/ - PDF downloads")
        print("   • Press Ctrl+C to stop")
        print("-" * 60)
        
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        httpd.server_close()
    except OSError as e:
        if e.errno == 10048:  # Port already in use
            print(f"❌ Port {port} is already in use. Please:")
            print("   1. Stop any other service using port 3000")
            print("   2. Or use a different port: python pdf_server.py --port 3001")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Static PDF Report Server')
    parser.add_argument('--port', type=int, default=3000, help='Port to serve on (default: 3000)')
    
    args = parser.parse_args()
    start_pdf_server(args.port)
