"""
Tests for OBD2 Adapter communication

These tests validate the OBD2Adapter class functionality,
focusing on connection handling and communication logic.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import threading
import time
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from obd2_diagnostics.obd2_adapter import OBD2Adapter, ConnectionStatus, AdapterDiscovery
from obd2_diagnostics.config import OBD2Config, AdapterType, ConnectionType, Protocol


class TestOBD2Adapter(unittest.TestCase):
    """Test OBD2 Adapter functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = OBD2Config()
        self.config.port = "/dev/ttyUSB0"
        self.config.timeout = 5.0
        
    def test_initialization(self):
        """Test OBD2Adapter initialization"""
        adapter = OBD2Adapter(self.config)
        
        self.assertEqual(adapter.config, self.config)
        self.assertIsNone(adapter.connection)
        self.assertEqual(adapter.status, ConnectionStatus.DISCONNECTED)
        self.assertIsNone(adapter.last_error)
        self.assertEqual(len(adapter.supported_commands), 0)
        self.assertEqual(len(adapter.protocols), 0)
    
    def test_connection_callbacks(self):
        """Test connection callback system"""
        adapter = OBD2Adapter(self.config)
        
        # Test adding callbacks
        callback_calls = []
        def test_callback(status, error):
            callback_calls.append((status, error))
        
        adapter.add_connection_callback(test_callback)
        self.assertEqual(len(adapter._connection_callbacks), 1)
        
        # Test callback notification
        adapter._notify_connection_change(ConnectionStatus.CONNECTING)
        self.assertEqual(len(callback_calls), 1)
        self.assertEqual(callback_calls[0][0], ConnectionStatus.CONNECTING)
        self.assertIsNone(callback_calls[0][1])
        
        # Test callback with error
        adapter._notify_connection_change(ConnectionStatus.ERROR, "Test error")
        self.assertEqual(len(callback_calls), 2)
        self.assertEqual(callback_calls[1][0], ConnectionStatus.ERROR)
        self.assertEqual(callback_calls[1][1], "Test error")
    
    def test_connection_args_generation(self):
        """Test connection arguments generation"""
        adapter = OBD2Adapter(self.config)
        
        # Test default args
        args = adapter._get_connection_args()
        self.assertEqual(args['portstr'], '/dev/ttyUSB0')
        self.assertEqual(args['baudrate'], 38400)
        self.assertEqual(args['timeout'], 5.0)
        
        # Test with specific protocol
        self.config.protocol = Protocol.ISO_15765_4
        args = adapter._get_connection_args()
        self.assertIn('protocol', args)
    
    def test_is_connected_logic(self):
        """Test connection status logic"""
        adapter = OBD2Adapter(self.config)
        
        # Initially disconnected
        self.assertFalse(adapter.is_connected())
        
        # Mock connected state
        adapter.status = ConnectionStatus.CONNECTED
        mock_connection = Mock()
        mock_connection.status = Mock()
        mock_connection.status.__eq__ = Mock(return_value=True)
        adapter.connection = mock_connection
        
        # Should still be False without proper OBD status
        self.assertFalse(adapter.is_connected())
    
    def test_disconnect_cleanup(self):
        """Test disconnect cleanup"""
        adapter = OBD2Adapter(self.config)
        
        # Mock a connection
        mock_connection = Mock()
        adapter.connection = mock_connection
        adapter.supported_commands = ['test_cmd']
        adapter.protocols = ['test_protocol']
        adapter.status = ConnectionStatus.CONNECTED
        
        # Test disconnect
        adapter.disconnect()
        
        # Verify cleanup
        mock_connection.close.assert_called_once()
        self.assertIsNone(adapter.connection)
        self.assertEqual(len(adapter.supported_commands), 0)
        self.assertEqual(len(adapter.protocols), 0)
        self.assertEqual(adapter.status, ConnectionStatus.DISCONNECTED)
    
    @patch('obd2_diagnostics.obd2_adapter.obd')
    def test_query_command_retry_logic(self, mock_obd):
        """Test command query retry logic"""
        adapter = OBD2Adapter(self.config)
        adapter.status = ConnectionStatus.CONNECTED
        
        # Mock connection and command
        mock_connection = Mock()
        mock_command = Mock()
        mock_command.name = "TEST_COMMAND"
        
        # Mock successful response after retry
        mock_response_null = Mock()
        mock_response_null.is_null.return_value = True
        
        mock_response_success = Mock()
        mock_response_success.is_null.return_value = False
        
        mock_connection.query.side_effect = [mock_response_null, mock_response_success]
        mock_connection.status = mock_obd.OBDStatus.CAR_CONNECTED
        adapter.connection = mock_connection
        
        result = adapter.query_command(mock_command, retries=1)
        
        # Should have retried and succeeded
        self.assertEqual(mock_connection.query.call_count, 2)
        self.assertEqual(result, mock_response_success)
    
    def test_multiple_commands_query(self):
        """Test querying multiple commands"""
        adapter = OBD2Adapter(self.config)
        adapter.status = ConnectionStatus.CONNECTED
        
        # Mock commands
        cmd1 = Mock()
        cmd1.name = "CMD1"
        cmd2 = Mock()
        cmd2.name = "CMD2"
        
        commands = [cmd1, cmd2]
        
        # Mock query_command method
        adapter.query_command = Mock(side_effect=lambda cmd: f"response_{cmd.name}")
        adapter.supported_commands = commands  # All commands supported
        
        results = adapter.query_multiple_commands(commands)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results['CMD1'], 'response_CMD1')
        self.assertEqual(results['CMD2'], 'response_CMD2')
    
    def test_adapter_info_structure(self):
        """Test adapter info structure"""
        adapter = OBD2Adapter(self.config)
        
        # When disconnected
        info = adapter.get_adapter_info()
        self.assertEqual(info, {})
        
        # Mock connected state
        adapter.status = ConnectionStatus.CONNECTED
        mock_connection = Mock()
        mock_connection.status.name = "CAR_CONNECTED"
        mock_connection.protocol.name = "ISO_15765_4"
        mock_connection.protocol.value = "6"
        mock_connection.interface.port_name = "/dev/ttyUSB0"
        adapter.connection = mock_connection
        adapter.supported_commands = ['cmd1', 'cmd2']
        adapter.protocols = ['ISO_15765_4']
        
        info = adapter.get_adapter_info()
        
        self.assertEqual(info['status'], 'CAR_CONNECTED')
        self.assertEqual(info['protocol'], 'ISO_15765_4')
        self.assertEqual(info['protocol_id'], '6')
        self.assertEqual(info['port'], '/dev/ttyUSB0')
        self.assertEqual(info['supported_commands_count'], 2)
        self.assertEqual(info['detected_protocols'], ['ISO_15765_4'])


