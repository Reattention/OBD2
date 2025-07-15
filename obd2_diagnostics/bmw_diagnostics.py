"""
BMW Diagnostics Main Class

Main interface for BMW OBD2 diagnostics, providing high-level functions
for real ECU communication and BMW-specific diagnostic operations.
"""

import obd
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, Future

from .config import OBD2Config, BMW_CONFIGS
from .obd2_adapter import OBD2Adapter, ConnectionStatus, AdapterDiscovery
from .dtc_handler import DTCHandler, DiagnosticTroubleCode, DTCStatus
from .bmw_pids import bmw_pid_registry, standard_pid_mapper
from .performance_analytics import PerformanceAnalytics
from .turbo_analytics import TurboAnalytics
from .predictive_maintenance import PredictiveMaintenance
from .web_interface import WebInterface


class BMWDiagnostics:
    """
    Main BMW OBD2 Diagnostics class
    
    Provides a high-level interface for BMW vehicle diagnostics,
    replacing simulated data with real ECU communication.
    """
    
    def __init__(self, config: Optional[OBD2Config] = None):
        """Initialize BMW diagnostics"""
        self.config = config or OBD2Config()
        self.adapter = OBD2Adapter(self.config)
        self.dtc_handler = DTCHandler(self.adapter)
        
        # Initialize advanced analytics modules
        self.performance_analytics = PerformanceAnalytics(self.adapter)
        self.turbo_analytics = TurboAnalytics(self.adapter)
        self.predictive_maintenance = PredictiveMaintenance(self.adapter)
        
        # Initialize web interface (optional)
        self.web_interface = None
        
        # State tracking
        self.connected = False
        self.vehicle_info = {}
        self.last_data_update = None
        self.live_data_cache = {}
        self.connection_callbacks = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.config.log_level)
        
        # Set logger for analytics modules
        self.performance_analytics.logger = self.logger
        self.turbo_analytics.logger = self.logger
        self.predictive_maintenance.logger = self.logger
        
        # Register connection callbacks
        self.adapter.add_connection_callback(self._on_connection_change)
        
        self.logger.info("BMW Diagnostics initialized with advanced analytics")
    
    def add_connection_callback(self, callback: Callable[[bool, Optional[str]], None]):
        """Add callback for connection status changes"""
        self.connection_callbacks.append(callback)
    
    def connect(self, auto_detect: bool = True) -> bool:
        """
        Connect to BMW vehicle via OBD2 adapter
        
        Args:
            auto_detect: Whether to auto-detect adapter if not configured
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.logger.info("Connecting to BMW vehicle...")
            
            # Auto-detect adapter if needed
            if auto_detect and not self.config.port:
                detected_port = AdapterDiscovery.auto_detect_adapter(self.config)
                if detected_port:
                    self.config.port = detected_port
                    self.logger.info(f"Auto-detected adapter on {detected_port}")
                else:
                    self.logger.warning("No adapter auto-detected")
            
            # Attempt connection
            success = self.adapter.connect()
            
            if success:
                self.connected = True
                self._update_vehicle_info()
                self.adapter.start_auto_reconnect()
                self.logger.info("Successfully connected to BMW vehicle")
            else:
                self.connected = False
                self.logger.error("Failed to connect to BMW vehicle")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error during connection: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from BMW vehicle"""
        try:
            self.adapter.disconnect()
            self.connected = False
            self.vehicle_info.clear()
            self.live_data_cache.clear()
            self.logger.info("Disconnected from BMW vehicle")
            
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to vehicle"""
        return self.connected and self.adapter.is_connected()
    
    def get_vehicle_info(self) -> Dict[str, Any]:
        """Get vehicle information and supported features"""
        if not self.is_connected():
            return {}
        
        return self.vehicle_info.copy()
    
    def get_live_data(self, refresh: bool = False) -> Dict[str, Any]:
        """
        Get live engine and vehicle data
        
        Args:
            refresh: Force refresh of cached data
            
        Returns:
            Dictionary of live vehicle data
        """
        if not self.is_connected():
            self.logger.warning("Cannot get live data - not connected")
            return {}
        
        # Check cache age
        if not refresh and self.live_data_cache and self.last_data_update:
            cache_age = (datetime.now() - self.last_data_update).total_seconds()
            if cache_age < 1.0:  # Use cache if less than 1 second old
                return self.live_data_cache.copy()
        
        try:
            # Standard OBD2 commands for BMW
            standard_commands = [
                obd.commands.RPM,
                obd.commands.SPEED,
                obd.commands.COOLANT_TEMP,
                obd.commands.ENGINE_LOAD,
                obd.commands.THROTTLE_POS,
                obd.commands.INTAKE_TEMP,
                obd.commands.MAF,
                obd.commands.FUEL_PRESSURE,
                obd.commands.INTAKE_PRESSURE,
                obd.commands.TIMING_ADVANCE,
                obd.commands.FUEL_LEVEL,
                obd.commands.BAROMETRIC_PRESSURE,
                obd.commands.AMBIENT_AIR_TEMP,
                obd.commands.CONTROL_MODULE_VOLTAGE
            ]
            
            # Query commands efficiently
            responses = self.adapter.query_multiple_commands(standard_commands)
            
            # Process responses with BMW-specific interpretation
            live_data = {
                'timestamp': datetime.now().isoformat(),
                'connection_status': 'connected',
                'vehicle_type': 'BMW F13',
                'data': {}
            }
            
            for command_name, response in responses.items():
                if response and not response.is_null():
                    # Get standard value
                    value = response.value
                    
                    # Apply BMW-specific interpretation
                    interpreted = standard_pid_mapper.interpret_value(
                        next((cmd for cmd in standard_commands if cmd.name == command_name), None),
                        value
                    )
                    
                    live_data['data'][command_name] = interpreted
            
            # Add BMW-specific data if available
            bmw_data = self._get_bmw_specific_data()
            if bmw_data:
                live_data['bmw_specific'] = bmw_data
            
            # Cache the data
            self.live_data_cache = live_data
            self.last_data_update = datetime.now()
            
            # Update advanced analytics modules with new data
            self._update_analytics_modules(live_data)
            
            return live_data
            
        except Exception as e:
            self.logger.error(f"Error getting live data: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'connection_status': 'error',
                'error': str(e),
                'data': {}
            }
    
    def get_dtcs(self) -> Dict[str, Any]:
        """Get diagnostic trouble codes with pattern analysis"""
        if not self.is_connected():
            return {'error': 'Not connected to vehicle'}
        
        try:
            dtcs, status = self.dtc_handler.read_dtcs()
            analysis = self.dtc_handler.get_dtc_analysis(dtcs)
            
            dtc_result = {
                'timestamp': datetime.now().isoformat(),
                'status': {
                    'mil_on': status.mil_on,
                    'total_dtcs': status.dtc_count,
                    'confirmed': status.confirmed_dtc_count,
                    'pending': status.pending_dtc_count,
                    'permanent': status.permanent_dtc_count
                },
                'dtcs': [dtc.to_dict() for dtc in dtcs],
                'analysis': analysis
            }
            
            # Extract DTC codes for pattern analysis
            dtc_codes = [dtc.code for dtc in dtcs]
            self._last_dtcs = dtc_codes
            
            # Update predictive maintenance with DTC patterns
            try:
                self.predictive_maintenance.update_dtc_patterns(dtc_codes)
            except Exception as e:
                self.logger.debug(f"Error updating DTC patterns: {e}")
            
            return dtc_result
            
        except Exception as e:
            self.logger.error(f"Error reading DTCs: {e}")
            return {'error': str(e)}
    
    # ===== MOBILE COMPANION WEB INTERFACE =====
    
    def start_web_interface(self, host='0.0.0.0', port=5000, debug=False) -> Dict[str, Any]:
        """
        Start the mobile companion web interface
        
        Args:
            host: Host address to bind to
            port: Port number to bind to 
            debug: Enable Flask debug mode
            
        Returns:
            Web interface startup status
        """
        try:
            if self.web_interface:
                return {'error': 'Web interface already running'}
            
            self.web_interface = WebInterface(self, host, port)
            
            # Start in a separate thread to avoid blocking
            import threading
            web_thread = threading.Thread(
                target=self.web_interface.start_server,
                args=(debug,),
                daemon=True
            )
            web_thread.start()
            
            return {
                'status': 'started',
                'url': f'http://{host}:{port}',
                'mobile_url': f'http://{host}:{port}/mobile',
                'qr_code_url': f'http://{host}:{port}/api/qr_code',
                'host': host,
                'port': port
            }
            
        except Exception as e:
            self.logger.error(f"Error starting web interface: {e}")
            return {'error': str(e)}
    
    def get_web_interface_status(self) -> Dict[str, Any]:
        """
        Get web interface status
        
        Returns:
            Current web interface status
        """
        if not self.web_interface:
            return {'status': 'not_running'}
        
        return {
            'status': 'running',
            'host': self.web_interface.host,
            'port': self.web_interface.port,
            'access_url': f'http://{self.web_interface.host}:{self.web_interface.port}',
            'mobile_url': f'http://{self.web_interface.host}:{self.web_interface.port}/mobile'
        }
    
    def generate_mobile_qr_code(self) -> Dict[str, Any]:
        """
        Generate QR code for mobile access
        
        Returns:
            QR code data and connection information
        """
        try:
            if not self.web_interface:
                return {'error': 'Web interface not running'}
            
            qr_code = self.web_interface.generate_qr_code()
            
            return {
                'qr_code': qr_code,
                'connection_url': f'http://{self.web_interface.host}:{self.web_interface.port}/mobile',
                'instructions': 'Scan this QR code with your phone to access the mobile dashboard'
            }
            
        except Exception as e:
            self.logger.error(f"Error generating QR code: {e}")
            return {'error': str(e)}
    
    def clear_dtcs(self) -> bool:
        """Clear diagnostic trouble codes"""
        if not self.is_connected():
            self.logger.warning("Cannot clear DTCs - not connected")
            return False
        
        return self.dtc_handler.clear_dtcs()
    
    def get_freeze_frame_data(self, dtc_code: str) -> Dict[str, Any]:
        """Get freeze frame data for specific DTC"""
        if not self.is_connected():
            return {}
        
        return self.dtc_handler.get_freeze_frame_data(dtc_code)
    
    def perform_readiness_test(self) -> Dict[str, Any]:
        """Perform OBD2 readiness test"""
        if not self.is_connected():
            return {'error': 'Not connected to vehicle'}
        
        try:
            # Get monitor status
            response = self.adapter.query_command(obd.commands.STATUS)
            
            if not response or response.is_null():
                return {'error': 'Could not read monitor status'}
            
            status = response.value
            
            readiness = {
                'timestamp': datetime.now().isoformat(),
                'mil_status': status.MIL if hasattr(status, 'MIL') else False,
                'dtc_count': status.DTC_count if hasattr(status, 'DTC_count') else 0,
                'monitors': {}
            }
            
            # Check individual monitors
            monitor_commands = [
                (obd.commands.MONITOR_O2_B1S1, 'O2_B1S1'),
                (obd.commands.MONITOR_O2_B1S2, 'O2_B1S2'),
                (obd.commands.MONITOR_CATALYST_B1, 'Catalyst_B1'),
                (obd.commands.MONITOR_EVAP, 'EVAP'),
                (obd.commands.MONITOR_SECONDARY_AIR, 'Secondary_Air'),
                (obd.commands.MONITOR_EGR, 'EGR'),
                (obd.commands.MONITOR_MISFIRE, 'Misfire'),
                (obd.commands.MONITOR_FUEL_SYSTEM, 'Fuel_System')
            ]
            
            for command, name in monitor_commands:
                try:
                    monitor_response = self.adapter.query_command(command)
                    if monitor_response and not monitor_response.is_null():
                        readiness['monitors'][name] = {
                            'available': True,
                            'complete': not monitor_response.value if hasattr(monitor_response, 'value') else True
                        }
                    else:
                        readiness['monitors'][name] = {
                            'available': False,
                            'complete': False
                        }
                except Exception as e:
                    self.logger.debug(f"Monitor {name} not available: {e}")
                    readiness['monitors'][name] = {
                        'available': False,
                        'complete': False
                    }
            
            return readiness
            
        except Exception as e:
            self.logger.error(f"Error performing readiness test: {e}")
            return {'error': str(e)}
    
    def get_adapter_info(self) -> Dict[str, Any]:
        """Get OBD2 adapter information"""
        base_info = self.adapter.get_adapter_info()
        
        base_info.update({
            'config': self.config.to_dict(),
            'bmw_support': True,
            'bmw_generation': self.config.generation,
            'connection_time': self.last_data_update.isoformat() if self.last_data_update else None
        })
        
        return base_info
    
    def set_bmw_config(self, model_config: str):
        """Set BMW model-specific configuration"""
        if model_config in BMW_CONFIGS:
            config_data = BMW_CONFIGS[model_config]
            self.config.from_dict(config_data)
            self.logger.info(f"Applied BMW configuration: {model_config}")
        else:
            self.logger.warning(f"Unknown BMW configuration: {model_config}")
    
    def _update_vehicle_info(self):
        """Update vehicle information from ECU"""
        try:
            info = {
                'connection_time': datetime.now().isoformat(),
                'adapter_info': self.adapter.get_adapter_info(),
                'bmw_generation': self.config.generation,
                'supported_commands': len(self.adapter.supported_commands),
                'bmw_specific_support': self.config.bmw_extended_pids
            }
            
            # Try to get VIN
            try:
                vin_response = self.adapter.query_command(obd.commands.VIN)
                if vin_response and not vin_response.is_null():
                    info['vin'] = vin_response.value
            except Exception as e:
                self.logger.debug(f"Could not read VIN: {e}")
            
            # Try to get ECU name
            try:
                ecu_response = self.adapter.query_command(obd.commands.ELM_DESCRIBE_PROTOCOL)
                if ecu_response and not ecu_response.is_null():
                    info['protocol_description'] = ecu_response.value
            except Exception as e:
                self.logger.debug(f"Could not read protocol description: {e}")
            
            self.vehicle_info = info
            
        except Exception as e:
            self.logger.error(f"Error updating vehicle info: {e}")
    
    def _get_bmw_specific_data(self) -> Dict[str, Any]:
        """Get BMW-specific PID data"""
        bmw_data = {}
        
        try:
            # Get BMW-specific PIDs that are available
            available_pids = bmw_pid_registry.get_all_pids()
            
            # For demonstration, we'll simulate BMW-specific data
            # In a real implementation, these would be actual PID queries
            if self.config.bmw_extended_pids:
                bmw_data = {
                    'valvetronic_position': 45.2,  # Would be actual PID query
                    'turbo_boost_target': 1.2,     # Would be actual PID query
                    'fuel_rail_pressure': 250.5,   # Would be actual PID query
                    'intake_cam_timing': 15.3,     # Would be actual PID query
                    'exhaust_cam_timing': -8.7,    # Would be actual PID query
                    'note': 'BMW-specific PIDs require actual implementation with vehicle'
                }
        
        except Exception as e:
            self.logger.debug(f"Error getting BMW-specific data: {e}")
        
        return bmw_data
    
    def _on_connection_change(self, status: ConnectionStatus, error: Optional[str]):
        """Handle connection status changes"""
        connected = (status == ConnectionStatus.CONNECTED)
        
        if connected != self.connected:
            self.connected = connected
            
            # Notify callbacks
            for callback in self.connection_callbacks:
                try:
                    callback(connected, error)
                except Exception as e:
                    self.logger.error(f"Error in connection callback: {e}")
        
        self.logger.info(f"Connection status changed: {status.value}")
        if error:
            self.logger.error(f"Connection error: {error}")
    
    def get_diagnostic_summary(self) -> Dict[str, Any]:
        """Get comprehensive diagnostic summary"""
        if not self.is_connected():
            return {'error': 'Not connected to vehicle'}
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'vehicle_info': self.get_vehicle_info(),
            'connection_status': 'connected',
            'live_data': self.get_live_data(),
            'dtc_info': self.get_dtcs(),
            'readiness_test': self.perform_readiness_test(),
            'adapter_info': self.get_adapter_info()
        }
        
        return summary
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
    
    def __repr__(self):
        """String representation"""
        status = "Connected" if self.is_connected() else "Disconnected"
        return f"BMWDiagnostics(status={status}, generation={self.config.generation})"
    
    # ===== ADVANCED MONITORING FEATURES =====
    # All methods below are READ-ONLY and provide advanced analytics
    
    def _update_analytics_modules(self, live_data: Dict[str, Any]) -> None:
        """Update all analytics modules with new live data"""
        try:
            # Extract mileage if available (would come from vehicle info)
            current_mileage = self.vehicle_info.get('mileage', 0)
            
            # Update performance analytics
            self.performance_analytics.update_live_data(live_data)
            
            # Update turbo analytics
            self.turbo_analytics.update_turbo_data(live_data)
            
            # Update predictive maintenance
            self.predictive_maintenance.update_maintenance_data(live_data, current_mileage)
            
            # Update DTC patterns if we have DTCs
            if hasattr(self, '_last_dtcs'):
                self.predictive_maintenance.update_dtc_patterns(self._last_dtcs)
                
        except Exception as e:
            self.logger.debug(f"Error updating analytics modules: {e}")
    
    # ===== PERFORMANCE ANALYTICS API =====
    
    def get_performance_data(self) -> Dict[str, Any]:
        """
        Get real-time performance analytics
        
        Returns:
            Current performance metrics including 0-60 timer, G-force, power estimates
        """
        try:
            return self.performance_analytics.get_current_performance_data()
        except Exception as e:
            self.logger.error(f"Error getting performance data: {e}")
            return {'error': str(e)}
    
    def start_acceleration_timer(self, event_type: str = "0-60") -> Dict[str, Any]:
        """
        Start an acceleration timer for performance measurement
        
        Args:
            event_type: Type of acceleration event ("0-60", "quarter-mile", "custom")
            
        Returns:
            Timer start confirmation with event ID
        """
        try:
            event_id = self.performance_analytics.start_acceleration_timer(event_type)
            return {
                'status': 'started',
                'event_id': event_id,
                'event_type': event_type,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error starting acceleration timer: {e}")
            return {'error': str(e)}
    
    def stop_acceleration_timer(self) -> Dict[str, Any]:
        """
        Stop the current acceleration timer
        
        Returns:
            Acceleration event results or error
        """
        try:
            result = self.performance_analytics.stop_acceleration_timer()
            if result:
                return {
                    'status': 'completed',
                    'results': result
                }
            else:
                return {'error': 'No active acceleration timer'}
        except Exception as e:
            self.logger.error(f"Error stopping acceleration timer: {e}")
            return {'error': str(e)}
    
    def start_performance_session(self, session_type: str = "track") -> Dict[str, Any]:
        """
        Start a performance session for telemetry recording
        
        Args:
            session_type: Type of session ("track", "drag", "street")
            
        Returns:
            Session start confirmation with session ID
        """
        try:
            session_id = self.performance_analytics.start_performance_session(session_type)
            return {
                'status': 'started',
                'session_id': session_id,
                'session_type': session_type,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error starting performance session: {e}")
            return {'error': str(e)}
    
    def end_performance_session(self) -> Dict[str, Any]:
        """
        End the current performance session
        
        Returns:
            Session summary and statistics
        """
        try:
            result = self.performance_analytics.end_performance_session()
            if result:
                return {
                    'status': 'completed',
                    'session_summary': result
                }
            else:
                return {'error': 'No active performance session'}
        except Exception as e:
            self.logger.error(f"Error ending performance session: {e}")
            return {'error': str(e)}
    
    def get_acceleration_history(self, limit: int = 20) -> Dict[str, Any]:
        """
        Get recent acceleration event history
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of recent acceleration events
        """
        try:
            history = self.performance_analytics.get_acceleration_history(limit)
            return {
                'timestamp': datetime.now().isoformat(),
                'acceleration_history': history,
                'total_events': len(history)
            }
        except Exception as e:
            self.logger.error(f"Error getting acceleration history: {e}")
            return {'error': str(e)}
    
    def get_session_history(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get recent performance session history
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of recent performance sessions
        """
        try:
            history = self.performance_analytics.get_session_history(limit)
            return {
                'timestamp': datetime.now().isoformat(),
                'session_history': history,
                'total_sessions': len(history)
            }
        except Exception as e:
            self.logger.error(f"Error getting session history: {e}")
            return {'error': str(e)}
    
    def export_telemetry_data(self, session_id: str, format_type: str = "csv") -> Dict[str, Any]:
        """
        Export telemetry data for analysis
        
        Args:
            session_id: Session ID to export
            format_type: Export format ("csv", "json")
            
        Returns:
            Exported telemetry data
        """
        try:
            data = self.performance_analytics.export_telemetry_data(session_id, format_type)
            if data:
                return {
                    'status': 'success',
                    'session_id': session_id,
                    'format': format_type,
                    'data': data
                }
            else:
                return {'error': 'Session not found or no telemetry data available'}
        except Exception as e:
            self.logger.error(f"Error exporting telemetry data: {e}")
            return {'error': str(e)}
    
    # ===== TURBO ANALYTICS API =====
    
    def get_turbo_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive turbo performance analysis
        
        Returns:
            Detailed turbo performance data and health scores
        """
        try:
            return self.turbo_analytics.get_turbo_performance_summary()
        except Exception as e:
            self.logger.error(f"Error getting turbo performance summary: {e}")
            return {'error': str(e)}
    
    def get_boost_pressure_map(self, rpm_range: tuple = (1000, 7000), 
                              load_range: tuple = (0, 100)) -> Dict[str, Any]:
        """
        Get 3D boost pressure mapping data for visualization
        
        Args:
            rpm_range: RPM range for mapping (min, max)
            load_range: Engine load range for mapping (min, max)
            
        Returns:
            3D boost pressure map data
        """
        try:
            return self.turbo_analytics.get_boost_pressure_map(rpm_range, load_range)
        except Exception as e:
            self.logger.error(f"Error getting boost pressure map: {e}")
            return {'error': str(e)}
    
    def get_turbo_lag_analysis(self) -> Dict[str, Any]:
        """
        Get detailed turbo lag analysis and spool time comparison
        
        Returns:
            Comprehensive turbo lag analysis between Turbo 1 & 2
        """
        try:
            return self.turbo_analytics.get_turbo_lag_analysis()
        except Exception as e:
            self.logger.error(f"Error getting turbo lag analysis: {e}")
            return {'error': str(e)}
    
    def get_intercooler_efficiency_data(self) -> Dict[str, Any]:
        """
        Get intercooler efficiency monitoring data
        
        Returns:
            Intercooler efficiency analysis and temperature data
        """
        try:
            return self.turbo_analytics.get_intercooler_efficiency_data()
        except Exception as e:
            self.logger.error(f"Error getting intercooler efficiency data: {e}")
            return {'error': str(e)}
    
    def get_wastegate_analysis(self) -> Dict[str, Any]:
        """
        Get wastegate position tracking and analysis
        
        Returns:
            Wastegate behavior analysis based on boost patterns
        """
        try:
            return self.turbo_analytics.get_wastegate_analysis()
        except Exception as e:
            self.logger.error(f"Error getting wastegate analysis: {e}")
            return {'error': str(e)}
    
    def get_compressor_efficiency_map(self) -> Dict[str, Any]:
        """
        Get compressor efficiency visualization data
        
        Returns:
            Compressor efficiency map with operating points
        """
        try:
            return self.turbo_analytics.get_compressor_efficiency_map()
        except Exception as e:
            self.logger.error(f"Error getting compressor efficiency map: {e}")
            return {'error': str(e)}
    
    # ===== PREDICTIVE MAINTENANCE API =====
    
    def get_maintenance_recommendations(self) -> Dict[str, Any]:
        """
        Get comprehensive maintenance recommendations based on AI analysis
        
        Returns:
            Detailed maintenance analysis, alerts, and predictions
        """
        try:
            return self.predictive_maintenance.get_maintenance_recommendations()
        except Exception as e:
            self.logger.error(f"Error getting maintenance recommendations: {e}")
            return {'error': str(e)}
    
    def get_oil_analysis(self) -> Dict[str, Any]:
        """
        Get detailed oil condition analysis and change recommendations
        
        Returns:
            Comprehensive oil analysis based on driving conditions
        """
        try:
            return self.predictive_maintenance.get_oil_analysis()
        except Exception as e:
            self.logger.error(f"Error getting oil analysis: {e}")
            return {'error': str(e)}
    
    def get_turbo_health_prediction(self) -> Dict[str, Any]:
        """
        Get turbo health prediction and maintenance forecast
        
        Returns:
            Turbo health analysis with degradation predictions
        """
        try:
            return self.predictive_maintenance.get_turbo_health_prediction()
        except Exception as e:
            self.logger.error(f"Error getting turbo health prediction: {e}")
            return {'error': str(e)}
    
    def get_dtc_pattern_analysis(self) -> Dict[str, Any]:
        """
        Get DTC pattern analysis with failure predictions
        
        Returns:
            DTC pattern insights with predictive failure analysis
        """
        try:
            return self.predictive_maintenance.get_dtc_pattern_analysis()
        except Exception as e:
            self.logger.error(f"Error getting DTC pattern analysis: {e}")
            return {'error': str(e)}
    
    def record_maintenance_event(self, event_type: str, mileage: int = None, 
                                notes: str = None) -> Dict[str, Any]:
        """
        Record a maintenance event for pattern learning
        
        Args:
            event_type: Type of maintenance performed
            mileage: Mileage at which maintenance was performed
            notes: Additional notes about the maintenance
            
        Returns:
            Confirmation of recorded maintenance event
        """
        try:
            self.predictive_maintenance.record_maintenance_event(event_type, mileage, notes)
            return {
                'status': 'recorded',
                'event_type': event_type,
                'mileage': mileage or self.vehicle_info.get('mileage', 0),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error recording maintenance event: {e}")
            return {'error': str(e)}
    
    def export_health_report(self, format_type: str = "json") -> Dict[str, Any]:
        """
        Export comprehensive vehicle health report
        
        Args:
            format_type: Export format ("json", "csv")
            
        Returns:
            Complete vehicle health report
        """
        try:
            report = self.predictive_maintenance.export_health_report(format_type)
            return {
                'status': 'success',
                'format': format_type,
                'report': report,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error exporting health report: {e}")
            return {'error': str(e)}
    
    # ===== ADVANCED DIAGNOSTICS API =====
    
    def get_advanced_diagnostics(self) -> Dict[str, Any]:
        """
        Get advanced diagnostic analysis combining all modules
        
        Returns:
            Comprehensive advanced diagnostics report
        """
        try:
            # Gather data from all analytics modules
            performance_data = self.get_performance_data()
            turbo_summary = self.get_turbo_performance_summary()
            maintenance_rec = self.get_maintenance_recommendations()
            
            # Combine into comprehensive report
            advanced_diagnostics = {
                'timestamp': datetime.now().isoformat(),
                'vehicle_status': {
                    'connection_status': 'connected' if self.is_connected() else 'disconnected',
                    'bmw_generation': self.config.generation,
                    'data_quality': self._assess_data_quality()
                },
                'performance_analytics': performance_data,
                'turbo_analytics': turbo_summary,
                'predictive_maintenance': maintenance_rec,
                'safety_confirmation': {
                    'read_only_operation': True,
                    'no_ecu_modifications': True,
                    'data_collection_only': True
                }
            }
            
            return advanced_diagnostics
            
        except Exception as e:
            self.logger.error(f"Error getting advanced diagnostics: {e}")
            return {'error': str(e)}
    
    def _assess_data_quality(self) -> Dict[str, Any]:
        """Assess the quality of collected data"""
        try:
            if not self.live_data_cache:
                return {'quality': 'no_data', 'completeness': 0}
            
            data = self.live_data_cache.get('data', {})
            expected_fields = ['RPM', 'SPEED', 'COOLANT_TEMP', 'ENGINE_LOAD', 'THROTTLE_POS']
            
            available_fields = len([field for field in expected_fields if field in data])
            completeness = (available_fields / len(expected_fields)) * 100
            
            quality = "excellent" if completeness > 90 else \
                     "good" if completeness > 70 else \
                     "fair" if completeness > 50 else "poor"
            
            return {
                'quality': quality,
                'completeness': round(completeness, 1),
                'available_parameters': available_fields,
                'last_update': self.last_data_update.isoformat() if self.last_data_update else None
            }
            
        except Exception as e:
            return {'quality': 'error', 'error': str(e)}
    
    # Override get_dtcs to also update DTC patterns
    # (This method replaces the original get_dtcs method above)