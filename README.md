# BMW OBD2 Diagnostics Tool

A comprehensive OBD2 diagnostics tool specifically designed for BMW vehicles, featuring real ECU communication and BMW-specific PID support. This tool replaces simulated data with actual OBD2 adapter communication using the python-OBD library.

## Features

### 🚗 Real OBD2 Communication
- **Real adapter support**: ELM327, OBDLink, and other OBD2 adapters
- **Multiple connection types**: USB, Bluetooth, and WiFi adapters
- **Protocol support**: ISO 15765-4 (CAN), ISO 14230-4 (KWP2000), and more
- **Auto-detection**: Automatic adapter and protocol detection

### 🔧 BMW-Specific Features
- **BMW F13 generation support**: Optimized for 6 Series Coupe/Convertible
- **BMW-specific PIDs**: Extended PIDs for BMW systems
- **Valvetronic support**: BMW variable valve lift diagnostics
- **Twin-turbo diagnostics**: N63 engine specific monitoring
- **BMW DTC interpretation**: BMW-specific trouble code descriptions

### 📊 Comprehensive Diagnostics
- **Live data monitoring**: Real-time engine and vehicle parameters
- **DTC management**: Read, interpret, and clear diagnostic trouble codes
- **Freeze frame data**: Capture data at the time of fault occurrence
- **Readiness tests**: OBD2 monitor status and emission readiness
- **BMW analysis**: Intelligent interpretation of BMW-specific data

### 🛠️ Advanced Features
- **Error handling**: Robust connection and communication error handling
- **Auto-reconnection**: Automatic reconnection on connection loss
- **Configuration management**: Flexible configuration for different BMW models
- **Logging support**: Comprehensive logging for debugging and analysis
- **Thread-safe**: Safe for use in multi-threaded applications

## Installation

### Prerequisites
- Python 3.7 or higher
- OBD2 adapter (ELM327, OBDLink, etc.)
- BMW vehicle with OBD2 port (1996 or newer)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Install Package
```bash
pip install -e .
```

## Quick Start

### Basic Usage
```python
from obd2_diagnostics import BMWDiagnostics
from obd2_diagnostics.config import OBD2Config

# Create configuration
config = OBD2Config()
config.generation = "F13"  # BMW F13 generation
config.bmw_extended_pids = True

# Connect to BMW vehicle
with BMWDiagnostics(config) as diagnostics:
    if diagnostics.connect(auto_detect=True):
        # Get live data
        live_data = diagnostics.get_live_data()
        print(f"Engine RPM: {live_data['data']['RPM']['value']}")
        
        # Get diagnostic trouble codes
        dtcs = diagnostics.get_dtcs()
        print(f"Total DTCs: {dtcs['status']['total_dtcs']}")
        
        # Get comprehensive summary
        summary = diagnostics.get_diagnostic_summary()
```

### Advanced Configuration
```python
from obd2_diagnostics.config import OBD2Config, AdapterType, Protocol

config = OBD2Config()

# Adapter settings
config.adapter_type = AdapterType.ELM327
config.port = "/dev/ttyUSB0"  # or "COM3" on Windows
config.baudrate = 38400
config.timeout = 10.0

# BMW-specific settings
config.generation = "F13"
config.model_year = 2012
config.engine_type = "N63"  # Twin-turbo V8

# Protocol settings
config.protocol = Protocol.ISO_15765_4  # CAN bus
config.fast_mode = True

# Error handling
config.retry_attempts = 3
config.reconnect_delay = 2.0
```

## BMW Model Support

### Supported Generations
- **F13**: 6 Series Coupe/Convertible (2011-2018)
- Additional generations can be added with proper PID definitions

### Supported Engines
- **N63**: Twin-turbo V8 (650i)
- **N55**: Single-turbo I6 (640i)
- Additional engines supported through standard OBD2 PIDs

### Pre-configured Models
```python
# Set pre-configured BMW model
diagnostics.set_bmw_config("F13_650i")  # N63 twin-turbo V8
diagnostics.set_bmw_config("F13_640i")  # N55 single-turbo I6
```

## OBD2 Adapter Compatibility

### Tested Adapters
- **ELM327**: USB and Bluetooth versions
- **OBDLink SX**: Professional grade adapter
- **ScanTool OBDLink**: Various models
- **Generic ELM327 clones**: Basic functionality

### Connection Types
- **USB**: Reliable, plug-and-play
- **Bluetooth**: Wireless convenience
- **WiFi**: Some adapters support WiFi

### Auto-Detection
```python
# Scan for available adapters
from obd2_diagnostics.obd2_adapter import AdapterDiscovery

ports = AdapterDiscovery.scan_ports()
bluetooth_devices = AdapterDiscovery.scan_bluetooth()
auto_port = AdapterDiscovery.auto_detect_adapter(config)
```

## Live Data Monitoring

### Supported Parameters
- **Engine**: RPM, load, temperature, timing
- **Performance**: Speed, throttle position, boost pressure
- **Fuel**: Pressure, level, injection timing
- **Emissions**: MAF, intake temperature, O2 sensors
- **BMW-specific**: Valvetronic, turbo parameters

