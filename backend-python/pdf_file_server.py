#!/usr/bin/env python3
"""
Simple HTTP server to serve PDF files from the reports directory.
This server provides CORS-enabled access to generated PDF files.
"""

import os
import http.server
import socketserver
from urllib.parse import urlparse, unquote
import mimetypes
from pathlib import Path

class PDFFileHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.reports_root = Path(__file__).parent / "reports"
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests for PDF files."""
        try:
            # Parse the URL path
            parsed_path = urlparse(self.path)
            path = unquote(parsed_path.path)
            
            # Security: Only allow access to files within the reports directory
            if not path.startswith('/reports/'):
                self.send_error(404, "File not found")
                return
            
            # Convert URL path to file system path
            relative_path = path[1:]  # Remove leading /
            file_path = self.reports_root.parent / relative_path
            
            # Check if file exists and is within allowed directory
            if not file_path.exists():
                self.send_error(404, "File not found")
                return
                
            if not str(file_path.resolve()).startswith(str(self.reports_root.parent.resolve())):
                self.send_error(403, "Access denied")
                return
            
            # Read and serve the file
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type is None:
                if file_path.suffix.lower() == '.pdf':
                    mime_type = 'application/pdf'
                else:
                    mime_type = 'application/octet-stream'
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', mime_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            self.wfile.write(content)
            
            print(f"✅ Served file: {file_path} ({len(content):,} bytes)")
            
        except Exception as e:
            print(f"❌ Error serving file: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override to provide cleaner logging."""
        print(f"📁 File Server: {format % args}")

def start_pdf_server(port=3001):
    """Start the PDF file server."""
    try:
        os.chdir(Path(__file__).parent)
        
        with socketserver.TCPServer(("", port), PDFFileHandler) as httpd:
            print(f"🚀 PDF File Server starting on http://localhost:{port}")
            print(f"📁 Serving files from: {Path(__file__).parent / 'reports'}")
            print(f"🌐 CORS enabled for cross-origin requests")
            print(f"📋 Access PDFs at: http://localhost:{port}/reports/discharge/downloads/[filename].pdf")
            print(f"⏹️  Press Ctrl+C to stop the server\n")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n🛑 PDF File Server stopped")
    except Exception as e:
        print(f"❌ Failed to start PDF server: {e}")

if __name__ == "__main__":
    start_pdf_server()
