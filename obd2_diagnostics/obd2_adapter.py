"""
OBD2 Adapter Communication Module

Handles real OBD2 adapter communication using python-OBD library,
supporting multiple adapter types and connection methods.
"""

import obd
import logging
import time
import threading
from typing import Optional, Dict, Any, List, Callable
from enum import Enum

from .config import OBD2Config, AdapterType, ConnectionType, Protocol


class ConnectionStatus(Enum):
    """Connection status enumeration"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class OBD2Adapter:
    """OBD2 Adapter communication handler"""
    
    def __init__(self, config: OBD2Config):
        self.config = config
        self.connection: Optional[obd.OBD] = None
        self.status = ConnectionStatus.DISCONNECTED
        self.last_error: Optional[str] = None
        self.supported_commands: List[obd.OBDCommand] = []
        self.protocols: List[str] = []
        
        # Threading and reconnection
        self._reconnect_thread: Optional[threading.Thread] = None
        self._stop_reconnect = threading.Event()
        self._connection_callbacks: List[Callable] = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(config.log_level)
        
        if config.log_file:
            handler = logging.FileHandler(config.log_file)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def add_connection_callback(self, callback: Callable[[ConnectionStatus, Optional[str]], None]):
        """Add callback for connection status changes"""
        self._connection_callbacks.append(callback)
    
    def _notify_connection_change(self, status: ConnectionStatus, error: Optional[str] = None):
        """Notify all callbacks of connection status change"""
        self.status = status
        self.last_error = error
        for callback in self._connection_callbacks:
            try:
                callback(status, error)
            except Exception as e:
                self.logger.error(f"Error in connection callback: {e}")
    
    def connect(self) -> bool:
        """Connect to OBD2 adapter"""
        try:
            self._notify_connection_change(ConnectionStatus.CONNECTING)
            self.logger.info("Attempting to connect to OBD2 adapter...")
            
            # Determine connection parameters
            connection_args = self._get_connection_args()
            
            # Create OBD connection
            if self.config.fast_mode:
                self.connection = obd.OBD(**connection_args, fast=True)
            else:
                self.connection = obd.OBD(**connection_args)
            
            if self.connection.status == obd.OBDStatus.CAR_CONNECTED:
                self.logger.info("Successfully connected to vehicle ECU")
                self._update_supported_commands()
                self._detect_protocols()
                self._notify_connection_change(ConnectionStatus.CONNECTED)
                return True
            else:
                error_msg = f"Failed to connect: {self.connection.status}"
                self.logger.error(error_msg)
                self._notify_connection_change(ConnectionStatus.ERROR, error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            self.logger.error(error_msg)
            self._notify_connection_change(ConnectionStatus.ERROR, error_msg)
            return False
    
    def disconnect(self):
        """Disconnect from OBD2 adapter"""
        try:
            self._stop_reconnect.set()
            if self._reconnect_thread and self._reconnect_thread.is_alive():
                self._reconnect_thread.join(timeout=5.0)
            
            if self.connection:
                self.connection.close()
                self.connection = None
                
            self.supported_commands.clear()
            self.protocols.clear()
            self._notify_connection_change(ConnectionStatus.DISCONNECTED)
            self.logger.info("Disconnected from OBD2 adapter")
            
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
    
    def is_connected(self) -> bool:
        """Check if adapter is connected"""
        return (self.connection is not None and 
                self.connection.status == obd.OBDStatus.CAR_CONNECTED and
                self.status == ConnectionStatus.CONNECTED)
    
    def query_command(self, command, retries: Optional[int] = None) -> Optional[obd.OBDResponse]:
        """Query a specific OBD command with retry logic"""
        if not self.is_connected():
            self.logger.warning("Cannot query - not connected to adapter")
            return None
        
        max_retries = retries if retries is not None else self.config.retry_attempts
        
        for attempt in range(max_retries + 1):
            try:
                response = self.connection.query(command)
                
                if response.is_null():
                    if attempt < max_retries:
                        self.logger.warning(f"Null response for {command.name}, retrying ({attempt + 1}/{max_retries})")
                        time.sleep(0.1)
                        continue
                    else:
                        self.logger.error(f"Failed to get valid response for {command.name} after {max_retries} retries")
                        return None
                
                return response
                
            except Exception as e:
                if attempt < max_retries:
                    self.logger.warning(f"Error querying {command.name}, retrying ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(0.1)
                    continue
                else:
                    self.logger.error(f"Failed to query {command.name} after {max_retries} retries: {e}")
                    # Connection might be lost, start reconnection
                    if self.is_connected():
                        self._start_reconnection()
                    return None
        
        return None
    
    def query_multiple_commands(self, commands: List[obd.OBDCommand]) -> Dict[str, Optional[obd.OBDResponse]]:
        """Query multiple commands efficiently"""
        results = {}
        
        for command in commands:
            if command in self.supported_commands or self.config.bmw_extended_pids:
                results[command.name] = self.query_command(command)
            else:
                self.logger.debug(f"Command {command.name} not supported by ECU")
                results[command.name] = None
        
        return results
    
    def send_raw_command(self, raw_command: str) -> Optional[str]:
        """Send raw AT/OBD command to adapter"""
        if not self.is_connected():
            return None
        
        try:
            # Use the raw query method if available
            if hasattr(self.connection, 'send_and_parse'):
                response = self.connection.send_and_parse(raw_command)
                return response
            else:
                self.logger.warning("Raw command sending not supported by this OBD library version")
                return None
                
        except Exception as e:
            self.logger.error(f"Error sending raw command '{raw_command}': {e}")
            return None
    
    def get_adapter_info(self) -> Dict[str, Any]:
        """Get information about the connected adapter"""
        if not self.is_connected():
            return {}
        
        info = {
            'status': self.connection.status.name,
            'protocol': self.connection.protocol.name if self.connection.protocol else 'Unknown',
            'protocol_id': self.connection.protocol.value if self.connection.protocol else None,
            'port': self.connection.interface.port_name if hasattr(self.connection.interface, 'port_name') else 'Unknown',
            'supported_commands_count': len(self.supported_commands),
            'detected_protocols': self.protocols
        }
        
        return info
    
    def start_auto_reconnect(self):
        """Start automatic reconnection on connection loss"""
        if not self._reconnect_thread or not self._reconnect_thread.is_alive():
            self._stop_reconnect.clear()
            self._reconnect_thread = threading.Thread(target=self._reconnection_loop, daemon=True)
            self._reconnect_thread.start()
    
    def _get_connection_args(self) -> Dict[str, Any]:
        """Get connection arguments based on configuration"""
        args = {}
        
        # Set port if specified
        if self.config.port:
            args['portstr'] = self.config.port
        
        # Set baudrate
        args['baudrate'] = self.config.baudrate
        
        # Set timeout
        args['timeout'] = self.config.timeout
        
        # Set protocol if specified
        if self.config.protocol != Protocol.AUTO:
            protocol_map = {
                Protocol.ISO_15765_4: obd.protocols.ISO_15765_4_11bit_500k,
                Protocol.ISO_14230_4: obd.protocols.ISO_14230_4_fast,
                Protocol.ISO_9141_2: obd.protocols.ISO_9141_2,
                Protocol.SAE_J1850_PWM: obd.protocols.SAE_J1850_PWM,
                Protocol.SAE_J1850_VPW: obd.protocols.SAE_J1850_VPW
            }
            if self.config.protocol in protocol_map:
                args['protocol'] = protocol_map[self.config.protocol]
        
        return args
    
    def _update_supported_commands(self):
        """Update list of supported commands"""
        if not self.connection:
            return
        
        try:
            self.supported_commands = list(self.connection.supported_commands)
            self.logger.info(f"ECU supports {len(self.supported_commands)} commands")
            
            # Log some key supported commands
            key_commands = [
                obd.commands.RPM,
                obd.commands.SPEED,
                obd.commands.COOLANT_TEMP,
                obd.commands.ENGINE_LOAD,
                obd.commands.GET_DTC,
                obd.commands.CLEAR_DTC
            ]
            
            for cmd in key_commands:
                if cmd in self.supported_commands:
                    self.logger.debug(f"✓ {cmd.name} supported")
                else:
                    self.logger.debug(f"✗ {cmd.name} not supported")
                    
        except Exception as e:
            self.logger.error(f"Error updating supported commands: {e}")
    
    def _detect_protocols(self):
        """Detect available OBD2 protocols"""
        if not self.connection:
            return
        
        try:
            if self.connection.protocol:
                self.protocols = [self.connection.protocol.name]
                self.logger.info(f"Using protocol: {self.connection.protocol.name}")
            else:
                self.logger.warning("No protocol detected")
                
        except Exception as e:
            self.logger.error(f"Error detecting protocols: {e}")
    
    def _start_reconnection(self):
        """Start reconnection process"""
        if self.status != ConnectionStatus.RECONNECTING:
            self._notify_connection_change(ConnectionStatus.RECONNECTING)
            if not self._reconnect_thread or not self._reconnect_thread.is_alive():
                self.start_auto_reconnect()
    
    def _reconnection_loop(self):
        """Automatic reconnection loop"""
        while not self._stop_reconnect.is_set():
            if not self.is_connected() and self.status == ConnectionStatus.RECONNECTING:
                self.logger.info("Attempting to reconnect...")
                
                try:
                    # Clean up current connection
                    if self.connection:
                        self.connection.close()
                        self.connection = None
                    
                    # Wait before reconnection attempt
                    time.sleep(self.config.reconnect_delay)
                    
                    # Attempt reconnection
                    if self.connect():
                        self.logger.info("Reconnection successful")
                        break
                    else:
                        self.logger.warning("Reconnection failed, will retry...")
                        
                except Exception as e:
                    self.logger.error(f"Error during reconnection: {e}")
            
            time.sleep(1.0)


class AdapterDiscovery:
    """Discover available OBD2 adapters"""
    
    @staticmethod
    def scan_ports() -> List[str]:
        """Scan for available serial ports"""
        try:
            import serial.tools.list_ports
            ports = [port.device for port in serial.tools.list_ports.comports()]
            return ports
        except ImportError:
            logging.warning("pyserial not available for port scanning")
            return []
    
    @staticmethod
    def scan_bluetooth() -> List[Dict[str, str]]:
        """Scan for Bluetooth OBD2 adapters"""
        try:
            import bluetooth
            devices = []
            nearby_devices = bluetooth.discover_devices(lookup_names=True)
            
            for addr, name in nearby_devices:
                if any(obd_keyword in name.lower() for obd_keyword in ['obd', 'elm', 'obdlink']):
                    devices.append({'address': addr, 'name': name})
            
            return devices
        except ImportError:
            logging.warning("Bluetooth scanning not available - install pybluez")
            return []
    
    @staticmethod
    def auto_detect_adapter(config: OBD2Config) -> Optional[str]:
        """Auto-detect best available adapter"""
        # Try common ports first
        common_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', 'COM1', 'COM2', 'COM3']
        available_ports = AdapterDiscovery.scan_ports()
        
        # Prioritize common ports that exist
        test_ports = [port for port in common_ports if port in available_ports]
        test_ports.extend([port for port in available_ports if port not in test_ports])
        
        for port in test_ports:
            try:
                # Quick connection test
                test_config = OBD2Config()
                test_config.port = port
                test_config.timeout = 5.0
                
                adapter = OBD2Adapter(test_config)
                if adapter.connect():
                    adapter.disconnect()
                    logging.info(f"Auto-detected adapter on {port}")
                    return port
                    
            except Exception as e:
                logging.debug(f"Port {port} test failed: {e}")
                continue
        
        return None