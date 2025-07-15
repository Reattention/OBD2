"""
BMW OBD2 Diagnostics - Basic Usage Example

This example demonstrates how to use the BMW OBD2 diagnostics library
to connect to a real OBD2 adapter and retrieve diagnostic data from a BMW vehicle.
"""

import time
import json
import logging
import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import the BMW diagnostics library
from obd2_diagnostics import BMWDiagnostics
from obd2_diagnostics.config import OBD2Config, AdapterType, ConnectionType, Protocol


def setup_logging():
    """Setup logging for the example"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('bmw_diagnostics.log')
        ]
    )


def create_bmw_config():
    """Create BMW-specific configuration"""
    config = OBD2Config()
    
    # Adapter configuration
    config.adapter_type = AdapterType.AUTO  # Auto-detect adapter type
    config.connection_type = ConnectionType.AUTO  # Auto-detect connection type
    config.protocol = Protocol.AUTO  # Auto-detect protocol
    
    # Connection settings
    config.port = None  # Auto-detect port
    config.baudrate = 38400
    config.timeout = 10.0
    config.fast_mode = True
    
    # BMW-specific settings
    config.bmw_extended_pids = True
    config.generation = "F13"  # BMW F13 generation (6 Series Coupe/Convertible)
    config.model_year = 2012
    config.engine_type = "N63"  # Twin-turbo V8
    
    # Error handling
    config.retry_attempts = 3
    config.reconnect_delay = 2.0
    
    # Logging
    config.log_level = logging.INFO
    config.log_file = 'bmw_diagnostics.log'
    
    return config


def connection_callback(connected, error):
    """Callback function for connection status changes"""
    if connected:
        print("✅ Connected to BMW vehicle!")
    else:
        print(f"❌ Disconnected from BMW vehicle. Error: {error}")


def display_live_data(live_data):
    """Display live vehicle data in a formatted way"""
    if 'error' in live_data:
        print(f"❌ Error getting live data: {live_data['error']}")
        return
    
    print("\n" + "="*60)
    print("📊 LIVE VEHICLE DATA")
    print("="*60)
    
    timestamp = live_data.get('timestamp', 'Unknown')
    print(f"Timestamp: {timestamp}")
    print(f"Vehicle Type: {live_data.get('vehicle_type', 'Unknown')}")
    print(f"Connection Status: {live_data.get('connection_status', 'Unknown')}")
    
    data = live_data.get('data', {})
    
    # Engine data
    print("\n🚗 ENGINE DATA:")
    if 'RPM' in data:
        rpm_info = data['RPM']
        print(f"  RPM: {rpm_info.get('value', 'N/A')} {rpm_info.get('unit', '')}")
        print(f"    BMW Analysis: {rpm_info.get('bmw_interpretation', 'N/A')}")
    
    if 'COOLANT_TEMP' in data:
        temp_info = data['COOLANT_TEMP']
        print(f"  Coolant Temperature: {temp_info.get('value', 'N/A')} {temp_info.get('unit', '')}")
        print(f"    BMW Analysis: {temp_info.get('bmw_interpretation', 'N/A')}")
    
    if 'ENGINE_LOAD' in data:
        load_info = data['ENGINE_LOAD']
        print(f"  Engine Load: {load_info.get('value', 'N/A')} {load_info.get('unit', '')}")
        print(f"    BMW Analysis: {load_info.get('bmw_interpretation', 'N/A')}")
    
    # Performance data
    print("\n🏁 PERFORMANCE DATA:")
    if 'SPEED' in data:
        speed_info = data['SPEED']
        print(f"  Vehicle Speed: {speed_info.get('value', 'N/A')} {speed_info.get('unit', '')}")
    
    if 'THROTTLE_POS' in data:
        throttle_info = data['THROTTLE_POS']
        print(f"  Throttle Position: {throttle_info.get('value', 'N/A')} {throttle_info.get('unit', '')}")
    
    if 'INTAKE_PRESSURE' in data:
        pressure_info = data['INTAKE_PRESSURE']
        print(f"  Intake Pressure: {pressure_info.get('value', 'N/A')} {pressure_info.get('unit', '')}")
    
    # BMW-specific data
    bmw_data = live_data.get('bmw_specific', {})
    if bmw_data:
        print("\n🔧 BMW-SPECIFIC DATA:")
        for key, value in bmw_data.items():
            if key != 'note':
                print(f"  {key.replace('_', ' ').title()}: {value}")
        
        if 'note' in bmw_data:
            print(f"  Note: {bmw_data['note']}")


def display_dtc_info(dtc_info):
    """Display diagnostic trouble code information"""
    if 'error' in dtc_info:
        print(f"❌ Error getting DTCs: {dtc_info['error']}")
        return
    
    print("\n" + "="*60)
    print("🔍 DIAGNOSTIC TROUBLE CODES")
    print("="*60)
    
    status = dtc_info.get('status', {})
    print(f"MIL Status: {'🚨 ON' if status.get('mil_on', False) else '✅ OFF'}")
    print(f"Total DTCs: {status.get('total_dtcs', 0)}")
    print(f"Confirmed: {status.get('confirmed', 0)}")
    print(f"Pending: {status.get('pending', 0)}")
    print(f"Permanent: {status.get('permanent', 0)}")
    
    dtcs = dtc_info.get('dtcs', [])
    if dtcs:
        print("\nDETECTED DTCs:")
        for dtc in dtcs:
            severity_icon = {
                'confirmed': '🔴',
                'pending': '🟡',
                'permanent': '🟠'
            }.get(dtc.get('severity', 'confirmed'), '🔴')
            
            print(f"  {severity_icon} {dtc.get('code', 'Unknown')}: {dtc.get('description', 'No description')}")
            print(f"    Type: {dtc.get('dtc_type', 'Unknown')}")
            print(f"    BMW Specific: {'Yes' if dtc.get('bmw_specific', False) else 'No'}")
            print(f"    Timestamp: {dtc.get('timestamp', 'Unknown')}")
    else:
        print("\n✅ No DTCs detected")
    
    # Display analysis
    analysis = dtc_info.get('analysis', {})
    if analysis:
        print(f"\n📋 ANALYSIS:")
        print(f"  BMW-specific codes: {analysis.get('bmw_specific_count', 0)}")
        
        priority_issues = analysis.get('priority_issues', [])
        if priority_issues:
            print(f"\n⚠️  PRIORITY ISSUES:")
            for issue in priority_issues:
                print(f"    {issue.get('code', 'Unknown')}: {issue.get('reason', 'No reason')}")
        
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"    {i}. {rec}")


def display_readiness_test(readiness):
    """Display readiness test results"""
    if 'error' in readiness:
        print(f"❌ Error performing readiness test: {readiness['error']}")
        return
    
    print("\n" + "="*60)
    print("🔬 OBD2 READINESS TEST")
    print("="*60)
    
    print(f"MIL Status: {'🚨 ON' if readiness.get('mil_status', False) else '✅ OFF'}")
    print(f"DTC Count: {readiness.get('dtc_count', 0)}")
    
    monitors = readiness.get('monitors', {})
    if monitors:
        print("\nMONITOR STATUS:")
        for monitor_name, monitor_data in monitors.items():
            available = monitor_data.get('available', False)
            complete = monitor_data.get('complete', False)
            
            status_icon = '✅' if complete else ('🔄' if available else '❌')
            status_text = 'Complete' if complete else ('Ready' if available else 'Not Available')
            
            print(f"  {status_icon} {monitor_name.replace('_', ' ').title()}: {status_text}")


def main():
    """Main demonstration function"""
    setup_logging()
    
    print("🚗 BMW OBD2 Diagnostics Tool")
    print("=" * 50)
    
    # Create BMW-specific configuration
    config = create_bmw_config()
    
    # Create diagnostics instance
    print("Initializing BMW diagnostics...")
    with BMWDiagnostics(config) as diagnostics:
        
        # Set BMW model configuration
        diagnostics.set_bmw_config("F13_650i")
        
        # Add connection callback
        diagnostics.add_connection_callback(connection_callback)
        
        # Attempt connection
        print("Attempting to connect to BMW vehicle...")
        print("(Make sure your OBD2 adapter is connected and vehicle is running)")
        
        if diagnostics.connect(auto_detect=True):
            print("🎉 Successfully connected to BMW vehicle!")
            
            # Display vehicle information
            vehicle_info = diagnostics.get_vehicle_info()
            if vehicle_info:
                print(f"\n📋 Vehicle Information:")
                print(f"  Generation: {vehicle_info.get('bmw_generation', 'Unknown')}")
                print(f"  Supported Commands: {vehicle_info.get('supported_commands', 0)}")
                print(f"  BMW Support: {'Yes' if vehicle_info.get('bmw_specific_support', False) else 'No'}")
            
            # Get adapter information
            adapter_info = diagnostics.get_adapter_info()
            if adapter_info:
                print(f"\n🔌 Adapter Information:")
                print(f"  Status: {adapter_info.get('status', 'Unknown')}")
                print(f"  Protocol: {adapter_info.get('protocol', 'Unknown')}")
                print(f"  Port: {adapter_info.get('port', 'Unknown')}")
            
            # Live data monitoring loop
            print("\n🔄 Starting live data monitoring...")
            print("Press Ctrl+C to stop monitoring")
            
            try:
                for i in range(10):  # Monitor for 10 iterations
                    print(f"\n--- Update {i+1}/10 ---")
                    
                    # Get live data
                    live_data = diagnostics.get_live_data(refresh=True)
                    display_live_data(live_data)
                    
                    # Get DTCs every few iterations
                    if i % 3 == 0:
                        dtc_info = diagnostics.get_dtcs()
                        display_dtc_info(dtc_info)
                    
                    # Get readiness test on first iteration
                    if i == 0:
                        readiness = diagnostics.perform_readiness_test()
                        display_readiness_test(readiness)
                    
                    # Wait between updates
                    time.sleep(2)
                    
            except KeyboardInterrupt:
                print("\n⏹️  Monitoring stopped by user")
            
            # Get comprehensive diagnostic summary
            print("\n📊 Getting comprehensive diagnostic summary...")
            summary = diagnostics.get_diagnostic_summary()
            
            # Save summary to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bmw_diagnostic_summary_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            print(f"📄 Diagnostic summary saved to: {filename}")
            
        else:
            print("❌ Failed to connect to BMW vehicle")
            print("\nTroubleshooting:")
            print("1. Ensure OBD2 adapter is properly connected")
            print("2. Make sure vehicle ignition is ON")
            print("3. Check adapter compatibility with your BMW model")
            print("4. Verify adapter drivers are installed")
            print("5. Try different USB ports or Bluetooth pairing")
    
    print("\n👋 BMW OBD2 Diagnostics session ended")


if __name__ == "__main__":
    main()