"""
Tests for BMW Diagnostics main class

These tests validate the BMWDiagnostics class functionality,
focusing on configuration and API interface validation.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from obd2_diagnostics.bmw_diagnostics import BMWDiagnostics
from obd2_diagnostics.config import OBD2Config, AdapterType, ConnectionType, Protocol


class TestBMWDiagnostics(unittest.TestCase):
    """Test BMW Diagnostics functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = OBD2Config()
        self.config.port = "/dev/ttyUSB0"  # Mock port
        
    def test_initialization(self):
        """Test BMWDiagnostics initialization"""
        diagnostics = BMWDiagnostics(self.config)
        
        self.assertIsNotNone(diagnostics.config)
        self.assertIsNotNone(diagnostics.adapter)
        self.assertIsNotNone(diagnostics.dtc_handler)
        self.assertFalse(diagnostics.connected)
        self.assertEqual(diagnostics.config.generation, "F13")
    
    def test_initialization_without_config(self):
        """Test initialization with default config"""
        diagnostics = BMWDiagnostics()
        
        self.assertIsNotNone(diagnostics.config)
        self.assertEqual(diagnostics.config.generation, "F13")
        self.assertEqual(diagnostics.config.adapter_type, AdapterType.AUTO)
    
    def test_connection_interface(self):
        """Test connection interface methods"""
        diagnostics = BMWDiagnostics(self.config)
        
        # Test initial state
        self.assertFalse(diagnostics.is_connected())
        
        # Test connection callbacks
        callback_called = False
        def test_callback(connected, error):
            nonlocal callback_called
            callback_called = True
        
        diagnostics.add_connection_callback(test_callback)
        self.assertEqual(len(diagnostics.connection_callbacks), 1)
    
    def test_bmw_config_setting(self):
        """Test BMW model configuration setting"""
        diagnostics = BMWDiagnostics(self.config)
        
        # Test setting valid BMW config
        diagnostics.set_bmw_config("F13_650i")
        self.assertEqual(diagnostics.config.generation, "F13")
        self.assertEqual(diagnostics.config.engine_type, "N63")
        
        # Test setting invalid config (should not crash)
        diagnostics.set_bmw_config("INVALID_MODEL")
        # Should still have previous valid config
        self.assertEqual(diagnostics.config.generation, "F13")
    
    def test_context_manager(self):
        """Test context manager functionality"""
        with patch.object(BMWDiagnostics, 'disconnect') as mock_disconnect:
            with BMWDiagnostics(self.config) as diagnostics:
                self.assertIsInstance(diagnostics, BMWDiagnostics)
            
            # Disconnect should be called on exit
            mock_disconnect.assert_called_once()
    
    def test_string_representation(self):
        """Test string representation"""
        diagnostics = BMWDiagnostics(self.config)
        repr_str = repr(diagnostics)
        
        self.assertIn("BMWDiagnostics", repr_str)
        self.assertIn("Disconnected", repr_str)
        self.assertIn("F13", repr_str)
    
    @patch('obd2_diagnostics.bmw_diagnostics.OBD2Adapter')
    def test_api_methods_disconnected(self, mock_adapter_class):
        """Test API methods when disconnected"""
        # Mock adapter to return disconnected state
        mock_adapter = Mock()
        mock_adapter.is_connected.return_value = False
        mock_adapter_class.return_value = mock_adapter
        
        diagnostics = BMWDiagnostics(self.config)
        
        # Test methods that require connection
        live_data = diagnostics.get_live_data()
        self.assertEqual(live_data, {})
        
        dtcs = diagnostics.get_dtcs()
        self.assertIn('error', dtcs)
        
        clear_result = diagnostics.clear_dtcs()
        self.assertFalse(clear_result)
        
        readiness = diagnostics.perform_readiness_test()
        self.assertIn('error', readiness)
        
        summary = diagnostics.get_diagnostic_summary()
        self.assertIn('error', summary)
    
    def test_vehicle_info_structure(self):
        """Test vehicle info structure"""
        diagnostics = BMWDiagnostics(self.config)
        
        # When disconnected, should return empty dict
        vehicle_info = diagnostics.get_vehicle_info()
        self.assertEqual(vehicle_info, {})
    
    def test_adapter_info_structure(self):
        """Test adapter info includes BMW-specific information"""
        with patch.object(BMWDiagnostics, '_update_vehicle_info'):
            diagnostics = BMWDiagnostics(self.config)
            
            # Mock adapter info
            diagnostics.adapter.get_adapter_info = Mock(return_value={
                'status': 'CONNECTED',
                'protocol': 'ISO_15765_4'
            })
            
            adapter_info = diagnostics.get_adapter_info()
            
            # Should include BMW-specific information
            self.assertIn('bmw_support', adapter_info)
            self.assertIn('bmw_generation', adapter_info)
            self.assertIn('config', adapter_info)
            self.assertTrue(adapter_info['bmw_support'])
            self.assertEqual(adapter_info['bmw_generation'], 'F13')


class TestBMWDiagnosticsIntegration(unittest.TestCase):
    """Integration tests for BMW Diagnostics"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.config = OBD2Config()
        self.config.port = "/dev/null"  # Non-existent port for testing
        self.config.timeout = 1.0  # Short timeout for tests
    
    def test_connection_failure_handling(self):
        """Test handling of connection failures"""
        diagnostics = BMWDiagnostics(self.config)
        
        # Connection should fail with non-existent port
        result = diagnostics.connect(auto_detect=False)
        self.assertFalse(result)
        self.assertFalse(diagnostics.is_connected())
    
    def test_auto_detect_with_no_adapters(self):
        """Test auto-detection when no adapters are available"""
        with patch('obd2_diagnostics.obd2_adapter.AdapterDiscovery.auto_detect_adapter') as mock_detect:
            mock_detect.return_value = None
            
            diagnostics = BMWDiagnostics(self.config)
            result = diagnostics.connect(auto_detect=True)
            
            self.assertFalse(result)
            mock_detect.assert_called_once()


if __name__ == '__main__':
    unittest.main()