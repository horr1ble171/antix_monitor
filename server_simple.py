#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import subprocess
from datetime import datetime

def get_stats():
    try:
        cpu = os.popen("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1").read().strip()
        ram = os.popen("free -h | grep Mem | awk '{print $3\"/\"$2}'").read().strip()
        disk = os.popen("df -h / | tail -1 | awk '{print $3\"/\"$2}'").read().strip()
        uptime = os.popen("uptime -p").read().strip()
        ip = os.popen("hostname -I").read().strip()
        
        # Calculate disk percent for progress bar
        disk_pct = 0
        try:
            disk_pct = int(os.popen("df / | tail -1 | awk '{print $5}' | sed 's/%//'").read().strip())
        except: pass

        return {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'cpu_percent': cpu if cpu else '0',
            'ram_used': ram.split('/')[0] if '/' in ram else ram,
            'ram_total': ram.split('/')[1] if '/' in ram else '',
            'disk_used': disk.split('/')[0] if '/' in disk else disk,
            'disk_total': disk.split('/')[1] if '/' in disk else '',
            'disk_percent': disk_pct,
            'uptime': uptime,
            'ip': ip,
            'processes': os.popen("ps ax | wc -l").read().strip(),
            'cpu_freq': 'N/A',
            'cpu_cores': os.cpu_count() or 1,
            'load_1m': os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0,
            'load_5m': os.getloadavg()[1] if hasattr(os, 'getloadavg') else 0,
            'load_15m': os.getloadavg()[2] if hasattr(os, 'getloadavg') else 0,
            'net_sent': '-',
            'net_recv': '-',
            'temperature': 'N/A'
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
            ps = os.popen("ps aux --sort=-%cpu | head -6 | tail -5").read()
            procs = []
            for line in ps.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) > 10:
                        procs.append({
                            'pid': parts[1],
                            'name': ' '.join(parts[10:]),
                            'cpu_percent': parts[2],
                            'memory_percent': float(parts[3]) if parts[3].replace('.','',1).isdigit() else 0
                        })
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(procs).encode('utf-8'))
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
