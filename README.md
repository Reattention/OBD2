# BMW OBD2 Bluetooth Diagnosticator

A professional-grade OBD2 diagnostic tool specifically designed for BMW vehicles, featuring iOS 26 Glassmorphism styling and real-time data monitoring. This application is optimized for BMW 640D F13 RWD models but supports most BMW vehicles with OBD2 ports.

## Features

### 🚗 BMW-Specific Diagnostics
- Real-time engine parameters monitoring
- BMW F13 generation specific PIDs
- Diesel engine parameters (640D optimized)
- Turbo pressure and intake monitoring
- DPF (Diesel Particulate Filter) status

### 🎨 Modern UI/UX
- iOS 26 Glassmorphism design language
- Responsive layout for all screen sizes
- Real-time gauge visualizations
- Live data charting
- Smooth animations and transitions

### 📊 AutoDoc-Like Features
- Diagnostic Trouble Code (DTC) reading and clearing
- Live data streaming
- Historical data visualization
- Parameter trending analysis
- Professional diagnostic interface

### 🔧 Technical Capabilities
- Bluetooth OBD2 adapter support
- WebSocket real-time communication
- RESTful API endpoints
- Cross-platform compatibility
- Localhost web interface

## Requirements

### Hardware
- OBD2 Bluetooth adapter (ELM327 compatible)
- BMW vehicle with OBD2 port (1996+)
- Computer with Bluetooth capability

### Software
- Python 3.7+
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Bluetooth stack (BlueZ on Linux, native on Windows/macOS)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Reattention/OBD2.git
   cd OBD2
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Pair your OBD2 adapter:**
   - Turn on your vehicle's ignition
   - Plug in the OBD2 adapter to your vehicle's diagnostic port
   - Pair the adapter with your computer via Bluetooth
   - Note the adapter's COM port (Windows) or device path (Linux/macOS)

## Usage

1. **Start the application:**
   ```bash
   python app.py
   ```

2. **Open your web browser:**
   Navigate to `http://localhost:5000`

3. **Connect to your vehicle:**
   - Click the "Connect" button in the top-right corner
   - The application will auto-detect your OBD2 adapter
   - Once connected, real-time data will begin streaming

4. **Monitor your BMW:**
   - View real-time engine parameters
   - Check diagnostic trouble codes
   - Monitor BMW-specific parameters
   - Analyze live data charts

## BMW 640D F13 Specific Parameters

This application includes specialized monitoring for:

- **Engine Management:**
  - Turbo boost pressure
  - Intercooler temperature
  - EGR valve position
  - DPF pressure differential

- **Fuel System:**
  - High-pressure fuel rail pressure
  - Fuel injection timing
  - Fuel rail temperature
  - AdBlue level (if equipped)

- **Transmission (if automatic):**
  - Transmission fluid temperature
  - Gear position
  - Torque converter status

## API Endpoints

- `GET /` - Main dashboard
- `POST /api/connect` - Connect to OBD2 adapter
- `POST /api/disconnect` - Disconnect from adapter
- `GET /api/status` - Get connection status and current data
- `GET /api/dtcs` - Retrieve diagnostic trouble codes
- `POST /api/clear_dtcs` - Clear diagnostic trouble codes

## WebSocket Events

- `connect` - Client connected to server
- `disconnect` - Client disconnected
- `obd_data` - Real-time OBD2 data stream
- `status` - Connection status updates

## Troubleshooting

### Connection Issues
- Ensure OBD2 adapter is properly paired
- Check that the vehicle's ignition is on
- Verify the adapter is compatible (ELM327 recommended)
- Try different COM ports if auto-detection fails

### Data Not Updating
- Check vehicle compatibility
- Ensure the engine is running for most parameters
- Some parameters may not be available on all BMW models
- Verify the adapter supports the required protocols

### Performance Issues
- Close unnecessary browser tabs
- Check Bluetooth signal strength
- Restart the application if data becomes stale

## Development

### Project Structure
```
OBD2/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html     # Main dashboard template
├── static/
│   ├── css/
│   │   └── style.css  # Glassmorphism styling
│   ├── js/
│   │   └── app.js     # Frontend JavaScript
│   └── images/        # Static images
└── README.md          # This file
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with BMW vehicles
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational and diagnostic purposes only. Always consult with qualified BMW technicians for serious vehicle issues. The authors are not responsible for any damage caused by the use of this software.

## Compatibility

### Tested BMW Models
- 640D F13 RWD (primary target)
- 6 Series F06/F12/F13 (2011-2018)
- Other BMW models with OBD2 support

### Supported OBD2 Adapters
- ELM327 Bluetooth (recommended)
- OBDLink MX+
- BlueDriver
- Most generic ELM327 clones

## Support

For issues, questions, or contributions, please visit:
- GitHub Issues: https://github.com/Reattention/OBD2/issues
- BMW forums for vehicle-specific questions
- OBD2 community resources