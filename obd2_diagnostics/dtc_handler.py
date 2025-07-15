"""
Diagnostic Trouble Code (DTC) Handler

Handles reading, clearing, and interpreting DTCs from BMW vehicles.
Supports both standard OBD2 DTCs and BMW-specific codes.
"""

import obd
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from .obd2_adapter import OBD2Adapter


class DTCType(Enum):
    """DTC type classification"""
    POWERTRAIN = "P"
    CHASSIS = "C"
    BODY = "B"
    NETWORK = "U"


class DTCSeverity(Enum):
    """DTC severity levels"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PERMANENT = "permanent"


class DTCStatus:
    """DTC status information"""
    
    def __init__(self):
        self.mil_on = False  # Malfunction Indicator Light
        self.dtc_count = 0
        self.confirmed_dtc_count = 0
        self.pending_dtc_count = 0
        self.permanent_dtc_count = 0
        self.test_available = False
        self.test_incomplete = False


class DiagnosticTroubleCode:
    """Represents a single DTC"""
    
    def __init__(self, code: str, description: str = "", severity: DTCSeverity = DTCSeverity.CONFIRMED):
        self.code = code
        self.description = description
        self.severity = severity
        self.timestamp = datetime.now()
        self.freeze_frame_data = {}
        self.bmw_specific = self._is_bmw_specific()
        self.dtc_type = self._get_dtc_type()
    
    def _is_bmw_specific(self) -> bool:
        """Check if this is a BMW-specific DTC"""
        # BMW specific codes often start with certain patterns
        bmw_patterns = ['P1', 'P2', 'P3', 'B1', 'B2', 'C1', 'C2', 'U1', 'U2']
        return any(self.code.startswith(pattern) for pattern in bmw_patterns)
    
    def _get_dtc_type(self) -> DTCType:
        """Get DTC type from code"""
        if self.code.startswith('P'):
            return DTCType.POWERTRAIN
        elif self.code.startswith('C'):
            return DTCType.CHASSIS
        elif self.code.startswith('B'):
            return DTCType.BODY
        elif self.code.startswith('U'):
            return DTCType.NETWORK
        else:
            return DTCType.POWERTRAIN  # Default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DTC to dictionary"""
        return {
            'code': self.code,
            'description': self.description,
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'bmw_specific': self.bmw_specific,
            'dtc_type': self.dtc_type.value,
            'freeze_frame_data': self.freeze_frame_data
        }


