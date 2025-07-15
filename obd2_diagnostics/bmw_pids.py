"""
BMW-specific PID definitions and handlers

This module contains BMW-specific PIDs for F13 generation vehicles
and standard OBD2 PIDs with BMW-specific interpretations.
"""

import obd
from obd import Unit
from typing import Dict, Any, Optional, Callable


class BMWPIDRegistry:
    """Registry for BMW-specific PIDs"""
    
    def __init__(self):
        self._custom_pids = {}
        self._register_bmw_pids()
    
    def _register_bmw_pids(self):
        """Register BMW-specific PIDs for F13 generation"""
        
        # BMW F13 specific PIDs (examples - actual PIDs would need BMW documentation)
        self._custom_pids.update({
            # Engine Management PIDs
            'BMW_ENGINE_TEMP_DETAILED': {
                'pid': 0x22D001,
                'name': 'Engine Temperature Detailed',
                'description': 'Detailed engine temperature readings',
                'unit': Unit.celsius,
                'decoder': self._decode_bmw_engine_temp
            },
            
            'BMW_TURBO_BOOST_PRESSURE': {
                'pid': 0x22D002,
                'name': 'Turbo Boost Pressure',
                'description': 'Turbocharger boost pressure',
                'unit': Unit.kilopascal,
                'decoder': self._decode_bmw_boost_pressure
            },
            
            'BMW_INJECTION_TIMING': {
                'pid': 0x22D003,
                'name': 'Injection Timing',
                'description': 'Fuel injection timing',
                'unit': Unit.degree,
                'decoder': self._decode_bmw_injection_timing
            },
            
            # Transmission PIDs (for automatic transmission)
            'BMW_TRANS_TEMP': {
                'pid': 0x22D010,
                'name': 'Transmission Temperature',
                'description': 'Automatic transmission fluid temperature',
                'unit': Unit.celsius,
                'decoder': self._decode_bmw_trans_temp
            },
            
            'BMW_TRANS_PRESSURE': {
                'pid': 0x22D011,
                'name': 'Transmission Pressure',
                'description': 'Transmission line pressure',
                'unit': Unit.kilopascal,
                'decoder': self._decode_bmw_trans_pressure
            },
            
            # Chassis/Body PIDs
            'BMW_SUSPENSION_LEVEL': {
                'pid': 0x22D020,
                'name': 'Suspension Level',
                'description': 'Air suspension level sensors',
                'unit': Unit.millimeter,
                'decoder': self._decode_bmw_suspension
            },
            
            'BMW_STEERING_ANGLE': {
                'pid': 0x22D021,
                'name': 'Steering Angle',
                'description': 'Steering wheel angle sensor',
                'unit': Unit.degree,
                'decoder': self._decode_bmw_steering_angle
            },
            
            # Comfort/Convenience PIDs
            'BMW_INTERIOR_TEMP': {
                'pid': 0x22D030,
                'name': 'Interior Temperature',
                'description': 'Interior temperature sensors',
                'unit': Unit.celsius,
                'decoder': self._decode_bmw_interior_temp
            },
            
            'BMW_BATTERY_VOLTAGE': {
                'pid': 0x22D031,
                'name': 'Battery Voltage Detailed',
                'description': 'Detailed battery voltage and current',
                'unit': Unit.volt,
                'decoder': self._decode_bmw_battery
            }
        })
    
    def get_pid(self, pid_name: str) -> Optional[Dict[str, Any]]:
        """Get PID definition by name"""
        return self._custom_pids.get(pid_name)
    
    def get_all_pids(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered PIDs"""
        return self._custom_pids.copy()
    
    # BMW-specific decoders
    def _decode_bmw_engine_temp(self, data: bytes) -> float:
        """Decode BMW engine temperature with higher precision"""
        if len(data) >= 2:
            temp = (data[0] * 256 + data[1]) / 10.0 - 40.0
            return temp
        return 0.0
    
    def _decode_bmw_boost_pressure(self, data: bytes) -> float:
        """Decode BMW turbo boost pressure"""
        if len(data) >= 2:
            pressure = (data[0] * 256 + data[1]) / 100.0
            return pressure
        return 0.0
    
    def _decode_bmw_injection_timing(self, data: bytes) -> float:
        """Decode BMW injection timing"""
        if len(data) >= 2:
            timing = ((data[0] * 256 + data[1]) / 128.0) - 210.0
            return timing
        return 0.0
    
    def _decode_bmw_trans_temp(self, data: bytes) -> float:
        """Decode BMW transmission temperature"""
        if len(data) >= 1:
            temp = data[0] - 40.0
            return temp
        return 0.0
    
    def _decode_bmw_trans_pressure(self, data: bytes) -> float:
        """Decode BMW transmission pressure"""
        if len(data) >= 2:
            pressure = (data[0] * 256 + data[1]) / 10.0
            return pressure
        return 0.0
    
    def _decode_bmw_suspension(self, data: bytes) -> float:
        """Decode BMW suspension level"""
        if len(data) >= 2:
            level = (data[0] * 256 + data[1]) / 10.0
            return level
        return 0.0
    
    def _decode_bmw_steering_angle(self, data: bytes) -> float:
        """Decode BMW steering angle"""
        if len(data) >= 2:
            angle = ((data[0] * 256 + data[1]) / 10.0) - 2048.0
            return angle
        return 0.0
    
    def _decode_bmw_interior_temp(self, data: bytes) -> float:
        """Decode BMW interior temperature"""
        if len(data) >= 1:
            temp = (data[0] / 2.0) - 40.0
            return temp
        return 0.0
    
    def _decode_bmw_battery(self, data: bytes) -> float:
        """Decode BMW battery voltage"""
        if len(data) >= 2:
            voltage = (data[0] * 256 + data[1]) / 1000.0
            return voltage
        return 0.0


class StandardPIDMapper:
    """Maps standard OBD2 PIDs to BMW-specific interpretations"""
    
    def __init__(self):
        self.bmw_pid_mapping = {
            # Standard PIDs with BMW-specific handling
            obd.commands.ENGINE_LOAD: self._interpret_bmw_engine_load,
            obd.commands.COOLANT_TEMP: self._interpret_bmw_coolant_temp,
            obd.commands.RPM: self._interpret_bmw_rpm,
            obd.commands.SPEED: self._interpret_bmw_speed,
            obd.commands.INTAKE_TEMP: self._interpret_bmw_intake_temp,
            obd.commands.MAF: self._interpret_bmw_maf,
            obd.commands.THROTTLE_POS: self._interpret_bmw_throttle,
            obd.commands.FUEL_PRESSURE: self._interpret_bmw_fuel_pressure,
            obd.commands.INTAKE_PRESSURE: self._interpret_bmw_intake_pressure,
        }
    
    def interpret_value(self, command, value) -> Dict[str, Any]:
        """Interpret OBD2 value with BMW-specific context"""
        base_result = {
            'value': value.magnitude if hasattr(value, 'magnitude') else value,
            'unit': str(value.units) if hasattr(value, 'units') else None,
            'command': command.name if hasattr(command, 'name') else str(command)
        }
        
        if command in self.bmw_pid_mapping:
            bmw_interpretation = self.bmw_pid_mapping[command](value)
            base_result.update(bmw_interpretation)
        
        return base_result
    
    def _interpret_bmw_engine_load(self, value) -> Dict[str, Any]:
        """BMW-specific engine load interpretation"""
        load_pct = value.magnitude if hasattr(value, 'magnitude') else value
        return {
            'bmw_interpretation': 'Normal' if load_pct < 85 else 'High Load',
            'bmw_notes': 'BMW N55/N63 engines typically run 15-30% load at idle'
        }
    
    def _interpret_bmw_coolant_temp(self, value) -> Dict[str, Any]:
        """BMW-specific coolant temperature interpretation"""
        temp_c = value.magnitude if hasattr(value, 'magnitude') else value
        return {
            'bmw_interpretation': self._get_bmw_temp_status(temp_c),
            'bmw_notes': 'BMW target operating temperature: 87-105°C'
        }
    
    def _interpret_bmw_rpm(self, value) -> Dict[str, Any]:
        """BMW-specific RPM interpretation"""
        rpm = value.magnitude if hasattr(value, 'magnitude') else value
        return {
            'bmw_interpretation': self._get_bmw_rpm_status(rpm),
            'bmw_notes': 'BMW F13 idle speed: 650-750 RPM'
        }
    
    def _interpret_bmw_speed(self, value) -> Dict[str, Any]:
        """BMW-specific speed interpretation"""
        return {
            'bmw_interpretation': 'Standard',
            'bmw_notes': 'Speed signal from ABS module'
        }
    
    def _interpret_bmw_intake_temp(self, value) -> Dict[str, Any]:
        """BMW-specific intake temperature interpretation"""
        temp_c = value.magnitude if hasattr(value, 'magnitude') else value
        return {
            'bmw_interpretation': self._get_bmw_intake_temp_status(temp_c),
            'bmw_notes': 'BMW turbo engines: monitor for excessive intake temps'
        }
    
    def _interpret_bmw_maf(self, value) -> Dict[str, Any]:
        """BMW-specific MAF interpretation"""
        return {
            'bmw_interpretation': 'Standard',
            'bmw_notes': 'BMW uses hot-film MAF sensors'
        }
    
    def _interpret_bmw_throttle(self, value) -> Dict[str, Any]:
        """BMW-specific throttle position interpretation"""
        return {
            'bmw_interpretation': 'Electronic throttle control',
            'bmw_notes': 'BMW Valvetronic system may affect readings'
        }
    
    def _interpret_bmw_fuel_pressure(self, value) -> Dict[str, Any]:
        """BMW-specific fuel pressure interpretation"""
        return {
            'bmw_interpretation': 'High pressure direct injection',
            'bmw_notes': 'BMW DI systems operate at 200+ bar'
        }
    
    def _interpret_bmw_intake_pressure(self, value) -> Dict[str, Any]:
        """BMW-specific intake manifold pressure interpretation"""
        return {
            'bmw_interpretation': 'Turbo/supercharged system',
            'bmw_notes': 'BMW twin-turbo systems in F13 650i'
        }
    
    def _get_bmw_temp_status(self, temp_c: float) -> str:
        """Get BMW-specific temperature status"""
        if temp_c < 60:
            return "Cold/Warming up"
        elif temp_c < 87:
            return "Below operating temperature"
        elif temp_c < 105:
            return "Normal operating temperature"
        elif temp_c < 115:
            return "Running hot"
        else:
            return "Overheating - immediate attention required"
    
    def _get_bmw_rpm_status(self, rpm: float) -> str:
        """Get BMW-specific RPM status"""
        if rpm < 600:
            return "Below idle speed"
        elif rpm < 800:
            return "Normal idle"
        elif rpm < 2000:
            return "Light throttle"
        elif rpm < 4000:
            return "Moderate throttle"
        elif rpm < 6500:
            return "High RPM"
        else:
            return "Redline zone"
    
    def _get_bmw_intake_temp_status(self, temp_c: float) -> str:
        """Get BMW-specific intake temperature status"""
        if temp_c < 10:
            return "Very cold air"
        elif temp_c < 30:
            return "Cool air - good performance"
        elif temp_c < 50:
            return "Normal intake temperature"
        elif temp_c < 70:
            return "Warm air - monitor performance"
        else:
            return "Hot air - reduced performance expected"


# Global instances
bmw_pid_registry = BMWPIDRegistry()
standard_pid_mapper = StandardPIDMapper()