### Real-time Updates
```python
# Continuous monitoring
while diagnostics.is_connected():
    data = diagnostics.get_live_data(refresh=True)
    
    # Engine data with BMW interpretation
    rpm_data = data['data']['RPM']
    print(f"RPM: {rpm_data['value']} - {rpm_data['bmw_interpretation']}")
    
    # BMW-specific data
    bmw_data = data.get('bmw_specific', {})
    if bmw_data:
        print(f"Valvetronic: {bmw_data.get('valvetronic_position')}")
        print(f"Turbo Boost: {bmw_data.get('turbo_boost_target')}")
    
    time.sleep(1)
```

## Diagnostic Trouble Codes

### DTC Types
- **Powertrain (P)**: Engine and transmission codes
- **Chassis (C)**: ABS, suspension, steering codes
- **Body (B)**: Comfort and convenience codes
- **Network (U)**: Communication and CAN bus codes

### BMW-Specific DTCs
- **Valvetronic codes**: P1014-P1017
- **Twin-turbo codes**: P0299, P0234, P0235
- **Direct injection**: P0087, P0088
- **Communication**: U0100, U0101

### DTC Management
```python
# Read all DTCs
dtc_info = diagnostics.get_dtcs()

# Analyze DTCs
analysis = dtc_info['analysis']
priority_issues = analysis['priority_issues']
recommendations = analysis['recommendations']

# Clear DTCs (after repairs)
if diagnostics.clear_dtcs():
    print("DTCs cleared successfully")

# Get freeze frame data
freeze_data = diagnostics.get_freeze_frame_data("P0300")
```

## Error Handling and Reconnection

### Automatic Reconnection
```python
# Enable auto-reconnection
config.retry_attempts = 5
config.reconnect_delay = 3.0

# Connection callbacks
def on_connection_change(connected, error):
    if connected:
        print("Reconnected to vehicle")
    else:
        print(f"Connection lost: {error}")

diagnostics.add_connection_callback(on_connection_change)
```

### Error Recovery
- **Connection timeouts**: Automatic retry with exponential backoff
- **Protocol errors**: Automatic protocol re-detection
- **Adapter disconnection**: Continuous reconnection attempts
- **Invalid responses**: Command retry with error reporting

## Logging and Debugging

### Enable Logging
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bmw_diagnostics.log')
    ]
)

# Set log level in config
config.log_level = logging.DEBUG
config.log_file = 'detailed_diagnostics.log'
```

### Debug Information
- **Connection details**: Adapter info, protocols, port settings
- **Command traces**: OBD2 command requests and responses
- **Error details**: Detailed error messages and stack traces
- **Performance metrics**: Response times and success rates

## Examples

### Complete Examples
- `examples/basic_usage.py`: Comprehensive usage example
- `examples/live_monitoring.py`: Real-time data monitoring
- `examples/dtc_analysis.py`: DTC reading and analysis
- `examples/adapter_discovery.py`: Adapter detection and testing

### Run Example
```bash
cd examples
python basic_usage.py
```

## Testing

### Run Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_bmw_diagnostics.py

# Run with coverage
python -m pytest tests/ --cov=obd2_diagnostics
```

### Test Coverage
- Unit tests for all major components
- Mock-based testing for OBD2 communication
- Integration tests for real adapter scenarios
- BMW-specific functionality testing

## Troubleshooting

### Common Issues

#### Connection Problems
1. **"No adapter found"**
   - Check USB/Bluetooth connection
   - Verify adapter drivers are installed
   - Try different ports or re-pair Bluetooth

2. **"Connection timeout"**
   - Increase timeout in configuration
   - Check vehicle ignition is ON
   - Verify OBD2 port is functional

3. **"Protocol not supported"**
   - Try AUTO protocol detection
   - Check adapter compatibility with BMW
   - Some older BMWs may need specific protocols

#### Data Issues
1. **"No response from ECU"**
   - Vehicle may be in sleep mode
   - Try turning accessories on
   - Check OBD2 fuse

2. **"Incomplete data"**
   - Some PIDs may not be supported
   - BMW-specific PIDs need proper implementation
   - Check BMW generation compatibility

### BMW-Specific Notes
- **F13 generation**: Full support implemented
- **Valvetronic**: Requires specific PID implementation
- **iDrive**: Some features may need CAN bus access
- **Hybrid models**: May have different ECU layouts

## Contributing

### Development Setup
```bash
git clone https://github.com/Reattention/OBD2.git
cd OBD2
pip install -e .
pip install -r requirements-dev.txt
```

### Adding BMW Support
1. Add PID definitions in `bmw_pids.py`
2. Update model configurations in `config.py`
3. Add DTC descriptions in `dtc_handler.py`
4. Create tests for new functionality

## License

MIT License - see LICENSE file for details.

## Disclaimer

This tool is for diagnostic purposes only. Always consult BMW service documentation and qualified technicians for repairs. Use at your own risk.