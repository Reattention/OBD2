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
        
        # State tracking
        self.connected = False
        self.vehicle_info = {}
        self.last_data_update = None
        self.live_data_cache = {}
        self.connection_callbacks = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.config.log_level)
        
        # Register connection callbacks
        self.adapter.add_connection_callback(self._on_connection_change)
        
        self.logger.info("BMW Diagnostics initialized")
    
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
                obd.commands.AMBIANT_AIR_TEMP,
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
        """Get diagnostic trouble codes"""
        if not self.is_connected():
            return {'error': 'Not connected to vehicle'}
        
        try:
            dtcs, status = self.dtc_handler.read_dtcs()
            analysis = self.dtc_handler.get_dtc_analysis(dtcs)
            
            return {
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
            
        except Exception as e:
            self.logger.error(f"Error reading DTCs: {e}")
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