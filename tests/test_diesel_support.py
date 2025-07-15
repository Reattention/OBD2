"""
Tests for N57D30 Diesel Engine Support

These tests validate the diesel-specific functionality added for BMW N57D30 engine support.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from obd2_diagnostics.bmw_pids import bmw_pid_registry, standard_pid_mapper
from obd2_diagnostics.dtc_handler import DTCHandler, DiagnosticTroubleCode, DTCSeverity
from obd2_diagnostics.config import OBD2Config, BMW_CONFIGS
from obd2_diagnostics.bmw_diagnostics import BMWDiagnostics


class TestDieselPIDSupport(unittest.TestCase):
    """Test diesel-specific PID functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pid_registry = bmw_pid_registry
        self.pid_mapper = standard_pid_mapper
    
    def test_diesel_pid_registry(self):
        """Test that diesel PIDs are registered"""
        diesel_pids = [
            'BMW_DPF_PRESSURE_DIFFERENTIAL',
            'BMW_DPF_REGENERATION_STATUS',
            'BMW_EGR_VALVE_POSITION',
            'BMW_VNT_TURBO_POSITION',
            'BMW_NOX_SENSOR_BANK1',
            'BMW_NOX_SENSOR_BANK2',
            'BMW_DEF_TANK_LEVEL',
            'BMW_DEF_QUALITY',
            'BMW_DIESEL_FUEL_TEMP',
            'BMW_FUEL_RAIL_PRESSURE_HIGH',
            'BMW_DIESEL_INJECTION_TIMING'
        ]
        
        all_pids = self.pid_registry.get_all_pids()
        
        for pid_name in diesel_pids:
            self.assertIn(pid_name, all_pids, f"Diesel PID {pid_name} not found in registry")
            
            pid_def = all_pids[pid_name]
            self.assertIn('pid', pid_def)
            self.assertIn('name', pid_def)
            self.assertIn('description', pid_def)
            self.assertIn('unit', pid_def)
            self.assertIn('decoder', pid_def)
    
    def test_diesel_pid_decoders(self):
        """Test diesel PID decoder functions"""
        # Test DPF pressure decoder
        test_data = bytes([0x01, 0x90])  # Example data
        dpf_pressure = self.pid_registry._decode_bmw_dpf_pressure(test_data)
        self.assertIsInstance(dpf_pressure, float)
        self.assertGreaterEqual(dpf_pressure, 0)
        
        # Test EGR position decoder
        test_data = bytes([0x80])  # 50% position
        egr_position = self.pid_registry._decode_bmw_egr_position(test_data)
        self.assertIsInstance(egr_position, float)
        self.assertGreaterEqual(egr_position, 0)
        self.assertLessEqual(egr_position, 100)
        
        # Test NOx sensor decoder
        test_data = bytes([0x01, 0xF4])  # Example NOx reading
        nox_level = self.pid_registry._decode_bmw_nox_sensor(test_data)
        self.assertIsInstance(nox_level, float)
        self.assertGreaterEqual(nox_level, 0)
        
        # Test DEF level decoder
        test_data = bytes([0xCC])  # ~80% level
        def_level = self.pid_registry._decode_bmw_def_level(test_data)
        self.assertIsInstance(def_level, float)
        self.assertGreaterEqual(def_level, 0)
        self.assertLessEqual(def_level, 100)
    
    def test_diesel_specific_interpretations(self):
        """Test diesel-specific interpretations in standard PID mapper"""
        # Test that diesel-specific notes are included
        self.assertIn('diesel_specific_notes', dir(self.pid_mapper))
        
        diesel_notes = self.pid_mapper.diesel_specific_notes
        self.assertIn('dpf_notes', diesel_notes)
        self.assertIn('egr_notes', diesel_notes)
        self.assertIn('turbo_notes', diesel_notes)
        self.assertIn('nox_notes', diesel_notes)
        self.assertIn('def_notes', diesel_notes)
        
        # Test that interpretations include diesel notes
        mock_value = Mock()
        mock_value.magnitude = 50.0
        
        # Test fuel pressure interpretation with diesel notes
        import obd
        fuel_pressure_result = self.pid_mapper.interpret_value(obd.commands.FUEL_PRESSURE, mock_value)
        self.assertIn('diesel_notes', fuel_pressure_result)
        self.assertIn('Common rail', fuel_pressure_result['diesel_notes'])


