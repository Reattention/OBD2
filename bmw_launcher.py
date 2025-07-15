#!/usr/bin/env python3
"""
BMW OBD2 Diagnostics Launcher

This script provides a unified interface to launch different diagnostic functions
and serves as a consolidation point for the various modules.
"""

import sys
import os
import argparse
import logging
from typing import Optional

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from obd2_diagnostics import BMWDiagnostics
    from obd2_diagnostics.config import OBD2Config, BMW_CONFIGS
    from obd2_diagnostics.obd2_adapter import AdapterDiscovery
except ImportError as e:
    print(f"Error importing BMW diagnostics modules: {e}")
    print("Please ensure dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def list_bmw_configs() -> None:
    """List available BMW configurations"""
    print("Available BMW Configurations:")
    print("=" * 40)
    
    for config_name, config_data in BMW_CONFIGS.items():
        print(f"\n{config_name}:")
        print(f"  Generation: {config_data.get('generation', 'Unknown')}")
        print(f"  Engine: {config_data.get('engine_type', 'Unknown')}")
        print(f"  Fuel Type: {config_data.get('fuel_type', 'gasoline')}")
        print(f"  Model Year: {config_data.get('model_year', 'Unknown')}")
        
        if 'diesel_specific' in config_data:
            diesel_info = config_data['diesel_specific']
            print(f"  Diesel Features:")
            print(f"    - DPF: {'Yes' if diesel_info.get('dpf_equipped', False) else 'No'}")
            print(f"    - SCR: {'Yes' if diesel_info.get('scr_equipped', False) else 'No'}")
            print(f"    - DEF: {'Yes' if diesel_info.get('def_required', False) else 'No'}")


def scan_adapters() -> None:
    """Scan for available OBD2 adapters"""
    print("Scanning for OBD2 Adapters...")
    print("=" * 30)
    
    # Scan serial ports
    print("\nSerial Ports:")
    ports = AdapterDiscovery.scan_ports()
    if ports:
        for port in ports:
            print(f"  📍 {port}")
    else:
        print("  No serial ports found")
    
    # Scan Bluetooth devices
    print("\nBluetooth OBD2 Devices:")
    bluetooth_devices = AdapterDiscovery.scan_bluetooth()
    if bluetooth_devices:
        for device in bluetooth_devices:
            print(f"  📶 {device.get('name', 'Unknown')} ({device.get('address', 'Unknown')})")
    else:
        print("  No Bluetooth OBD2 devices found")
    
    # Try auto-detection
    print("\nAuto-Detection Test:")
    config = OBD2Config()
    config.timeout = 5.0  # Short timeout for scanning
    
    detected_port = AdapterDiscovery.auto_detect_adapter(config)
    if detected_port:
        print(f"  ✅ Auto-detected adapter on: {detected_port}")
    else:
        print("  ❌ No adapter auto-detected")


def test_connection(bmw_config: Optional[str] = None, port: Optional[str] = None) -> None:
    """Test connection to BMW vehicle"""
    print("Testing BMW OBD2 Connection...")
    print("=" * 30)
    
    # Create configuration
    config = OBD2Config()
    config.timeout = 10.0
    config.retry_attempts = 2
    
    if port:
        config.port = port
        print(f"Using specified port: {port}")
    
    if bmw_config:
        if bmw_config in BMW_CONFIGS:
            print(f"Using BMW configuration: {bmw_config}")
        else:
            print(f"Unknown BMW configuration: {bmw_config}")
            print("Available configurations:")
            for name in BMW_CONFIGS.keys():
                print(f"  - {name}")
            return
    
    # Test connection
    with BMWDiagnostics(config) as diagnostics:
        if bmw_config:
            diagnostics.set_bmw_config(bmw_config)
        
        print("\nAttempting connection...")
        if diagnostics.connect(auto_detect=True):
            print("✅ Successfully connected to BMW vehicle!")
            
            # Get basic info
            vehicle_info = diagnostics.get_vehicle_info()
            adapter_info = diagnostics.get_adapter_info()
            
            print(f"\nVehicle Information:")
            print(f"  Generation: {vehicle_info.get('bmw_generation', 'Unknown')}")
            print(f"  Supported Commands: {vehicle_info.get('supported_commands', 0)}")
            
            print(f"\nAdapter Information:")
            print(f"  Protocol: {adapter_info.get('protocol', 'Unknown')}")
            print(f"  Port: {adapter_info.get('port', 'Unknown')}")
            
            # Quick data test
            print(f"\nQuick Data Test:")
            live_data = diagnostics.get_live_data()
            if 'error' not in live_data:
                data = live_data.get('data', {})
                if 'RPM' in data:
                    rpm = data['RPM'].get('value', 'N/A')
                    print(f"  Engine RPM: {rpm}")
                if 'COOLANT_TEMP' in data:
                    temp = data['COOLANT_TEMP'].get('value', 'N/A')
                    print(f"  Coolant Temp: {temp}°C")
                print("  ✅ Data retrieval successful")
            else:
                print(f"  ❌ Data retrieval failed: {live_data['error']}")
            
        else:
            print("❌ Failed to connect to BMW vehicle")
            print("\nTroubleshooting tips:")
            print("1. Ensure vehicle ignition is ON")
            print("2. Check OBD2 adapter connection")
            print("3. Try scanning for adapters first")
            print("4. Verify adapter compatibility")


def run_diagnostics(bmw_config: Optional[str] = None, port: Optional[str] = None, diesel: bool = False) -> None:
    """Run full diagnostics session"""
    print("BMW OBD2 Full Diagnostics")
    print("=" * 25)
    
    # Create configuration
    config = OBD2Config()
    if port:
        config.port = port
    
    # Set diesel if specified
    if diesel:
        if not bmw_config:
            bmw_config = "F13_535d"
        config.fuel_type = "diesel"
        print("Diesel engine mode enabled")
    
    with BMWDiagnostics(config) as diagnostics:
        if bmw_config:
            diagnostics.set_bmw_config(bmw_config)
            config_info = BMW_CONFIGS.get(bmw_config, {})
            print(f"BMW Configuration: {bmw_config}")
            print(f"Engine: {config_info.get('engine_type', 'Unknown')}")
            print(f"Fuel Type: {config_info.get('fuel_type', 'gasoline')}")
        
        print("\nConnecting to vehicle...")
        if diagnostics.connect(auto_detect=True):
            print("✅ Connected successfully!")
            
            # Get live data
            print("\n📊 Getting live data...")
            live_data = diagnostics.get_live_data()
            if 'error' not in live_data:
                data = live_data.get('data', {})
                print("Engine Data:")
                for param in ['RPM', 'SPEED', 'COOLANT_TEMP', 'ENGINE_LOAD']:
                    if param in data:
                        info = data[param]
                        value = info.get('value', 'N/A')
                        unit = info.get('unit', '')
                        print(f"  {param}: {value} {unit}")
                        
                        # Show diesel-specific notes if available
                        if diesel and 'diesel_notes' in info:
                            print(f"    Diesel: {info['diesel_notes']}")
            
            # Get DTCs
            print("\n🔍 Checking diagnostic trouble codes...")
            dtc_info = diagnostics.get_dtcs()
            if 'error' not in dtc_info:
                status = dtc_info.get('status', {})
                dtcs = dtc_info.get('dtcs', [])
                
                print(f"MIL Status: {'ON' if status.get('mil_on', False) else 'OFF'}")
                print(f"Total DTCs: {len(dtcs)}")
                
                if dtcs:
                    print("Detected codes:")
                    for dtc in dtcs[:5]:  # Show first 5
                        code = dtc.get('code', 'Unknown')
                        desc = dtc.get('description', 'No description')
                        print(f"  {code}: {desc}")
                    
                    if len(dtcs) > 5:
                        print(f"  ... and {len(dtcs) - 5} more codes")
                    
                    # Show diesel-specific analysis
                    if diesel:
                        analysis = dtc_info.get('analysis', {})
                        recommendations = analysis.get('recommendations', [])
                        diesel_recs = [r for r in recommendations if any(
                            keyword in r.lower() for keyword in ['dpf', 'def', 'egr', 'turbo', 'nox']
                        )]
                        if diesel_recs:
                            print("\nDiesel-specific recommendations:")
                            for rec in diesel_recs[:3]:
                                print(f"  • {rec}")
                else:
                    print("✅ No diagnostic trouble codes found")
            
            # Readiness test
            print("\n🔬 Performing readiness test...")
            readiness = diagnostics.perform_readiness_test()
            if 'error' not in readiness:
                monitors = readiness.get('monitors', {})
                ready_count = sum(1 for m in monitors.values() if m.get('complete', False))
                total_count = len(monitors)
                print(f"Ready monitors: {ready_count}/{total_count}")
                
                # Show diesel-specific monitors
                if diesel:
                    diesel_monitors = {k: v for k, v in monitors.items() 
                                     if any(dm in k.lower() for dm in ['dpf', 'egr', 'nox', 'scr'])}
                    if diesel_monitors:
                        print("Diesel system monitors:")
                        for name, status in diesel_monitors.items():
                            complete = "✅" if status.get('complete', False) else "⏳"
                            print(f"  {complete} {name}")
            
            print("\n✅ Diagnostics completed successfully")
            
        else:
            print("❌ Failed to connect to vehicle")


def run_examples() -> None:
    """Run example scripts"""
    print("Available Examples:")
    print("=" * 18)
    
    examples_dir = os.path.join(os.path.dirname(__file__), 'examples')
    
    if os.path.exists(examples_dir):
        example_files = [f for f in os.listdir(examples_dir) if f.endswith('.py')]
        
        for i, example_file in enumerate(example_files, 1):
            print(f"{i}. {example_file}")
        
        print(f"\nTo run an example:")
        print(f"python examples/basic_usage.py")
        print(f"python examples/diesel_n57d30_example.py")
    else:
        print("Examples directory not found")


def main():
    """Main launcher function"""
    parser = argparse.ArgumentParser(
        description="BMW OBD2 Diagnostics Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list-configs                    # List BMW configurations
  %(prog)s --scan                           # Scan for adapters
  %(prog)s --test F13_650i                  # Test connection with gasoline engine
  %(prog)s --test F13_535d --diesel         # Test connection with diesel engine
  %(prog)s --diagnostics --diesel           # Run diesel diagnostics
  %(prog)s --diagnostics --port /dev/ttyUSB0 # Use specific port
  %(prog)s --examples                       # Show available examples
        """
    )
    
    parser.add_argument('--list-configs', action='store_true',
                        help='List available BMW configurations')
    parser.add_argument('--scan', action='store_true',
                        help='Scan for OBD2 adapters')
    parser.add_argument('--test', metavar='BMW_CONFIG',
                        help='Test connection with specified BMW configuration')
    parser.add_argument('--diagnostics', action='store_true',
                        help='Run full diagnostics session')
    parser.add_argument('--examples', action='store_true',
                        help='Show available example scripts')
    
    parser.add_argument('--port', metavar='PORT',
                        help='Specify OBD2 adapter port (e.g., /dev/ttyUSB0 or COM3)')
    parser.add_argument('--diesel', action='store_true',
                        help='Enable diesel engine mode (N57D30 support)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        default='INFO', help='Set logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Execute requested action
    if args.list_configs:
        list_bmw_configs()
    elif args.scan:
        scan_adapters()
    elif args.test:
        test_connection(args.test, args.port)
    elif args.diagnostics:
        bmw_config = "F13_535d" if args.diesel else None
        run_diagnostics(bmw_config, args.port, args.diesel)
    elif args.examples:
        run_examples()
    else:
        # Default action - show help and available configurations
        parser.print_help()
        print(f"\n")
        list_bmw_configs()


if __name__ == "__main__":
    main()