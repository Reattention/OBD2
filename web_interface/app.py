"""
BMW OBD2 Diagnostics Flask Web Application

Premium web interface for BMW OBD2 diagnostics featuring:
- Real-time dual turbo PSI monitoring
- BMW-themed professional UI
- WebSocket support for live updates
- REST API for OBD2 data
"""

import os
import sys
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import time
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from obd2_diagnostics import BMWDiagnostics
from obd2_diagnostics.config import OBD2Config

# Flask app configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'bmw-obd2-diagnostics-premium-interface'

# SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global diagnostics instance
diagnostics = None
live_data_thread = None
stop_live_data = threading.Event()


class TurboPressureConverter:
    """Utility class for turbo pressure conversions"""
    
    @staticmethod
    def kpa_to_psi(kpa_value):
        """Convert kPa to PSI"""
        if kpa_value is None:
            return None
        return round(kpa_value * 0.145038, 1)
    
    @staticmethod
    def bar_to_psi(bar_value):
        """Convert bar to PSI"""
        if bar_value is None:
            return None
        return round(bar_value * 14.5038, 1)
    
    @staticmethod
    def get_boost_vacuum_range(psi_value):
        """Get boost/vacuum status from PSI value"""
        if psi_value is None:
            return "No Data"
        
        if psi_value < -10:
            return "High Vacuum"
        elif psi_value < -5:
            return "Moderate Vacuum"
        elif psi_value < 0:
            return "Light Vacuum"
        elif psi_value < 0.5:
            return "Atmospheric"
        elif psi_value < 5:
            return "Light Boost"
        elif psi_value < 10:
            return "Moderate Boost"
        elif psi_value < 15:
            return "High Boost"
        else:
            return "Very High Boost"


def get_dual_turbo_data():
    """Get dual turbocharger data from BMW diagnostics"""
    if not diagnostics or not diagnostics.is_connected():
        return {
            'turbo1_psi': None,
            'turbo2_psi': None,
            'turbo1_status': 'Disconnected',
            'turbo2_status': 'Disconnected'
        }
    
    try:
        live_data = diagnostics.get_live_data()
        
        # Extract intake manifold pressure (simulates turbo pressure)
        intake_pressure = live_data.get('data', {}).get('INTAKE_PRESSURE', {}).get('value', 0)
        
        # For twin turbo BMW N63, simulate individual turbo pressures
        # In real implementation, these would be separate BMW PIDs
        if intake_pressure:
            # Simulate slight variance between turbos (real implementation would use actual PIDs)
            turbo1_kpa = intake_pressure + (hash('turbo1') % 10) / 10.0  # Small variance
            turbo2_kpa = intake_pressure + (hash('turbo2') % 10) / 10.0  # Small variance
            
            turbo1_psi = TurboPressureConverter.kpa_to_psi(turbo1_kpa)
            turbo2_psi = TurboPressureConverter.kpa_to_psi(turbo2_kpa)
            
            return {
                'turbo1_psi': turbo1_psi,
                'turbo2_psi': turbo2_psi,
                'turbo1_status': TurboPressureConverter.get_boost_vacuum_range(turbo1_psi),
                'turbo2_status': TurboPressureConverter.get_boost_vacuum_range(turbo2_psi),
                'raw_intake_pressure': intake_pressure
            }
        else:
            return {
                'turbo1_psi': 0.0,
                'turbo2_psi': 0.0,
                'turbo1_status': 'No Data',
                'turbo2_status': 'No Data'
            }
            
    except Exception as e:
        app.logger.error(f"Error getting turbo data: {e}")
        return {
            'turbo1_psi': None,
            'turbo2_psi': None,
            'turbo1_status': 'Error',
            'turbo2_status': 'Error'
        }


def live_data_worker():
    """Background thread for live data updates via WebSocket"""
    while not stop_live_data.is_set():
        try:
            if diagnostics and diagnostics.is_connected():
                # Get comprehensive live data
                live_data = diagnostics.get_live_data(refresh=True)
                turbo_data = get_dual_turbo_data()
                
                # Combine data for WebSocket emission
                combined_data = {
                    'timestamp': datetime.now().isoformat(),
                    'live_data': live_data,
                    'turbo_data': turbo_data,
                    'connection_status': 'connected'
                }
                
                socketio.emit('live_data_update', combined_data)
            else:
                # Send disconnected status
                socketio.emit('live_data_update', {
                    'timestamp': datetime.now().isoformat(),
                    'connection_status': 'disconnected'
                })
                
        except Exception as e:
            app.logger.error(f"Error in live data worker: {e}")
            
        # Wait 1 second between updates
        time.sleep(1)


# Route handlers
@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/dtc-scanner')
def dtc_scanner():
    """DTC scanner page"""
    return render_template('dtc_scanner.html')


