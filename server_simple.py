#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import subprocess
from datetime import datetime

def get_cpu_freq():
    try:
        # Try from /proc/cpuinfo
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if 'cpu MHz' in line:
                    return f"{float(line.split(':')[1].strip()):.0f} MHz"
    except:
        pass
    return "N/A"

def get_temperature():
    try:
        # Try primary thermal zone
        if os.path.exists('/sys/class/thermal/thermal_zone0/temp'):
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = int(f.read().strip()) / 1000
                return f"{temp:.1f}°C"
        # Try fallback via sensors
        temp = os.popen("sensors 2>/dev/null | grep 'Core 0' | awk '{print $3}'").read().strip()
        if temp:
            return temp
    except:
        pass
    return "N/A"

def get_network_stats():
    try:
        with open('/proc/net/dev', 'r') as f:
            lines = f.readlines()
        # Look for active interface (wlan0, eth0, enp...)
        for line in lines:
            if ':' in line and not 'lo' in line:
                parts = line.split()
                # Parts[0] is "interface:", parts[1] is recv bytes, parts[9] is sent bytes
                # Standard format has at least 10 parts for interface + metrics
                if len(parts) >= 10:
                    recv_bytes = int(parts[1])
                    sent_bytes = int(parts[9])
                    return f"{sent_bytes / (1024**2):.1f} MB", f"{recv_bytes / (1024**2):.1f} MB"
    except:
        pass
    return "-", "-"

def get_stats():
    try:
        cpu = os.popen("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1").read().strip()
        # Get RAM: used/total/free
        ram = os.popen("free -h | grep Mem | awk '{print $3\"/\"$2\"/\"$4}'").read().strip()
        # Get RAM percentage separately
        ram_pct = os.popen("free | grep Mem | awk '{print $3/$2 * 100.0}'").read().strip()
        
        # Get Disk: used/total/free
        disk = os.popen("df -h / | tail -1 | awk '{print $3\"/\"$2\"/\"$4}'").read().strip()
        uptime = os.popen("uptime -p").read().strip()
        ip = os.popen("hostname -I").read().strip()
        
        disk_pct = 0
        try:
            disk_pct = int(os.popen("df / | tail -1 | awk '{print $5}' | sed 's/%//'").read().strip())
        except: pass

        net_sent, net_recv = get_network_stats()

        return {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'cpu_percent': cpu if cpu else '0',
            'ram_used': ram.split('/')[0] if '/' in ram else ram,
            'ram_total': ram.split('/')[1] if '/' in ram else '',
            'ram_free': ram.split('/')[2] if len(ram.split('/')) > 2 else '',
            'ram_percent': ram_pct if ram_pct else '0',
            'disk_used': disk.split('/')[0] if '/' in disk else disk,
            'disk_total': disk.split('/')[1] if '/' in disk else '',
            'disk_free': disk.split('/')[2] if len(disk.split('/')) > 2 else '',
            'disk_percent': disk_pct,
            'uptime': uptime,
            'ip': ip,
            'processes': os.popen("ps ax | wc -l").read().strip(),
            'cpu_freq': get_cpu_freq(),
            'cpu_cores': os.cpu_count() or 1,
            'load_1m': os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0,
            'load_5m': os.getloadavg()[1] if hasattr(os, 'getloadavg') else 0,
            'load_15m': os.getloadavg()[2] if hasattr(os, 'getloadavg') else 0,
            'net_sent': net_sent,
            'net_recv': net_recv,
            'temperature': get_temperature()
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
            # Fix: exclude ps aux itself
            ps = os.popen("ps aux --sort=-%cpu | grep -v 'ps aux' | head -6 | tail -5").read()
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
