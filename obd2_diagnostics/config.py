"""
Configuration module for BMW OBD2 Diagnostics

Handles configuration for different OBD2 adapters and connection methods.
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum


class AdapterType(Enum):
    """Supported OBD2 adapter types"""
    ELM327 = "elm327"
    OBDLINK = "obdlink"
    SCANTOOL = "scantool"
    AUTO = "auto"


class ConnectionType(Enum):
    """Supported connection types"""
    USB = "usb"
    BLUETOOTH = "bluetooth"
    WIFI = "wifi"
    AUTO = "auto"


class Protocol(Enum):
    """Supported OBD2 protocols"""
    ISO_15765_4 = "ISO 15765-4 (CAN)"
    ISO_14230_4 = "ISO 14230-4 (KWP2000)"
    ISO_9141_2 = "ISO 9141-2"
    SAE_J1850_PWM = "SAE J1850 PWM"
    SAE_J1850_VPW = "SAE J1850 VPW"
    AUTO = "AUTO"


class OBD2Config:
    """Configuration class for OBD2 diagnostics"""
    
    def __init__(self):
        self.adapter_type = AdapterType.AUTO
        self.connection_type = ConnectionType.AUTO
        self.protocol = Protocol.AUTO
        self.port = None
        self.baudrate = 38400
        self.timeout = 10.0
        self.fast_mode = True
        self.bmw_extended_pids = True
        self.retry_attempts = 3
        self.reconnect_delay = 2.0
        
        # BMW-specific settings
        self.generation = "F13"  # BMW F13 generation
        self.model_year = None
        self.engine_type = None
        self.fuel_type = "gasoline"  # gasoline or diesel
        self.emissions_standard = None
        self.displacement_liters = None
        self.cylinders = None
        self.turbo_type = None  # twin-turbo, single-turbo, VNT
        self.diesel_specific = {}  # Diesel-specific configuration
        
        # Logging configuration
        self.log_level = logging.INFO
        self.log_file = None
        
    def from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Load configuration from dictionary"""
        for key, value in config_dict.items():
            if hasattr(self, key):
                if key == 'adapter_type':
                    self.adapter_type = AdapterType(value)
                elif key == 'connection_type':
                    self.connection_type = ConnectionType(value)
                elif key == 'protocol':
                    self.protocol = Protocol(value)
                elif key == 'log_level':
                    self.log_level = getattr(logging, value.upper())
                else:
                    setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration to dictionary"""
        return {
            'adapter_type': self.adapter_type.value,
            'connection_type': self.connection_type.value,
            'protocol': self.protocol.value,
            'port': self.port,
            'baudrate': self.baudrate,
            'timeout': self.timeout,
            'fast_mode': self.fast_mode,
            'bmw_extended_pids': self.bmw_extended_pids,
            'retry_attempts': self.retry_attempts,
            'reconnect_delay': self.reconnect_delay,
            'generation': self.generation,
            'model_year': self.model_year,
            'engine_type': self.engine_type,
            'fuel_type': self.fuel_type,
            'emissions_standard': self.emissions_standard,
            'displacement_liters': self.displacement_liters,
            'cylinders': self.cylinders,
            'turbo_type': self.turbo_type,
            'diesel_specific': self.diesel_specific,
            'log_level': logging.getLevelName(self.log_level),
            'log_file': self.log_file
        }


# Default configurations for common BMW models
BMW_CONFIGS = {
    "F13_650i": {
        "generation": "F13",
        "model_year": 2012,
        "engine_type": "N63",
        "protocol": Protocol.ISO_15765_4.value,
        "baudrate": 500000
    },
    "F13_640i": {
        "generation": "F13",
        "model_year": 2012,
        "engine_type": "N55",
        "protocol": Protocol.ISO_15765_4.value,
        "baudrate": 500000
    },
    "F13_535d": {
        "generation": "F13",
        "model_year": 2012,
        "engine_type": "N57D30",
        "protocol": Protocol.ISO_15765_4.value,
        "baudrate": 500000,
        "fuel_type": "diesel",
        "emissions_standard": "Euro5",
        "displacement_liters": 3.0,
        "cylinders": 6,
        "turbo_type": "VNT",
        "diesel_specific": {
            "dpf_equipped": True,
            "scr_equipped": True,
            "def_required": True,
            "egr_equipped": True,
            "common_rail_pressure_max": 2000,  # bar
            "regeneration_interval_miles": 400
        }
    }
}