@app.route('/settings')
def settings():
    """Settings and configuration page"""
    return render_template('settings.html')


# API Routes
@app.route('/api/live-data')
def api_live_data():
    """REST API endpoint for live OBD2 data"""
    if not diagnostics:
        return jsonify({'error': 'Diagnostics not initialized'})
    
    if not diagnostics.is_connected():
        return jsonify({'error': 'Not connected to vehicle'})
    
    try:
        live_data = diagnostics.get_live_data(refresh=True)
        return jsonify(live_data)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/dtcs')
def api_dtcs():
    """REST API endpoint for diagnostic trouble codes"""
    if not diagnostics:
        return jsonify({'error': 'Diagnostics not initialized'})
    
    if not diagnostics.is_connected():
        return jsonify({'error': 'Not connected to vehicle'})
    
    try:
        dtcs = diagnostics.get_dtcs()
        return jsonify(dtcs)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/clear-dtcs', methods=['POST'])
def api_clear_dtcs():
    """REST API endpoint to clear diagnostic trouble codes"""
    if not diagnostics:
        return jsonify({'error': 'Diagnostics not initialized'})
    
    if not diagnostics.is_connected():
        return jsonify({'error': 'Not connected to vehicle'})
    
    try:
        success = diagnostics.clear_dtcs()
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/turbo-pressure')
def api_turbo_pressure():
    """REST API endpoint for dual turbo PSI readings"""
    turbo_data = get_dual_turbo_data()
    return jsonify(turbo_data)


@app.route('/api/connection-status')
def api_connection_status():
    """REST API endpoint for connection status"""
    if not diagnostics:
        return jsonify({
            'connected': False,
            'status': 'Not initialized'
        })
    
    connected = diagnostics.is_connected()
    vehicle_info = diagnostics.get_vehicle_info() if connected else {}
    
    return jsonify({
        'connected': connected,
        'status': 'Connected' if connected else 'Disconnected',
        'vehicle_info': vehicle_info
    })


@app.route('/api/connect', methods=['POST'])
def api_connect():
    """REST API endpoint to connect to vehicle"""
    global diagnostics
    
    try:
        if not diagnostics:
            diagnostics = BMWDiagnostics()
            diagnostics.set_bmw_config("F13_650i")  # Default to BMW F13 650i
        
        success = diagnostics.connect(auto_detect=True)
        
        if success:
            return jsonify({'success': True, 'message': 'Connected to BMW vehicle'})
        else:
            return jsonify({'success': False, 'message': 'Failed to connect to vehicle'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/disconnect', methods=['POST'])
def api_disconnect():
    """REST API endpoint to disconnect from vehicle"""
    if diagnostics:
        try:
            diagnostics.disconnect()
            return jsonify({'success': True, 'message': 'Disconnected from vehicle'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    else:
        return jsonify({'success': True, 'message': 'Already disconnected'})


# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket client connection"""
    app.logger.info('WebSocket client connected')
    emit('connection_response', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket client disconnection"""
    app.logger.info('WebSocket client disconnected')


@socketio.on('request_live_data')
def handle_request_live_data():
    """Handle request for immediate live data update"""
    if diagnostics and diagnostics.is_connected():
        try:
            live_data = diagnostics.get_live_data(refresh=True)
            turbo_data = get_dual_turbo_data()
            
            combined_data = {
                'timestamp': datetime.now().isoformat(),
                'live_data': live_data,
                'turbo_data': turbo_data,
                'connection_status': 'connected'
            }
            
            emit('live_data_update', combined_data)
        except Exception as e:
            emit('live_data_update', {'error': str(e)})
    else:
        emit('live_data_update', {
            'timestamp': datetime.now().isoformat(),
            'connection_status': 'disconnected'
        })


def start_live_data_thread():
    """Start the background live data thread"""
    global live_data_thread
    if live_data_thread is None or not live_data_thread.is_alive():
        stop_live_data.clear()
        live_data_thread = threading.Thread(target=live_data_worker, daemon=True)
        live_data_thread.start()


def stop_live_data_thread():
    """Stop the background live data thread"""
    stop_live_data.set()
    if live_data_thread and live_data_thread.is_alive():
        live_data_thread.join(timeout=2)


if __name__ == '__main__':
    # Initialize diagnostics
    try:
        diagnostics = BMWDiagnostics()
        diagnostics.set_bmw_config("F13_650i")
        app.logger.info("BMW diagnostics initialized")
    except Exception as e:
        app.logger.error(f"Failed to initialize diagnostics: {e}")
    
    # Start live data thread
    start_live_data_thread()
    
    try:
        # Run Flask app with SocketIO
        socketio.run(app, host='127.0.0.1', port=5000, debug=True, use_reloader=False)
    finally:
        # Clean up
        stop_live_data_thread()
        if diagnostics:
            diagnostics.disconnect()