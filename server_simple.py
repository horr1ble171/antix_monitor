#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import subprocess
from datetime import datetime

def get_stats():
    # Simple version compatible with AntiX/Linux
    try:
        cpu = os.popen("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1").read().strip()
        ram = os.popen("free -h | grep Mem | awk '{print $3\"/\"$2}'").read().strip()
        disk = os.popen("df -h / | tail -1 | awk '{print $3\"/\"$2}'").read().strip()
        uptime = os.popen("uptime -p").read().strip()
        ip = os.popen("hostname -I").read().strip()
        
        return {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'cpu': cpu if cpu else '0',
            'ram': ram,
            'disk': disk,
            'uptime': uptime,
            'ip': ip
        }
    except Exception as e:
        return {'error': str(e)}

# Load index.html once at startup
try:
    with open('index.html', 'r', encoding='utf-8') as f:
        HTML_CONTENT = f.read()
except FileNotFoundError:
    HTML_CONTENT = '<h1>index.html not found</h1>'

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode('utf-8'))
        elif self.path == '/api/stats':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_stats()).encode('utf-8'))
        elif self.path == '/api/processes':
            # Stub for processes
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps([]).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    port = 8080
    print(f"🚀 Монитор запущен на http://0.0.0.0:{port}")
    try:
        HTTPServer(('0.0.0.0', port), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