class DTCHandler:
    """Handles DTC operations for BMW vehicles"""
    
    def __init__(self, adapter: OBD2Adapter):
        self.adapter = adapter
        self.logger = logging.getLogger(__name__)
        self._load_bmw_dtc_database()
    
    def _load_bmw_dtc_database(self):
        """Load BMW-specific DTC descriptions"""
        # BMW F13 specific DTCs (sample - would be expanded with full database)
        self.bmw_dtc_database = {
            # Engine DTCs
            'P0300': 'Random/Multiple Cylinder Misfire Detected',
            'P0301': 'Cylinder 1 Misfire Detected',
            'P0302': 'Cylinder 2 Misfire Detected',
            'P0303': 'Cylinder 3 Misfire Detected',
            'P0304': 'Cylinder 4 Misfire Detected',
            'P0305': 'Cylinder 5 Misfire Detected',
            'P0306': 'Cylinder 6 Misfire Detected',
            'P0307': 'Cylinder 7 Misfire Detected',
            'P0308': 'Cylinder 8 Misfire Detected',
            
            # BMW N63 Twin Turbo specific
            'P0299': 'Turbocharger/Supercharger "A" Underboost Condition',
            'P0234': 'Turbocharger/Supercharger "A" Overboost Condition',
            'P0235': 'Turbocharger/Supercharger "A" Boost Sensor "A" Circuit',
            'P0236': 'Turbocharger/Supercharger "A" Boost Sensor "A" Circuit Range/Performance',
            
            # BMW Valvetronic
            'P1014': 'Valvetronic Eccentric Shaft Sensor Circuit',
            'P1015': 'Valvetronic Eccentric Shaft Position Sensor Signal Implausible',
            'P1016': 'Valvetronic Motor Position Sensor Signal Implausible',
            'P1017': 'Valvetronic Emergency Mode Active',
            
            # BMW Direct Injection
            'P0087': 'Fuel Rail/System Pressure - Too Low',
            'P0088': 'Fuel Rail/System Pressure - Too High',
            'P0089': 'Fuel Pressure Regulator Performance',
            
            # BMW Transmission (ZF 8HP)
            'P0700': 'Transmission Control System Malfunction',
            'P0715': 'Input/Turbine Speed Sensor Circuit',
            'P0720': 'Output Speed Sensor Circuit',
            'P0731': 'Gear 1 Incorrect Ratio',
            'P0732': 'Gear 2 Incorrect Ratio',
            'P0733': 'Gear 3 Incorrect Ratio',
            'P0734': 'Gear 4 Incorrect Ratio',
            'P0735': 'Gear 5 Incorrect Ratio',
            'P0736': 'Reverse Incorrect Ratio',
            
            # BMW Chassis/Suspension
            'C1221': 'ABS Wheel Speed Sensor FR Signal Invalid',
            'C1222': 'ABS Wheel Speed Sensor FL Signal Invalid',
            'C1223': 'ABS Wheel Speed Sensor RR Signal Invalid',
            'C1224': 'ABS Wheel Speed Sensor RL Signal Invalid',
            'C1430': 'Air Suspension Compressor Relay Circuit',
            'C1431': 'Air Suspension Height Sensor Circuit',
            
            # BMW Body/Comfort
            'B1000': 'ECU Internal Fault',
            'B1001': 'ECU Defective',
            'B1318': 'Battery Voltage Low',
            'B1319': 'Battery Voltage High',
            
            # BMW Network/Communication
            'U0100': 'Lost Communication with ECM/PCM',
            'U0101': 'Lost Communication with TCM',
            'U0140': 'Lost Communication with Body Control Module',
            'U0141': 'Lost Communication with Body Control Module "A"',
            'U0155': 'Lost Communication with Instrument Panel Control Module',
        }
    
    def read_dtcs(self) -> Tuple[List[DiagnosticTroubleCode], DTCStatus]:
        """Read all DTCs from vehicle"""
        if not self.adapter.is_connected():
            self.logger.error("Cannot read DTCs - adapter not connected")
            return [], DTCStatus()
        
        dtcs = []
        status = DTCStatus()
        
        try:
            # Read confirmed DTCs
            confirmed_response = self.adapter.query_command(obd.commands.GET_DTC)
            if confirmed_response and not confirmed_response.is_null():
                for dtc_tuple in confirmed_response.value:
                    code = dtc_tuple[0] if len(dtc_tuple) > 0 else "Unknown"
                    description = self._get_dtc_description(code)
                    dtc = DiagnosticTroubleCode(code, description, DTCSeverity.CONFIRMED)
                    dtcs.append(dtc)
                    status.confirmed_dtc_count += 1
            
            # Read pending DTCs
            try:
                pending_response = self.adapter.query_command(obd.commands.GET_PENDING_DTC)
                if pending_response and not pending_response.is_null():
                    for dtc_tuple in pending_response.value:
                        code = dtc_tuple[0] if len(dtc_tuple) > 0 else "Unknown"
                        description = self._get_dtc_description(code)
                        dtc = DiagnosticTroubleCode(code, description, DTCSeverity.PENDING)
                        dtcs.append(dtc)
                        status.pending_dtc_count += 1
            except Exception as e:
                self.logger.debug(f"Could not read pending DTCs: {e}")
            
            # Read permanent DTCs
            try:
                permanent_response = self.adapter.query_command(obd.commands.GET_PERMANENT_DTC)
                if permanent_response and not permanent_response.is_null():
                    for dtc_tuple in permanent_response.value:
                        code = dtc_tuple[0] if len(dtc_tuple) > 0 else "Unknown"
                        description = self._get_dtc_description(code)
                        dtc = DiagnosticTroubleCode(code, description, DTCSeverity.PERMANENT)
                        dtcs.append(dtc)
                        status.permanent_dtc_count += 1
            except Exception as e:
                self.logger.debug(f"Could not read permanent DTCs: {e}")
            
            # Update status
            status.dtc_count = len(dtcs)
            status.mil_on = status.confirmed_dtc_count > 0
            
            # Check MIL status
            try:
                mil_response = self.adapter.query_command(obd.commands.STATUS)
                if mil_response and not mil_response.is_null():
                    # Parse MIL status from response
                    status.mil_on = mil_response.value.MIL if hasattr(mil_response.value, 'MIL') else False
                    status.dtc_count = mil_response.value.DTC_count if hasattr(mil_response.value, 'DTC_count') else len(dtcs)
            except Exception as e:
                self.logger.debug(f"Could not read MIL status: {e}")
            
            self.logger.info(f"Read {len(dtcs)} DTCs (Confirmed: {status.confirmed_dtc_count}, "
                           f"Pending: {status.pending_dtc_count}, Permanent: {status.permanent_dtc_count})")
            
            return dtcs, status
            
        except Exception as e:
            self.logger.error(f"Error reading DTCs: {e}")
            return [], DTCStatus()
    
    def clear_dtcs(self) -> bool:
        """Clear DTCs from vehicle"""
        if not self.adapter.is_connected():
            self.logger.error("Cannot clear DTCs - adapter not connected")
            return False
        
        try:
            self.logger.info("Clearing DTCs...")
            response = self.adapter.query_command(obd.commands.CLEAR_DTC)
            
            if response and not response.is_null():
                self.logger.info("DTCs cleared successfully")
                return True
            else:
                self.logger.error("Failed to clear DTCs - no response or null response")
                return False
                
        except Exception as e:
            self.logger.error(f"Error clearing DTCs: {e}")
            return False
    
    def get_freeze_frame_data(self, dtc_code: str) -> Dict[str, Any]:
        """Get freeze frame data for a specific DTC"""
        if not self.adapter.is_connected():
            return {}
        
        try:
            # Try to get freeze frame data (Mode 02)
            freeze_frame_commands = [
                obd.commands.FREEZE_DTC,
                obd.commands.RPM,
                obd.commands.SPEED,
                obd.commands.COOLANT_TEMP,
                obd.commands.ENGINE_LOAD,
                obd.commands.THROTTLE_POS
            ]
            
            freeze_data = {}
            for command in freeze_frame_commands:
                try:
                    response = self.adapter.query_command(command)
                    if response and not response.is_null():
                        freeze_data[command.name] = {
                            'value': response.value.magnitude if hasattr(response.value, 'magnitude') else response.value,
                            'unit': str(response.value.units) if hasattr(response.value, 'units') else None
                        }
                except Exception as e:
                    self.logger.debug(f"Could not get freeze frame data for {command.name}: {e}")
            
            return freeze_data
            
        except Exception as e:
            self.logger.error(f"Error getting freeze frame data: {e}")
            return {}
    
    def get_dtc_analysis(self, dtcs: List[DiagnosticTroubleCode]) -> Dict[str, Any]:
        """Analyze DTCs and provide BMW-specific insights"""
        analysis = {
            'total_dtcs': len(dtcs),
            'by_severity': {
                'confirmed': len([d for d in dtcs if d.severity == DTCSeverity.CONFIRMED]),
                'pending': len([d for d in dtcs if d.severity == DTCSeverity.PENDING]),
                'permanent': len([d for d in dtcs if d.severity == DTCSeverity.PERMANENT])
            },
            'by_type': {
                'powertrain': len([d for d in dtcs if d.dtc_type == DTCType.POWERTRAIN]),
                'chassis': len([d for d in dtcs if d.dtc_type == DTCType.CHASSIS]),
                'body': len([d for d in dtcs if d.dtc_type == DTCType.BODY]),
                'network': len([d for d in dtcs if d.dtc_type == DTCType.NETWORK])
            },
            'bmw_specific_count': len([d for d in dtcs if d.bmw_specific]),
            'priority_issues': [],
            'recommendations': []
        }
        
        # Identify priority issues
        priority_codes = ['P0300', 'P0301', 'P0302', 'P0303', 'P0304', 'P0305', 'P0306', 'P0307', 'P0308',
                         'P0087', 'P0088', 'P1017', 'U0100', 'U0101']
        
        for dtc in dtcs:
            if dtc.code in priority_codes:
                analysis['priority_issues'].append({
                    'code': dtc.code,
                    'description': dtc.description,
                    'reason': self._get_priority_reason(dtc.code)
                })
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_recommendations(dtcs)
        
        return analysis
    
    def _get_dtc_description(self, code: str) -> str:
        """Get description for DTC code"""
        # First check BMW-specific database
        if code in self.bmw_dtc_database:
            return self.bmw_dtc_database[code]
        
        # Generic descriptions for common patterns
        generic_descriptions = {
            'P0300': 'Random/Multiple Cylinder Misfire',
            'P030': 'Ignition System Misfire',
            'P010': 'Fuel and Air Metering',
            'P020': 'Fuel and Air Metering (Injector Circuit)',
            'P040': 'Auxiliary Emission Controls',
            'P050': 'Vehicle Speed, Idle Control & Auxiliary Inputs',
            'P060': 'Computer & Auxiliary Outputs',
            'P070': 'Transmission',
            'U010': 'Network Communication Codes',
            'C0': 'Chassis System',
            'B0': 'Body System'
        }
        
        for pattern, description in generic_descriptions.items():
            if code.startswith(pattern):
                return description
        
        return "Unknown DTC - Consult BMW service manual"
    
    def _get_priority_reason(self, code: str) -> str:
        """Get reason why a DTC is high priority"""
        priority_reasons = {
            'P0300': 'Multiple cylinder misfire can cause engine damage',
            'P0301': 'Cylinder misfire can damage catalytic converter',
            'P0302': 'Cylinder misfire can damage catalytic converter',
            'P0303': 'Cylinder misfire can damage catalytic converter',
            'P0304': 'Cylinder misfire can damage catalytic converter',
            'P0305': 'Cylinder misfire can damage catalytic converter',
            'P0306': 'Cylinder misfire can damage catalytic converter',
            'P0307': 'Cylinder misfire can damage catalytic converter',
            'P0308': 'Cylinder misfire can damage catalytic converter',
            'P0087': 'Low fuel pressure can cause engine damage',
            'P0088': 'High fuel pressure can damage injectors',
            'P1017': 'Valvetronic emergency mode reduces performance',
            'U0100': 'Communication loss with engine control module',
            'U0101': 'Communication loss with transmission control module'
        }
        
        return priority_reasons.get(code, 'Requires immediate attention')
    
    def _generate_recommendations(self, dtcs: List[DiagnosticTroubleCode]) -> List[str]:
        """Generate recommendations based on DTCs"""
        recommendations = []
        
        # Check for common BMW issues
        codes = [dtc.code for dtc in dtcs]
        
        if any(code.startswith('P030') for code in codes):
            recommendations.append("Check ignition coils and spark plugs - common BMW maintenance item")
        
        if any(code in ['P0087', 'P0088'] for code in codes):
            recommendations.append("Check high-pressure fuel pump and fuel pressure regulator")
        
        if any(code.startswith('P101') for code in codes):
            recommendations.append("Check Valvetronic system - common on BMW engines with variable valve lift")
        
        if any(code.startswith('U01') for code in codes):
            recommendations.append("Check CAN bus connections and module communication")
        
        if any(code.startswith('C12') for code in codes):
            recommendations.append("Check ABS wheel speed sensors - clean or replace as needed")
        
        if len([d for d in dtcs if d.severity == DTCSeverity.PERMANENT]) > 0:
            recommendations.append("Permanent DTCs detected - complete drive cycle required after repairs")
        
        if not recommendations:
            recommendations.append("Consult BMW service documentation for specific diagnostic procedures")
        
        return recommendations