"""
BMW OBD2 Diagnostics - Simple API Demo

Demonstrates the clean API interface maintained while replacing simulated data
with real OBD2 communication.
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from obd2_diagnostics import BMWDiagnostics
from obd2_diagnostics.config import OBD2Config


def demo_clean_api():
    """Demonstrate the clean, simple API interface"""
    
    print("🚗 BMW OBD2 Diagnostics - Clean API Demo")
    print("=" * 50)
    
    # Simple initialization
    print("\n1. Simple Initialization:")
    diagnostics = BMWDiagnostics()
    print(f"   ✅ Created: {diagnostics}")
    
    # BMW model configuration
    print("\n2. BMW Model Configuration:")
    diagnostics.set_bmw_config("F13_650i")
    print("   ✅ BMW F13 650i configuration applied")
    
    # Clean API methods (work in disconnected state too)
    print("\n3. Clean API Methods:")
    
    # Connection status
    connected = diagnostics.is_connected()
    print(f"   📡 Connection Status: {'Connected' if connected else 'Disconnected'}")
    
    # Vehicle info
    vehicle_info = diagnostics.get_vehicle_info()
    print(f"   🚗 Vehicle Info: {len(vehicle_info)} properties")
    
    # Adapter info  
    adapter_info = diagnostics.get_adapter_info()
    print(f"   🔌 Adapter Info: {len(adapter_info)} properties")
    
    # Live data (shows clean error handling when disconnected)
    live_data = diagnostics.get_live_data()
    if live_data:
        print(f"   📊 Live Data: Available")
    else:
        print(f"   📊 Live Data: Not available (not connected)")
    
    # DTC information
    dtc_info = diagnostics.get_dtcs()
    if 'error' in dtc_info:
        print(f"   🔍 DTCs: Not available (not connected)")
    else:
        print(f"   🔍 DTCs: {dtc_info.get('status', {}).get('total_dtcs', 0)} codes")
    
    # Comprehensive summary
    summary = diagnostics.get_diagnostic_summary()
    if 'error' in summary:
        print(f"   📋 Summary: Not available (not connected)")
    else:
        print(f"   📋 Summary: Complete diagnostic data available")
    
    print("\n4. Context Manager Support:")
    with BMWDiagnostics() as diag:
        print(f"   ✅ Context manager: {type(diag).__name__}")
    print("   ✅ Auto-cleanup on exit")
    
    print("\n5. Example Real Usage (with actual adapter):")
    print("""
    # Real usage with OBD2 adapter connected:
    with BMWDiagnostics() as bmw:
        if bmw.connect():
            # Get live engine data
            data = bmw.get_live_data()
            rpm = data['data']['RPM']['value']
            
            # Read diagnostic codes
            dtcs = bmw.get_dtcs()
            if dtcs['status']['total_dtcs'] > 0:
                print("DTCs found!")
            
            # Clear codes after repairs
            bmw.clear_dtcs()
    """)
    
    print("✅ API Demo Complete - Clean interface maintained!")
    print("   The API remains simple while using real OBD2 communication")


if __name__ == "__main__":
    demo_clean_api()