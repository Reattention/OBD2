#!/usr/bin/env python3
"""
BMW OBD2 Bluetooth Diagnosticator
Designed for BMW 640D F13 RWD with Glassmorphism UI
"""

import http.server
import socketserver
import json
import threading
import time
import random
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import os

class BMWDiagnostics:
    def __init__(self):
        self.is_connected = False
        self.data_thread = None
        self.running = False
        
        # BMW 640D F13 specific parameters with demo data
        self.bmw_pids = {
            'engine_load': {'min': 0, 'max': 100, 'unit': '%', 'current': 45},
            'coolant_temp': {'min': 70, 'max': 110, 'unit': '°C', 'current': 88},
            'rpm': {'min': 600, 'max': 6000, 'unit': 'rpm', 'current': 1800},
            'speed': {'min': 0, 'max': 200, 'unit': 'km/h', 'current': 65},
            'intake_temp': {'min': 15, 'max': 70, 'unit': '°C', 'current': 35},
            'maf': {'min': 0, 'max': 200, 'unit': 'g/s', 'current': 25.6},
            'throttle_pos': {'min': 0, 'max': 100, 'unit': '%', 'current': 15},
            'fuel_pressure': {'min': 0, 'max': 400, 'unit': 'kPa', 'current': 280},
            'intake_pressure': {'min': 90, 'max': 250, 'unit': 'kPa', 'current': 105},
            'timing_advance': {'min': -10, 'max': 50, 'unit': '°', 'current': 12.5},
            'fuel_level': {'min': 0, 'max': 100, 'unit': '%', 'current': 67},
            'barometric_pressure': {'min': 95, 'max': 105, 'unit': 'kPa', 'current': 101.3},
            'ambient_air_temp': {'min': -20, 'max': 50, 'unit': '°C', 'current': 22},
            'fuel_rate': {'min': 0, 'max': 50, 'unit': 'L/h', 'current': 8.2},
        }
        
        self.current_data = {}
        self.dtcs = [
            {'code': 'P0171', 'description': 'System Too Lean (Bank 1)'},
            {'code': 'P0299', 'description': 'Turbocharger/Supercharger A Underboost Condition'}
        ]
    
    def connect_obd(self):
        """Simulate OBD2 adapter connection"""
        try:
            time.sleep(1)  # Simulate connection delay
            self.is_connected = True
            print("Demo mode: Simulated OBD2 connection established")
            return True
        except Exception as e:
            print(f"OBD Connection error: {e}")
            return False
    
    def start_data_collection(self):
        """Start collecting data in a separate thread"""
        if self.is_connected and not self.running:
            self.running = True
            self.data_thread = threading.Thread(target=self._collect_data)
            self.data_thread.daemon = True
            self.data_thread.start()
    
    def stop_data_collection(self):
        """Stop data collection"""
        self.running = False
    
    def _collect_data(self):
        """Generate realistic BMW diagnostic data"""
        while self.running and self.is_connected:
            try:
                for name, config in self.bmw_pids.items():
                    if not self.running:
                        break
                    
                    # Generate realistic variations
                    current = config['current']
                    variation = (config['max'] - config['min']) * 0.05  # 5% variation
                    
                    # Add some realistic patterns
                    if name == 'rpm':
                        new_value = current + random.uniform(-200, 200)
                        new_value = max(config['min'], min(config['max'], new_value))
                    elif name == 'speed':
                        new_value = current + random.uniform(-5, 5)
                        new_value = max(config['min'], min(config['max'], new_value))
                    elif name == 'coolant_temp':
                        new_value = current + random.uniform(-1, 1)
                        new_value = max(config['min'], min(config['max'], new_value))
                    else:
                        new_value = current + random.uniform(-variation, variation)
                        new_value = max(config['min'], min(config['max'], new_value))
                    
                    config['current'] = new_value
                    
                    self.current_data[name] = {
                        'value': round(new_value, 2),
                        'unit': config['unit'],
                        'timestamp': datetime.now().isoformat()
                    }
                
                time.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                print(f"Data collection error: {e}")
                time.sleep(2)
    
    def get_dtcs(self):
        """Get Diagnostic Trouble Codes"""
        if self.is_connected:
            return self.dtcs
        return []
    
    def clear_dtcs(self):
        """Clear Diagnostic Trouble Codes"""
        if self.is_connected:
            self.dtcs = []
            print("Demo mode: DTCs cleared")
            return True
        return False

# Global diagnostics instance
bmw_diag = BMWDiagnostics()

class BMWRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_file('templates/index.html', 'text/html')
        elif parsed_path.path.startswith('/static/'):
            # Serve static files
            file_path = parsed_path.path[1:]  # Remove leading slash
            if os.path.exists(file_path):
                if file_path.endswith('.css'):
                    self.serve_file(file_path, 'text/css')
                elif file_path.endswith('.js'):
                    self.serve_file(file_path, 'application/javascript')
                else:
                    super().do_GET()
            else:
                self.send_error(404)
        elif parsed_path.path == '/api/status':
            self.serve_json({
                'connected': bmw_diag.is_connected,
                'data': bmw_diag.current_data
            })
        elif parsed_path.path == '/api/dtcs':
            dtcs = bmw_diag.get_dtcs()
            self.serve_json({'dtcs': dtcs})
        else:
            self.send_error(404)
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/connect':
            success = bmw_diag.connect_obd()
            if success:
                bmw_diag.start_data_collection()
            self.serve_json({'connected': success})
        elif parsed_path.path == '/api/disconnect':
            bmw_diag.stop_data_collection()
            bmw_diag.is_connected = False
            self.serve_json({'disconnected': True})
        elif parsed_path.path == '/api/clear_dtcs':
            success = bmw_diag.clear_dtcs()
            self.serve_json({'cleared': success})
        else:
            self.send_error(404)
    
    def serve_file(self, filepath, content_type):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.send_header('Content-Length', len(content.encode('utf-8')))
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(404)
    
    def serve_json(self, data):
        json_data = json.dumps(data)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', len(json_data.encode('utf-8')))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == '__main__':
    PORT = 5000
    
    print("BMW OBD2 Diagnosticator Starting...")
    print("Running in DEMO MODE with simulated data")
    print(f"Open your browser to http://localhost:{PORT}")
    
    with socketserver.TCPServer(("localhost", PORT), BMWRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            bmw_diag.stop_data_collection()
            httpd.shutdown()