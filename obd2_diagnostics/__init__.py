"""
BMW OBD2 Diagnostics Package

A comprehensive OBD2 diagnostics tool specifically designed for BMW vehicles,
featuring real ECU communication and BMW-specific PID support.
"""

__version__ = "0.1.0"
__author__ = "BMW OBD2 Team"

from .bmw_diagnostics import BMWDiagnostics
from .obd2_adapter import OBD2Adapter
from .dtc_handler import DTCHandler

__all__ = ['BMWDiagnostics', 'OBD2Adapter', 'DTCHandler']