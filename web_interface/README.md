# BMW OBD2 Diagnostics - Premium Web Interface

A professional-grade Flask web interface for BMW OBD2 diagnostics featuring real-time dual turbocharger PSI monitoring and premium automotive UI design.

## Features

### 🎨 Premium UI Design ($1000+ Grade)
- **BMW-themed dark interface** with professional automotive styling
- **BMW color scheme**: Blue (#1C69D4), White, Black with gradients
- **Responsive design** for desktop, tablet, and mobile
- **Real-time animated gauges** with smooth 60fps animations
- **Professional typography** using Inter font family
- **Interactive elements** with hover effects and transitions

### 🚗 BMW-Specific Features
- **F13 generation support** (6 Series Coupe 2011-2018)
- **N63 twin-turbo engine** specific monitoring
- **BMW PID interpretations** with expert analysis
- **Valvetronic system** monitoring capabilities
- **BMW DTC database** with specific trouble codes

### 💨 Dual Turbocharger PSI Monitoring
- **Individual turbo gauges** for Turbo 1 and Turbo 2
- **Real-time PSI conversion** from kPa/bar to PSI
- **Boost/vacuum ranges** with color-coded indicators
- **PSI precision control** (0-2 decimal places)
- **Warning thresholds** for safe operation
- **Data logging** for analysis and troubleshooting

### ⚡ Real-Time Features
- **WebSocket integration** for live data updates
- **Auto-reconnection** on adapter disconnect
- **1-second refresh rate** (configurable)
- **Live data caching** to prevent UI freezing
- **Connection status** monitoring

## Installation

### Prerequisites
- Python 3.7+
- BMW OBD2 adapter (ELM327, OBDLink, etc.)
- BMW F13 vehicle (or compatible)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run the Application
```bash
cd web_interface
python app.py
```

The web interface will be available at: `http://127.0.0.1:5000`

## Usage

### Dashboard
- **Real-time gauges**: RPM, Speed, Coolant Temperature, Engine Load
- **Dual turbo PSI monitoring**: Individual gauges for each turbocharger
- **Additional parameters**: Throttle Position, Fuel Pressure, Intake Temperature, MAF
- **Live data table**: Comprehensive parameter monitoring with BMW interpretations

### DTC Scanner
- **Real-time DTC scanning** with BMW-specific codes
- **MIL status monitoring** (Check Engine Light)
- **DTC analysis** with priority issues and recommendations
- **BMW-specific trouble codes**: N63 turbo codes, Valvetronic codes
- **Clear DTCs** functionality with confirmation

### Settings
- **Connection settings**: Adapter type, port, protocol configuration
- **BMW vehicle settings**: Generation, model year, engine type
- **Display settings**: Theme, units, refresh rate, animations
- **Dual turbo settings**: PSI units, precision, warning thresholds
- **Advanced settings**: Retry attempts, debug mode, fast mode

## API Endpoints

### Live Data
- `GET /api/live-data` - Get real-time OBD2 data
- `GET /api/turbo-pressure` - Get dual turbo PSI readings
- `GET /api/connection-status` - Check connection status

### Diagnostics
- `GET /api/dtcs` - Get diagnostic trouble codes
- `POST /api/clear-dtcs` - Clear all DTCs

### Connection Management
- `POST /api/connect` - Connect to vehicle
- `POST /api/disconnect` - Disconnect from vehicle

### WebSocket Events
- `live_data_update` - Real-time data updates
- `request_live_data` - Request immediate data refresh

## Technical Details

### Architecture
- **Flask** web framework with SocketIO
- **Bootstrap 5** for responsive design
- **Chart.js** for animated gauges
- **Font Awesome** for professional icons
- **WebSocket** for real-time communication

### Turbo PSI Conversion
```python
# kPa to PSI conversion
PSI = kPa × 0.145038

# Bar to PSI conversion  
PSI = bar × 14.5038

# Typical ranges
# Vacuum: -14.7 to 0 PSI
# Atmospheric: 0 PSI
# Boost: 0 to +15 PSI (typical max)
```

### File Structure
```
web_interface/
├── app.py                 # Main Flask application
├── templates/
│   ├── base.html         # Base template with navigation
│   ├── dashboard.html    # Main dashboard with gauges
│   ├── dtc_scanner.html  # DTC management interface
│   └── settings.html     # Configuration interface
├── static/
│   ├── css/
│   │   └── dashboard.css # Premium BMW styling
│   └── js/
│       ├── dashboard.js  # Core functionality
│       └── gauges.js     # Gauge animations
└── api/
    └── __init__.py       # API blueprint
```

## Customization

### BMW Models
Currently optimized for F13 generation. Additional models can be added by:
1. Adding model configurations in `config.py`
2. Implementing model-specific PIDs in `bmw_pids.py`
3. Adding DTC definitions in `dtc_handler.py`

### Styling
The interface uses CSS custom properties for easy customization:
```css
:root {
    --bmw-blue: #1C69D4;
    --bmw-blue-dark: #1557B3;
    --bmw-blue-light: #4A8AE8;
    /* Modify these to change the color scheme */
}
```

### Gauge Configuration
Gauges can be customized in `gauges.js`:
- Update ranges and thresholds
- Modify color schemes
- Add new gauge types
- Adjust animation settings

## Troubleshooting

### Common Issues
1. **WebSocket connection failed**: Ensure Flask-SocketIO is installed and no firewall blocking
2. **OBD2 adapter not found**: Check adapter connection and drivers
3. **No live data**: Verify vehicle connection and ignition is ON
4. **Turbo data showing 0**: May indicate no boost or adapter compatibility issues

### Debug Mode
Enable debug mode in Settings > Advanced Settings for detailed logging.

## Performance

### Optimizations
- **Throttled updates**: 100ms minimum between gauge updates
- **Data caching**: 1-second cache for live data
- **Efficient rendering**: CSS transforms for smooth animations
- **Lazy loading**: Charts initialized only when needed

### Browser Compatibility
- **Chrome/Edge**: Full support with hardware acceleration
- **Firefox**: Full support
- **Safari**: Full support (may need WebSocket polyfill for older versions)
- **Mobile browsers**: Responsive design with touch optimization

## License

MIT License - see main project LICENSE file.

## Acknowledgments

- BMW for the exceptional F13 platform
- python-OBD library for reliable OBD2 communication
- Chart.js for beautiful gauge animations
- Bootstrap team for responsive design framework