class TestAdapterDiscovery(unittest.TestCase):
    """Test adapter discovery functionality"""
    
    @patch('obd2_diagnostics.obd2_adapter.serial.tools.list_ports')
    def test_scan_ports(self, mock_list_ports):
        """Test port scanning"""
        # Mock available ports
        mock_port1 = Mock()
        mock_port1.device = '/dev/ttyUSB0'
        mock_port2 = Mock()
        mock_port2.device = '/dev/ttyUSB1'
        
        mock_list_ports.comports.return_value = [mock_port1, mock_port2]
        
        ports = AdapterDiscovery.scan_ports()
        self.assertEqual(len(ports), 2)
        self.assertIn('/dev/ttyUSB0', ports)
        self.assertIn('/dev/ttyUSB1', ports)
    
    def test_scan_ports_without_serial(self):
        """Test port scanning when pyserial is not available"""
        with patch('obd2_diagnostics.obd2_adapter.serial', None):
            ports = AdapterDiscovery.scan_ports()
            self.assertEqual(ports, [])
    
    @patch('obd2_diagnostics.obd2_adapter.bluetooth')
    def test_scan_bluetooth(self, mock_bluetooth):
        """Test Bluetooth scanning"""
        # Mock Bluetooth devices
        mock_bluetooth.discover_devices.return_value = [
            ('00:11:22:33:44:55', 'ELM327-Device'),
            ('00:11:22:33:44:56', 'Regular Device'),
            ('00:11:22:33:44:57', 'OBDLink Scanner')
        ]
        
        devices = AdapterDiscovery.scan_bluetooth()
        
        # Should find 2 OBD devices
        self.assertEqual(len(devices), 2)
        device_names = [dev['name'] for dev in devices]
        self.assertIn('ELM327-Device', device_names)
        self.assertIn('OBDLink Scanner', device_names)
    
    def test_scan_bluetooth_without_bluetooth(self):
        """Test Bluetooth scanning when bluetooth library is not available"""
        with patch('obd2_diagnostics.obd2_adapter.bluetooth', None):
            devices = AdapterDiscovery.scan_bluetooth()
            self.assertEqual(devices, [])
    
    @patch.object(AdapterDiscovery, 'scan_ports')
    @patch.object(OBD2Adapter, 'connect')
    @patch.object(OBD2Adapter, 'disconnect')
    def test_auto_detect_adapter(self, mock_disconnect, mock_connect, mock_scan_ports):
        """Test auto-detection of adapter"""
        # Mock available ports
        mock_scan_ports.return_value = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2']
        
        # Mock successful connection on second port
        mock_connect.side_effect = [False, True, False]
        
        config = OBD2Config()
        result = AdapterDiscovery.auto_detect_adapter(config)
        
        # Should return the port that connected successfully
        self.assertEqual(result, '/dev/ttyUSB1')
        self.assertEqual(mock_connect.call_count, 2)  # Stopped after successful connection
        mock_disconnect.assert_called_once()


class TestOBD2AdapterThreading(unittest.TestCase):
    """Test threading functionality of OBD2Adapter"""
    
    def setUp(self):
        """Set up threading test fixtures"""
        self.config = OBD2Config()
        self.config.reconnect_delay = 0.1  # Short delay for testing
    
    def test_reconnection_thread_lifecycle(self):
        """Test reconnection thread start and stop"""
        adapter = OBD2Adapter(self.config)
        
        # Start auto-reconnect
        adapter.start_auto_reconnect()
        
        # Thread should be created and running
        self.assertIsNotNone(adapter._reconnect_thread)
        self.assertTrue(adapter._reconnect_thread.is_alive())
        
        # Stop reconnection
        adapter._stop_reconnect.set()
        
        # Wait for thread to finish
        adapter._reconnect_thread.join(timeout=1.0)
        self.assertFalse(adapter._reconnect_thread.is_alive())
    
    def test_disconnect_stops_reconnection(self):
        """Test that disconnect stops reconnection thread"""
        adapter = OBD2Adapter(self.config)
        
        # Start auto-reconnect
        adapter.start_auto_reconnect()
        thread = adapter._reconnect_thread
        
        # Disconnect should stop the thread
        adapter.disconnect()
        
        # Wait and check thread is stopped
        time.sleep(0.2)
        self.assertFalse(thread.is_alive())


if __name__ == '__main__':
    unittest.main()