class TestDieselDTCSupport(unittest.TestCase):
    """Test diesel-specific DTC functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = OBD2Config()
        self.mock_adapter = Mock()
        self.dtc_handler = DTCHandler(self.mock_adapter)
    
    def test_diesel_dtc_database(self):
        """Test that diesel DTCs are in the database"""
        diesel_dtcs = [
            # DPF codes
            'P2002', 'P2463', 'P244A', 'P244B',
            # EGR codes  
            'P0401', 'P0402', 'P0403', 'P0404',
            # NOx/SCR codes
            'P20EE', 'P2200', 'P2201', 'P2202',
            # DEF system codes
            'P229F', 'P204F', 'P205B', 'P205C',
            # Turbo codes
            'P2563', 'P2564', 'P2565', 'P2566',
            # Glow plug codes
            'P0380', 'P0381', 'P0670', 'P0671'
        ]
        
        dtc_db = self.dtc_handler.bmw_dtc_database
        
        for dtc_code in diesel_dtcs:
            self.assertIn(dtc_code, dtc_db, f"Diesel DTC {dtc_code} not found in database")
            description = dtc_db[dtc_code]
            self.assertIsInstance(description, str)
            self.assertGreater(len(description), 10)  # Reasonable description length
    
    def test_diesel_dtc_priority_detection(self):
        """Test that diesel DTCs are properly prioritized"""
        # Create diesel DTCs
        diesel_dtcs = [
            DiagnosticTroubleCode('P2002', 'DPF Efficiency Below Threshold'),
            DiagnosticTroubleCode('P2463', 'DPF Soot Accumulation'),
            DiagnosticTroubleCode('P0401', 'EGR Flow Insufficient'),
            DiagnosticTroubleCode('P20EE', 'NOx Catalyst Efficiency Low'),
            DiagnosticTroubleCode('P229F', 'DEF Pump Control Circuit')
        ]
        
        analysis = self.dtc_handler.get_dtc_analysis(diesel_dtcs)
        
        # All of these should be priority issues
        priority_issues = analysis.get('priority_issues', [])
        priority_codes = [issue['code'] for issue in priority_issues]
        
        for dtc in diesel_dtcs:
            self.assertIn(dtc.code, priority_codes, f"Diesel DTC {dtc.code} not identified as priority")
    
    def test_diesel_dtc_recommendations(self):
        """Test that diesel-specific recommendations are generated"""
        # Create DTCs that should trigger diesel recommendations
        test_dtcs = [
            DiagnosticTroubleCode('P2002', 'DPF Efficiency Below Threshold'),  # DPF
            DiagnosticTroubleCode('P0401', 'EGR Flow Insufficient'),           # EGR
            DiagnosticTroubleCode('P20EE', 'NOx Catalyst Efficiency Low'),     # NOx
            DiagnosticTroubleCode('P229F', 'DEF Pump Control Circuit'),        # DEF
            DiagnosticTroubleCode('P2563', 'Turbo Position Sensor'),           # Turbo
            DiagnosticTroubleCode('P0380', 'Glow Plug Circuit A')              # Glow plugs
        ]
        
        recommendations = self.dtc_handler._generate_recommendations(test_dtcs)
        
        # Check for diesel-specific recommendations
        rec_text = ' '.join(recommendations).lower()
        self.assertIn('dpf', rec_text)
        self.assertIn('egr', rec_text)
        self.assertIn('def', rec_text) or self.assertIn('adblue', rec_text)
        self.assertIn('turbo', rec_text)
        self.assertIn('glow', rec_text)
    
    def test_diesel_priority_reasons(self):
        """Test that diesel DTCs have appropriate priority reasons"""
        diesel_priority_codes = ['P2002', 'P2463', 'P0401', 'P20EE', 'P229F', 'P0299', 'P0380']
        
        for code in diesel_priority_codes:
            reason = self.dtc_handler._get_priority_reason(code)
            self.assertIsInstance(reason, str)
            self.assertGreater(len(reason), 10)  # Should have meaningful reason
            self.assertNotEqual(reason, 'Requires immediate attention')  # Should be specific


class TestDieselConfiguration(unittest.TestCase):
    """Test diesel engine configuration support"""
    
    def test_f13_535d_config_exists(self):
        """Test that F13_535d configuration exists and is properly structured"""
        self.assertIn('F13_535d', BMW_CONFIGS)
        
        config = BMW_CONFIGS['F13_535d']
        
        # Check basic BMW config fields
        self.assertEqual(config['generation'], 'F13')
        self.assertEqual(config['engine_type'], 'N57D30')
        self.assertIn('fuel_type', config)
        self.assertEqual(config['fuel_type'], 'diesel')
        
        # Check diesel-specific fields
        self.assertIn('diesel_specific', config)
        diesel_spec = config['diesel_specific']
        
        self.assertTrue(diesel_spec['dpf_equipped'])
        self.assertTrue(diesel_spec['scr_equipped'])
        self.assertTrue(diesel_spec['def_required'])
        self.assertTrue(diesel_spec['egr_equipped'])
        self.assertGreater(diesel_spec['common_rail_pressure_max'], 1000)
        self.assertGreater(diesel_spec['regeneration_interval_miles'], 0)
    
    def test_obd2_config_diesel_attributes(self):
        """Test that OBD2Config supports diesel-specific attributes"""
        config = OBD2Config()
        
        # Test that diesel attributes exist
        self.assertTrue(hasattr(config, 'fuel_type'))
        self.assertTrue(hasattr(config, 'emissions_standard'))
        self.assertTrue(hasattr(config, 'displacement_liters'))
        self.assertTrue(hasattr(config, 'cylinders'))
        self.assertTrue(hasattr(config, 'turbo_type'))
        self.assertTrue(hasattr(config, 'diesel_specific'))
        
        # Test default values
        self.assertEqual(config.fuel_type, 'gasoline')
        self.assertIsInstance(config.diesel_specific, dict)
    
    def test_diesel_config_loading(self):
        """Test loading diesel configuration from dictionary"""
        config = OBD2Config()
        
        test_config = {
            'engine_type': 'N57D30',
            'fuel_type': 'diesel',
            'emissions_standard': 'Euro5',
            'displacement_liters': 3.0,
            'cylinders': 6,
            'turbo_type': 'VNT',
            'diesel_specific': {
                'dpf_equipped': True,
                'scr_equipped': True
            }
        }
        
        config.from_dict(test_config)
        
        self.assertEqual(config.engine_type, 'N57D30')
        self.assertEqual(config.fuel_type, 'diesel')
        self.assertEqual(config.emissions_standard, 'Euro5')
        self.assertEqual(config.displacement_liters, 3.0)
        self.assertEqual(config.cylinders, 6)
        self.assertEqual(config.turbo_type, 'VNT')
        self.assertTrue(config.diesel_specific['dpf_equipped'])
        self.assertTrue(config.diesel_specific['scr_equipped'])
    
    def test_diesel_config_export(self):
        """Test exporting diesel configuration to dictionary"""
        config = OBD2Config()
        config.fuel_type = 'diesel'
        config.engine_type = 'N57D30'
        config.diesel_specific = {'dpf_equipped': True}
        
        config_dict = config.to_dict()
        
        self.assertEqual(config_dict['fuel_type'], 'diesel')
        self.assertEqual(config_dict['engine_type'], 'N57D30')
        self.assertIn('diesel_specific', config_dict)
        self.assertTrue(config_dict['diesel_specific']['dpf_equipped'])


class TestDieselBMWDiagnosticsIntegration(unittest.TestCase):
    """Test integration of diesel support with main BMW diagnostics"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = OBD2Config()
        self.config.port = "/dev/null"  # Test port
    
    def test_f13_535d_config_setting(self):
        """Test setting F13_535d configuration"""
        diagnostics = BMWDiagnostics(self.config)
        
        # Set diesel configuration
        diagnostics.set_bmw_config("F13_535d")
        
        # Verify configuration was applied
        self.assertEqual(diagnostics.config.generation, "F13")
        self.assertEqual(diagnostics.config.engine_type, "N57D30")
        self.assertEqual(diagnostics.config.fuel_type, "diesel")
        self.assertIn('diesel_specific', diagnostics.config.to_dict())
    
    def test_diesel_diagnostics_initialization(self):
        """Test that diagnostics initializes properly with diesel config"""
        self.config.fuel_type = 'diesel'
        self.config.engine_type = 'N57D30'
        
        diagnostics = BMWDiagnostics(self.config)
        
        self.assertIsNotNone(diagnostics.config)
        self.assertIsNotNone(diagnostics.adapter)
        self.assertIsNotNone(diagnostics.dtc_handler)
        self.assertEqual(diagnostics.config.fuel_type, 'diesel')
        self.assertEqual(diagnostics.config.engine_type, 'N57D30')
    
    @patch('obd2_diagnostics.bmw_diagnostics.OBD2Adapter')
    def test_diesel_specific_data_structure(self, mock_adapter_class):
        """Test that diesel-specific data is included in live data"""
        # Mock adapter
        mock_adapter = Mock()
        mock_adapter.is_connected.return_value = True
        mock_adapter.query_multiple_commands.return_value = {}
        mock_adapter_class.return_value = mock_adapter
        
        diagnostics = BMWDiagnostics(self.config)
        diagnostics.set_bmw_config("F13_535d")
        diagnostics.connected = True
        
        # Get live data
        live_data = diagnostics.get_live_data()
        
        # Should include BMW-specific data structure
        self.assertIn('bmw_specific', live_data)
        bmw_data = live_data['bmw_specific']
        
        # Should have diesel-related notes or data
        self.assertIn('note', bmw_data)


if __name__ == '__main__':
    unittest.main()