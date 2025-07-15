"""
Web Interface for BMW OBD2 Mobile Companion

READ-ONLY web interface providing mobile access to BMW diagnostics and analytics.
Includes QR code generation for easy phone connection and responsive design.
"""

import json
import qrcode
import io
import base64
from typing import Dict, Any, Optional
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response
import threading
import time


class WebInterface:
    """
    Mobile companion web interface for BMW OBD2 diagnostics
    
    Provides:
    - QR code generation for easy phone connection
    - Remote monitoring dashboard (read-only web access)
    - Real-time data streaming
    - Performance analytics visualization
    - Data export functionality
    - Push notifications for critical alerts
    """
    
    def __init__(self, bmw_diagnostics, host='0.0.0.0', port=5000):
        self.bmw_diagnostics = bmw_diagnostics
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        
        # Configuration
        self.app.config['SECRET_KEY'] = 'bmw_obd2_mobile_companion'
        
        # Data streaming
        self.streaming_clients = set()
        self.streaming_active = False
        self.streaming_thread = None
        
        # Alert tracking
        self.active_alerts = []
        self.last_alert_check = datetime.now()
        
        # Setup routes
        self._setup_routes()
        
        # Disable Flask logging for cleaner output
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
    
    def _setup_routes(self):
        """Setup Flask routes for the web interface"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            return render_template('dashboard.html')
        
        @self.app.route('/mobile')
        def mobile_dashboard():
            """Mobile-optimized dashboard"""
            return render_template('mobile_dashboard.html')
        
        @self.app.route('/performance')
        def performance_page():
            """Performance analytics page"""
            return render_template('performance.html')
        
        @self.app.route('/turbo')
        def turbo_page():
            """Turbo analytics page"""
            return render_template('turbo.html')
        
        @self.app.route('/maintenance')
        def maintenance_page():
            """Predictive maintenance page"""
            return render_template('maintenance.html')
        
        # API Endpoints
        
        @self.app.route('/api/status')
        def api_status():
            """Get current system status"""
            try:
                return jsonify({
                    'status': 'online',
                    'timestamp': datetime.now().isoformat(),
                    'connected': self.bmw_diagnostics.is_connected(),
                    'vehicle_info': self.bmw_diagnostics.get_vehicle_info(),
                    'adapter_info': self.bmw_diagnostics.get_adapter_info()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/live_data')
        def api_live_data():
            """Get current live data"""
            try:
                return jsonify(self.bmw_diagnostics.get_live_data())
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/performance/current')
        def api_performance_current():
            """Get current performance data"""
            try:
                return jsonify(self.bmw_diagnostics.get_performance_data())
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/performance/start_timer', methods=['POST'])
        def api_start_timer():
            """Start acceleration timer"""
            try:
                data = request.get_json() or {}
                event_type = data.get('event_type', '0-60')
                return jsonify(self.bmw_diagnostics.start_acceleration_timer(event_type))
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/performance/stop_timer', methods=['POST'])
        def api_stop_timer():
            """Stop acceleration timer"""
            try:
                return jsonify(self.bmw_diagnostics.stop_acceleration_timer())
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/performance/start_session', methods=['POST'])
        def api_start_session():
            """Start performance session"""
            try:
                data = request.get_json() or {}
                session_type = data.get('session_type', 'track')
                return jsonify(self.bmw_diagnostics.start_performance_session(session_type))
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/performance/end_session', methods=['POST'])
        def api_end_session():
            """End performance session"""
            try:
                return jsonify(self.bmw_diagnostics.end_performance_session())
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/performance/history')
        def api_performance_history():
            """Get performance history"""
            try:
                limit = request.args.get('limit', 20, type=int)
                return jsonify(self.bmw_diagnostics.get_acceleration_history(limit))
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/turbo/summary')
        def api_turbo_summary():
            """Get turbo performance summary"""
            try:
                return jsonify(self.bmw_diagnostics.get_turbo_performance_summary())
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/turbo/boost_map')
        def api_boost_map():
            """Get boost pressure map"""
            try:
                rpm_min = request.args.get('rpm_min', 1000, type=int)
                rpm_max = request.args.get('rpm_max', 7000, type=int)
                load_min = request.args.get('load_min', 0, type=int)
                load_max = request.args.get('load_max', 100, type=int)
                
                return jsonify(self.bmw_diagnostics.get_boost_pressure_map(
                    (rpm_min, rpm_max), (load_min, load_max)
                ))
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/turbo/lag_analysis')
        def api_turbo_lag():
            """Get turbo lag analysis"""
            try:
                return jsonify(self.bmw_diagnostics.get_turbo_lag_analysis())
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/turbo/intercooler')
        def api_intercooler():
            """Get intercooler efficiency data"""
            try:
                return jsonify(self.bmw_diagnostics.get_intercooler_efficiency_data())
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/maintenance/recommendations')
        def api_maintenance_recommendations():
            """Get maintenance recommendations"""
            try:
                return jsonify(self.bmw_diagnostics.get_maintenance_recommendations())
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/maintenance/oil_analysis')
        def api_oil_analysis():
            """Get oil analysis"""
            try:
                return jsonify(self.bmw_diagnostics.get_oil_analysis())
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/maintenance/turbo_health')
        def api_turbo_health():
            """Get turbo health prediction"""
            try:
                return jsonify(self.bmw_diagnostics.get_turbo_health_prediction())
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/maintenance/dtc_patterns')
        def api_dtc_patterns():
            """Get DTC pattern analysis"""
            try:
                return jsonify(self.bmw_diagnostics.get_dtc_pattern_analysis())
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/maintenance/record_event', methods=['POST'])
        def api_record_maintenance():
            """Record maintenance event"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                event_type = data.get('event_type')
                mileage = data.get('mileage')
                notes = data.get('notes')
                
                return jsonify(self.bmw_diagnostics.record_maintenance_event(
                    event_type, mileage, notes
                ))
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/diagnostics/dtcs')
        def api_dtcs():
            """Get diagnostic trouble codes"""
            try:
                return jsonify(self.bmw_diagnostics.get_dtcs())
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/diagnostics/advanced')
        def api_advanced_diagnostics():
            """Get advanced diagnostics"""
            try:
                return jsonify(self.bmw_diagnostics.get_advanced_diagnostics())
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/export/telemetry/<session_id>')
        def api_export_telemetry(session_id):
            """Export telemetry data"""
            try:
                format_type = request.args.get('format', 'csv')
                result = self.bmw_diagnostics.export_telemetry_data(session_id, format_type)
                
                if 'error' in result:
                    return jsonify(result), 404
                
                # Return as file download
                output = io.StringIO(result['data'])
                
                response = Response(
                    output.getvalue(),
                    mimetype='text/csv' if format_type == 'csv' else 'application/json',
                    headers={
                        'Content-Disposition': f'attachment; filename=telemetry_{session_id}.{format_type}'
                    }
                )
                return response
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/export/health_report')
        def api_export_health_report():
            """Export health report"""
            try:
                format_type = request.args.get('format', 'json')
                result = self.bmw_diagnostics.export_health_report(format_type)
                
                if 'error' in result:
                    return jsonify(result), 500
                
                # Return as file download
                output = io.StringIO(result['report'])
                
                response = Response(
                    output.getvalue(),
                    mimetype='application/json' if format_type == 'json' else 'text/csv',
                    headers={
                        'Content-Disposition': f'attachment; filename=health_report.{format_type}'
                    }
                )
                return response
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/qr_code')
        def api_qr_code():
            """Generate QR code for mobile access"""
            try:
                # Generate QR code with connection info
                connection_url = f"http://{self.host}:{self.port}/mobile"
                
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(connection_url)
                qr.make(fit=True)
                
                # Create QR code image
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Convert to base64 for web display
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                img_str = base64.b64encode(buffer.getvalue()).decode()
                
                return jsonify({
                    'qr_code': f"data:image/png;base64,{img_str}",
                    'connection_url': connection_url,
                    'instructions': 'Scan this QR code with your phone to access the mobile dashboard'
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stream')
        def api_stream():
            """Server-sent events stream for real-time data"""
            def generate():
                try:
                    self.streaming_clients.add(request.environ.get('werkzeug.request'))
                    
                    while True:
                        if self.bmw_diagnostics.is_connected():
                            # Get current data
                            live_data = self.bmw_diagnostics.get_live_data()
                            performance_data = self.bmw_diagnostics.get_performance_data()
                            
                            stream_data = {
                                'timestamp': datetime.now().isoformat(),
                                'live_data': live_data,
                                'performance_data': performance_data,
                                'alerts': self._check_alerts()
                            }
                            
                            yield f"data: {json.dumps(stream_data)}\n\n"
                        else:
                            yield f"data: {json.dumps({'status': 'disconnected'})}\n\n"
                        
                        time.sleep(1)  # Update every second
                        
                except GeneratorExit:
                    self.streaming_clients.discard(request.environ.get('werkzeug.request'))
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return Response(generate(), mimetype='text/event-stream')
    
    def generate_qr_code(self) -> str:
        """Generate QR code for mobile access"""
        try:
            connection_url = f"http://{self.host}:{self.port}/mobile"
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(connection_url)
            qr.make(fit=True)
            
            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to buffer and convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            return f"Error generating QR code: {e}"
    
    def _check_alerts(self) -> list:
        """Check for critical alerts"""
        try:
            # Get maintenance recommendations which include alerts
            maintenance_data = self.bmw_diagnostics.get_maintenance_recommendations()
            
            alerts = []
            if 'active_alerts' in maintenance_data:
                for alert in maintenance_data['active_alerts']:
                    if alert.get('urgency') in ['high', 'critical']:
                        alerts.append({
                            'type': alert.get('alert_type', 'unknown'),
                            'message': alert.get('description', 'Critical alert'),
                            'urgency': alert.get('urgency', 'medium'),
                            'component': alert.get('component', 'unknown')
                        })
            
            # Check live data for immediate alerts
            live_data = self.bmw_diagnostics.get_live_data()
            if 'data' in live_data:
                data = live_data['data']
                
                # High coolant temperature
                coolant_temp = data.get('COOLANT_TEMP', {}).get('value', 0)
                if coolant_temp > 110:
                    alerts.append({
                        'type': 'high_temperature',
                        'message': f'High coolant temperature: {coolant_temp}°C',
                        'urgency': 'critical',
                        'component': 'cooling_system'
                    })
                
                # High boost pressure (potential overboost)
                boost_pressure = data.get('INTAKE_PRESSURE', {}).get('value', 0)
                if boost_pressure > 25:  # PSI, roughly 18 PSI boost + 14.7 atmospheric
                    alerts.append({
                        'type': 'overboost',
                        'message': f'Potential overboost condition: {boost_pressure} PSI',
                        'urgency': 'high',
                        'component': 'turbocharger'
                    })
            
            return alerts
            
        except Exception:
            return []
    
    def start_server(self, debug=False):
        """Start the web server"""
        try:
            print(f"🌐 Starting BMW OBD2 Mobile Companion Web Interface")
            print(f"📱 Access URL: http://{self.host}:{self.port}")
            print(f"📱 Mobile URL: http://{self.host}:{self.port}/mobile")
            print(f"🔗 QR Code: http://{self.host}:{self.port}/api/qr_code")
            print(f"🛡️  READ-ONLY Operation: No ECU modifications")
            
            self.app.run(
                host=self.host,
                port=self.port,
                debug=debug,
                threaded=True,
                use_reloader=False  # Disable reloader to prevent double initialization
            )
            
        except Exception as e:
            print(f"Error starting web server: {e}")
    
    def stop_server(self):
        """Stop the web server"""
        self.streaming_active = False
        if self.streaming_thread:
            self.streaming_thread.join()


# HTML Templates (embedded for simplicity)
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BMW OBD2 Advanced Monitoring</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #1f4e79; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status-good { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-danger { color: #dc3545; }
        .btn { background: #1f4e79; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #2a5a8a; }
        .metric { font-size: 2em; font-weight: bold; margin: 10px 0; }
        .qr-container { text-align: center; }
        .alert { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .alert-danger { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
        .alert-warning { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚗 BMW OBD2 Advanced Monitoring</h1>
            <p>Real-time diagnostics and performance analytics - READ-ONLY operation</p>
        </div>
        
        <div class="dashboard-grid">
            <div class="card">
                <h3>🔗 Mobile Access</h3>
                <div class="qr-container">
                    <div id="qr-code"></div>
                    <p>Scan QR code with your phone for mobile access</p>
                    <button class="btn" onclick="generateQR()">Generate QR Code</button>
                </div>
            </div>
            
            <div class="card">
                <h3>📊 System Status</h3>
                <div id="system-status">Loading...</div>
            </div>
            
            <div class="card">
                <h3>🏁 Performance Analytics</h3>
                <div id="performance-data">Loading...</div>
                <button class="btn" onclick="startAccelTimer()">Start 0-60 Timer</button>
                <button class="btn" onclick="stopAccelTimer()">Stop Timer</button>
            </div>
            
            <div class="card">
                <h3>🌪️ Turbo Analytics</h3>
                <div id="turbo-data">Loading...</div>
            </div>
            
            <div class="card">
                <h3>🔧 Predictive Maintenance</h3>
                <div id="maintenance-data">Loading...</div>
            </div>
            
            <div class="card">
                <h3>🚨 Active Alerts</h3>
                <div id="alerts">No alerts</div>
            </div>
        </div>
    </div>

    <script>
        let eventSource;
        
        function initializeRealTimeData() {
            eventSource = new EventSource('/api/stream');
            
            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.error) {
                    console.error('Stream error:', data.error);
                    return;
                }
                
                updateSystemStatus(data);
                updatePerformanceData(data);
                updateTurboData(data);
                updateAlerts(data.alerts || []);
            };
            
            eventSource.onerror = function(event) {
                console.error('EventSource failed:', event);
            };
        }
        
        function updateSystemStatus(data) {
            const status = document.getElementById('system-status');
            const connected = data.live_data && !data.live_data.error;
            
            status.innerHTML = `
                <div class="${connected ? 'status-good' : 'status-danger'}">
                    ${connected ? '✅ Connected' : '❌ Disconnected'}
                </div>
                <div>Last Update: ${new Date().toLocaleTimeString()}</div>
            `;
        }
        
        function updatePerformanceData(data) {
            const perf = document.getElementById('performance-data');
            const perfData = data.performance_data;
            
            if (perfData && perfData.current_metrics) {
                const metrics = perfData.current_metrics;
                perf.innerHTML = `
                    <div>Speed: <span class="metric">${metrics.speed_mph}</span> mph</div>
                    <div>G-Force: <span class="metric">${metrics.g_force_longitudinal}</span> G</div>
                    <div>Power Est: <span class="metric">${metrics.estimated_power_hp}</span> HP</div>
                `;
            } else {
                perf.innerHTML = 'No performance data available';
            }
        }
        
        function updateTurboData(data) {
            const turbo = document.getElementById('turbo-data');
            const liveData = data.live_data;
            
            if (liveData && liveData.data) {
                const boostPressure = liveData.data.INTAKE_PRESSURE?.value || 0;
                const rpm = liveData.data.RPM?.value || 0;
                
                turbo.innerHTML = `
                    <div>Boost: <span class="metric">${Math.max(0, boostPressure - 14.7).toFixed(1)}</span> PSI</div>
                    <div>RPM: <span class="metric">${rpm}</span></div>
                `;
            } else {
                turbo.innerHTML = 'No turbo data available';
            }
        }
        
        function updateAlerts(alerts) {
            const alertsDiv = document.getElementById('alerts');
            
            if (alerts.length === 0) {
                alertsDiv.innerHTML = '<div class="status-good">No active alerts</div>';
                return;
            }
            
            let alertsHTML = '';
            alerts.forEach(alert => {
                const alertClass = alert.urgency === 'critical' ? 'alert-danger' : 'alert-warning';
                alertsHTML += `<div class="alert ${alertClass}">${alert.message}</div>`;
            });
            
            alertsDiv.innerHTML = alertsHTML;
        }
        
        function generateQR() {
            fetch('/api/qr_code')
                .then(response => response.json())
                .then(data => {
                    if (data.qr_code) {
                        document.getElementById('qr-code').innerHTML = 
                            `<img src="${data.qr_code}" alt="QR Code" style="max-width: 200px;">`;
                    }
                })
                .catch(error => console.error('Error generating QR code:', error));
        }
        
        function startAccelTimer() {
            fetch('/api/performance/start_timer', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({event_type: '0-60'})
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'started') {
                    alert('0-60 timer started!');
                } else {
                    alert('Error starting timer: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => console.error('Error starting timer:', error));
        }
        
        function stopAccelTimer() {
            fetch('/api/performance/stop_timer', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'completed') {
                    const duration = data.results.duration_seconds;
                    alert(`0-60 time: ${duration.toFixed(2)} seconds!`);
                } else {
                    alert('Error stopping timer: ' + (data.error || 'No active timer'));
                }
            })
            .catch(error => console.error('Error stopping timer:', error));
        }
        
        // Initialize real-time data updates
        document.addEventListener('DOMContentLoaded', function() {
            initializeRealTimeData();
            
            // Load maintenance data
            fetch('/api/maintenance/recommendations')
                .then(response => response.json())
                .then(data => {
                    const maintenanceDiv = document.getElementById('maintenance-data');
                    if (data.vehicle_status) {
                        const healthScore = data.vehicle_status.overall_health_score;
                        maintenanceDiv.innerHTML = `
                            <div>Health Score: <span class="metric ${healthScore > 80 ? 'status-good' : healthScore > 60 ? 'status-warning' : 'status-danger'}">${healthScore}</span>%</div>
                            <div>Active Alerts: ${data.active_alerts?.length || 0}</div>
                        `;
                    }
                })
                .catch(error => console.error('Error loading maintenance data:', error));
        });
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', function() {
            if (eventSource) {
                eventSource.close();
            }
        });
    </script>
</body>
</html>
'''

# Create templates directory and save template
import os

def setup_web_templates():
    """Setup web templates for the Flask application"""
    templates_dir = '/home/runner/work/OBD2/OBD2/templates'
    
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # Save dashboard template
    with open(os.path.join(templates_dir, 'dashboard.html'), 'w') as f:
        f.write(DASHBOARD_TEMPLATE)
    
    # Create mobile dashboard template (simplified version)
    mobile_template = DASHBOARD_TEMPLATE.replace(
        'BMW OBD2 Advanced Monitoring',
        'BMW OBD2 Mobile'
    ).replace(
        'grid-template-columns: repeat(auto-fit, minmax(300px, 1fr))',
        'grid-template-columns: 1fr'
    )
    
    with open(os.path.join(templates_dir, 'mobile_dashboard.html'), 'w') as f:
        f.write(mobile_template)
    
    # Create placeholder templates for other pages
    placeholder_template = '''
    <!DOCTYPE html>
    <html><head><title>BMW OBD2 - {title}</title></head>
    <body><h1>{title}</h1><p>Feature coming soon...</p></body></html>
    '''
    
    for page, title in [('performance.html', 'Performance Analytics'), 
                       ('turbo.html', 'Turbo Analytics'), 
                       ('maintenance.html', 'Predictive Maintenance')]:
        with open(os.path.join(templates_dir, page), 'w') as f:
            f.write(placeholder_template.format(title=title))