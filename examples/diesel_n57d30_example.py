"""
BMW F13 535d N57D30 Diesel Engine Diagnostics Example

This example demonstrates the new diesel engine support for the BMW N57D30 engine
used in the F13 535d model. It shows how to use diesel-specific features.
"""

import time
import json
import logging
from datetime import datetime
import sys
import os

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from obd2_diagnostics import BMWDiagnostics
from obd2_diagnostics.config import OBD2Config


def setup_logging():
    """Setup logging for the diesel example"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def create_diesel_config():
    """Create N57D30 diesel-specific configuration"""
    config = OBD2Config()
    
    # Adapter configuration
    config.adapter_type = "AUTO"
    config.connection_type = "AUTO"
    config.protocol = "AUTO"
    
    # Connection settings
    config.port = None  # Auto-detect port
    config.baudrate = 38400
    config.timeout = 10.0
    config.fast_mode = True
    
    # N57D30 Diesel-specific settings
    config.bmw_extended_pids = True
    config.generation = "F13"
    config.model_year = 2012
    config.engine_type = "N57D30"
    config.fuel_type = "diesel"
    config.emissions_standard = "Euro5"
    config.displacement_liters = 3.0
    config.cylinders = 6
    config.turbo_type = "VNT"
    
    # Diesel system configuration
    config.diesel_specific = {
        "dpf_equipped": True,
        "scr_equipped": True,
        "def_required": True,
        "egr_equipped": True,
        "common_rail_pressure_max": 2000,  # bar
        "regeneration_interval_miles": 400
    }
    
    # Error handling
    config.retry_attempts = 3
    config.reconnect_delay = 2.0
    
    return config


def diesel_connection_callback(connected, error):
    """Callback function for diesel engine connection status"""
    if connected:
        print("🚗 Connected to BMW F13 535d (N57D30 Diesel Engine)!")
    else:
        print(f"❌ Disconnected from diesel vehicle. Error: {error}")


def display_diesel_live_data(live_data):
    """Display live diesel engine data with diesel-specific information"""
    if 'error' in live_data:
        print(f"❌ Error getting live data: {live_data['error']}")
        return
    
    print("\n" + "="*70)
    print("🛢️  BMW N57D30 DIESEL ENGINE - LIVE DATA")
    print("="*70)
    
    timestamp = live_data.get('timestamp', 'Unknown')
    print(f"Timestamp: {timestamp}")
    print(f"Vehicle: BMW F13 535d")
    print(f"Engine: N57D30 3.0L I6 Diesel (313 HP)")
    print(f"Connection: {live_data.get('connection_status', 'Unknown')}")
    
    data = live_data.get('data', {})
    
    # Engine performance data
    print("\n🚗 ENGINE PERFORMANCE:")
    if 'RPM' in data:
        rpm_info = data['RPM']
        print(f"  RPM: {rpm_info.get('value', 'N/A')} {rpm_info.get('unit', '')}")
        print(f"    BMW Analysis: {rpm_info.get('bmw_interpretation', 'N/A')}")
        if 'diesel_notes' in rpm_info:
            print(f"    Diesel Note: {rpm_info['diesel_notes']}")
    
    if 'ENGINE_LOAD' in data:
        load_info = data['ENGINE_LOAD']
        print(f"  Engine Load: {load_info.get('value', 'N/A')} {load_info.get('unit', '')}")
        print(f"    BMW Analysis: {load_info.get('bmw_interpretation', 'N/A')}")
        if 'diesel_notes' in load_info:
            print(f"    Diesel Note: {load_info['diesel_notes']}")
    
    if 'SPEED' in data:
        speed_info = data['SPEED']
        print(f"  Vehicle Speed: {speed_info.get('value', 'N/A')} {speed_info.get('unit', '')}")
    
    # Diesel fuel system
    print("\n⛽ DIESEL FUEL SYSTEM:")
    if 'FUEL_PRESSURE' in data:
        pressure_info = data['FUEL_PRESSURE']
        print(f"  Fuel Pressure: {pressure_info.get('value', 'N/A')} {pressure_info.get('unit', '')}")
        print(f"    BMW Analysis: {pressure_info.get('bmw_interpretation', 'N/A')}")
        if 'diesel_notes' in pressure_info:
            print(f"    Diesel Note: {pressure_info['diesel_notes']}")
    
    # Turbocharger system
    print("\n🌪️  TURBOCHARGER (VNT):")
    if 'INTAKE_PRESSURE' in data:
        boost_info = data['INTAKE_PRESSURE']
        print(f"  Intake Pressure: {boost_info.get('value', 'N/A')} {boost_info.get('unit', '')}")
        print(f"    BMW Analysis: {boost_info.get('bmw_interpretation', 'N/A')}")
        if 'diesel_notes' in boost_info:
            print(f"    Diesel Note: {boost_info['diesel_notes']}")
    
    # Engine temperatures
    print("\n🌡️  ENGINE TEMPERATURES:")
    if 'COOLANT_TEMP' in data:
        temp_info = data['COOLANT_TEMP']
        print(f"  Coolant Temperature: {temp_info.get('value', 'N/A')} {temp_info.get('unit', '')}")
        print(f"    BMW Analysis: {temp_info.get('bmw_interpretation', 'N/A')}")
    
    if 'INTAKE_TEMP' in data:
        intake_temp = data['INTAKE_TEMP']
        print(f"  Intake Air Temperature: {intake_temp.get('value', 'N/A')} {intake_temp.get('unit', '')}")
        print(f"    BMW Analysis: {intake_temp.get('bmw_interpretation', 'N/A')}")
    
    # BMW diesel-specific data (simulated)
    bmw_data = live_data.get('bmw_specific', {})
    if bmw_data:
        print("\n🔧 BMW N57D30 DIESEL-SPECIFIC DATA:")
        for key, value in bmw_data.items():
            if key != 'note':
                display_name = key.replace('_', ' ').title()
                if 'pressure' in key.lower():
                    unit = ' bar'
                elif 'temp' in key.lower():
                    unit = ' °C'
                elif 'timing' in key.lower():
                    unit = ' deg'
                else:
                    unit = ''
                print(f"  {display_name}: {value}{unit}")
        
        if 'note' in bmw_data:
            print(f"\n  📝 Note: {bmw_data['note']}")


def display_diesel_dtcs(dtc_info):
    """Display diesel-specific DTC information"""
    if 'error' in dtc_info:
        print(f"❌ Error getting DTCs: {dtc_info['error']}")
        return
    
    print("\n" + "="*70)
    print("🔍 N57D30 DIESEL ENGINE - DIAGNOSTIC TROUBLE CODES")
    print("="*70)
    
    status = dtc_info.get('status', {})
    print(f"MIL Status: {'🚨 ON' if status.get('mil_on', False) else '✅ OFF'}")
    print(f"Total DTCs: {status.get('total_dtcs', 0)}")
    print(f"Confirmed: {status.get('confirmed', 0)}")
    print(f"Pending: {status.get('pending', 0)}")
    print(f"Permanent: {status.get('permanent', 0)}")
    
    dtcs = dtc_info.get('dtcs', [])
    if dtcs:
        print("\nDETECTED DTCs:")
        
        # Categorize DTCs by diesel system
        dpf_codes = []
        egr_codes = []
        nox_scr_codes = []
        def_codes = []
        turbo_codes = []
        glow_plug_codes = []
        other_codes = []
        
        for dtc in dtcs:
            code = dtc.get('code', '')
            if code.startswith('P2') and ('Particulate' in dtc.get('description', '') or 'DPF' in dtc.get('description', '')):
                dpf_codes.append(dtc)
            elif 'EGR' in dtc.get('description', '') or code.startswith('P040'):
                egr_codes.append(dtc)
            elif 'NOx' in dtc.get('description', '') or 'SCR' in dtc.get('description', '') or code == 'P20EE':
                nox_scr_codes.append(dtc)
            elif 'DEF' in dtc.get('description', '') or 'Reductant' in dtc.get('description', '') or code.startswith('P229') or code.startswith('P204') or code.startswith('P205'):
                def_codes.append(dtc)
            elif 'Turbo' in dtc.get('description', '') or code in ['P0299', 'P0234'] or code.startswith('P256'):
                turbo_codes.append(dtc)
            elif 'Glow' in dtc.get('description', '') or code.startswith('P067') or code.startswith('P038'):
                glow_plug_codes.append(dtc)
            else:
                other_codes.append(dtc)
        
        def display_dtc_category(category_name, dtcs_list, emoji):
            if dtcs_list:
                print(f"\n{emoji} {category_name} ISSUES:")
                for dtc in dtcs_list:
                    severity_icon = {
                        'confirmed': '🔴',
                        'pending': '🟡',
                        'permanent': '🟠'
                    }.get(dtc.get('severity', 'confirmed'), '🔴')
                    
                    print(f"    {severity_icon} {dtc.get('code', 'Unknown')}: {dtc.get('description', 'No description')}")
        
        display_dtc_category("DPF (DIESEL PARTICULATE FILTER)", dpf_codes, "🫧")
        display_dtc_category("EGR (EXHAUST GAS RECIRCULATION)", egr_codes, "♻️")
        display_dtc_category("NOx/SCR (EMISSION CONTROL)", nox_scr_codes, "🌱")
        display_dtc_category("DEF/AdBlue SYSTEM", def_codes, "💧")
        display_dtc_category("TURBOCHARGER (VNT)", turbo_codes, "🌪️")
        display_dtc_category("GLOW PLUG SYSTEM", glow_plug_codes, "🔥")
        display_dtc_category("OTHER ENGINE CODES", other_codes, "⚙️")
        
    else:
        print("\n✅ No DTCs detected - Diesel systems operating normally")
    
    # Display diesel-specific analysis
    analysis = dtc_info.get('analysis', {})
    if analysis:
        print(f"\n📋 DIESEL ENGINE ANALYSIS:")
        print(f"  BMW-specific codes: {analysis.get('bmw_specific_count', 0)}")
        
        priority_issues = analysis.get('priority_issues', [])
        diesel_priority = [issue for issue in priority_issues 
                          if issue.get('code', '') in ['P2002', 'P2463', 'P0401', 'P0402', 'P20EE', 'P229F', 'P204F', 'P0299', 'P0380']]
        
        if diesel_priority:
            print(f"\n⚠️  DIESEL PRIORITY ISSUES:")
            for issue in diesel_priority:
                print(f"    🚨 {issue.get('code', 'Unknown')}: {issue.get('reason', 'No reason')}")
        
        recommendations = analysis.get('recommendations', [])
        diesel_recs = [rec for rec in recommendations 
                      if any(keyword in rec.lower() for keyword in ['dpf', 'def', 'adblue', 'egr', 'turbo', 'nox', 'glow', 'diesel'])]
        
        if diesel_recs:
            print(f"\n💡 DIESEL-SPECIFIC RECOMMENDATIONS:")
            for i, rec in enumerate(diesel_recs, 1):
                print(f"    {i}. {rec}")


def demonstrate_diesel_monitoring():
    """Demonstrate continuous diesel engine monitoring"""
    setup_logging()
    
    print("🚗 BMW N57D30 Diesel Engine Diagnostics Demo")
    print("=" * 50)
    print("Vehicle: BMW F13 535d")
    print("Engine: N57D30 3.0L I6 Diesel Turbo")
    print("Power: 313 HP / 630 Nm torque")
    print("Features: DPF, SCR, DEF/AdBlue, VNT Turbo")
    
    # Create diesel-specific configuration
    config = create_diesel_config()
    
    # Create diagnostics instance
    print("\nInitializing N57D30 diesel diagnostics...")
    with BMWDiagnostics(config) as diagnostics:
        
        # Set BMW diesel configuration
        diagnostics.set_bmw_config("F13_535d")
        
        # Add connection callback
        diagnostics.add_connection_callback(diesel_connection_callback)
        
        # Display configuration info
        print(f"\nDiesel Configuration:")
        print(f"  Engine Type: {config.engine_type}")
        print(f"  Fuel Type: {config.fuel_type}")
        print(f"  Emissions: {config.emissions_standard}")
        print(f"  Displacement: {config.displacement_liters}L")
        print(f"  Cylinders: {config.cylinders}")
        print(f"  Turbo Type: {config.turbo_type}")
        print(f"  DPF Equipped: {config.diesel_specific.get('dpf_equipped', False)}")
        print(f"  SCR Equipped: {config.diesel_specific.get('scr_equipped', False)}")
        print(f"  DEF Required: {config.diesel_specific.get('def_required', False)}")
        
        # Attempt connection
        print("\nAttempting to connect to BMW F13 535d...")
        print("(Make sure your OBD2 adapter is connected and vehicle is running)")
        
        if diagnostics.connect(auto_detect=True):
            print("\n🎉 Successfully connected to BMW N57D30 diesel engine!")
            
            # Display vehicle information
            vehicle_info = diagnostics.get_vehicle_info()
            if vehicle_info:
                print(f"\n📋 Diesel Vehicle Information:")
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
            
            # Diesel engine monitoring loop
            print("\n🔄 Starting N57D30 diesel monitoring...")
            print("Press Ctrl+C to stop monitoring")
            
            try:
                for i in range(10):  # Monitor for 10 iterations
                    print(f"\n--- Diesel Monitoring Update {i+1}/10 ---")
                    
                    # Get live diesel data
                    live_data = diagnostics.get_live_data(refresh=True)
                    display_diesel_live_data(live_data)
                    
                    # Check diesel DTCs every few iterations
                    if i % 3 == 0:
                        dtc_info = diagnostics.get_dtcs()
                        display_diesel_dtcs(dtc_info)
                    
                    # Diesel-specific checks
                    if i == 1:
                        print("\n🔍 Performing diesel readiness test...")
                        readiness = diagnostics.perform_readiness_test()
                        if 'error' not in readiness:
                            monitors = readiness.get('monitors', {})
                            diesel_monitors = ['DPF', 'EGR', 'NOx', 'SCR']
                            print("Diesel System Monitors:")
                            for name, status in monitors.items():
                                if any(dm.lower() in name.lower() for dm in diesel_monitors):
                                    available = status.get('available', False)
                                    complete = status.get('complete', False)
                                    status_text = 'Complete' if complete else ('Ready' if available else 'Not Available')
                                    print(f"  {name}: {status_text}")
                    
                    # Wait between updates
                    time.sleep(3)
                    
            except KeyboardInterrupt:
                print("\n⏹️  Diesel monitoring stopped by user")
            
            # Get comprehensive diesel diagnostic summary
            print("\n📊 Getting comprehensive N57D30 diagnostic summary...")
            summary = diagnostics.get_diagnostic_summary()
            
            # Save diesel-specific summary
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bmw_n57d30_diesel_summary_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            print(f"📄 N57D30 Diesel diagnostic summary saved to: {filename}")
            
        else:
            print("❌ Failed to connect to BMW F13 535d")
            print("\nDiesel Engine Troubleshooting:")
            print("1. Ensure OBD2 adapter is properly connected")
            print("2. Make sure vehicle ignition is ON")
            print("3. Check adapter compatibility with BMW CAN bus")
            print("4. Verify adapter drivers are installed")
            print("5. Try different USB ports or Bluetooth pairing")
            print("6. Diesel engines may take longer to initialize")
    
    print("\n👋 BMW N57D30 Diesel diagnostics session ended")
    print("\nDiesel System Notes:")
    print("• DPF regeneration typically occurs every 300-600 miles")
    print("• DEF consumption is approximately 3-5% of fuel consumption")
    print("• VNT turbo provides variable boost across RPM range")
    print("• Regular highway driving helps maintain diesel systems")


if __name__ == "__main__":
    demonstrate_diesel_monitoring()