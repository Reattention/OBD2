// BMW OBD2 Diagnosticator Frontend
class BMWDiagnosticsApp {
    constructor() {
        this.isConnected = false;
        this.charts = {};
        this.dataHistory = {};
        this.maxDataPoints = 50;
        this.pollInterval = null;
        
        this.initializeApp();
        this.createCharts();
    }
    
    initializeApp() {
        // Initialize UI elements
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusText = document.getElementById('statusText');
        this.connectBtn = document.getElementById('connectBtn');
        
        // Check initial connection status
        this.checkConnectionStatus();
        
        // Set up periodic status checks (every 3 seconds when not connected)
        this.pollInterval = setInterval(() => {
            if (!this.isConnected) {
                this.checkConnectionStatus();
            }
        }, 3000);
    }
    
    async checkConnectionStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            this.updateConnectionStatus(data.connected);
            if (data.data && Object.keys(data.data).length > 0) {
                this.updateDashboard(data.data);
                this.updateCharts(data.data);
            }
        } catch (error) {
            console.error('Error checking status:', error);
        }
    }
    
    updateConnectionStatus(connected) {
        this.isConnected = connected;
        this.statusIndicator.className = `status-indicator ${connected ? 'connected' : 'disconnected'}`;
        this.statusText.textContent = connected ? 'Connected' : 'Disconnected';
        this.connectBtn.innerHTML = connected ? 
            '<i class="fas fa-unlink"></i> Disconnect' : 
            '<i class="fas fa-plug"></i> Connect';
        
        // Start fast polling when connected
        if (connected && !this.pollInterval) {
            this.pollInterval = setInterval(() => this.checkConnectionStatus(), 2000);
        } else if (!connected && this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = setInterval(() => this.checkConnectionStatus(), 3000);
        }
    }
    
    updateDashboard(data) {
        // Update RPM
        if (data.rpm) {
            const rpmValue = Math.round(data.rpm.value);
            document.getElementById('rpmValue').textContent = rpmValue;
            this.updateGauge('rpmGauge', rpmValue, 8000, '#007AFF');
        }
        
        // Update Speed
        if (data.speed) {
            const speedValue = Math.round(data.speed.value);
            document.getElementById('speedValue').textContent = speedValue;
            this.updateGauge('speedGauge', speedValue, 250, '#32D74B');
        }
        
        // Update Coolant Temperature
        if (data.coolant_temp) {
            const temp = Math.round(data.coolant_temp.value);
            document.getElementById('coolantTemp').textContent = temp;
            this.updateTrendIndicator('coolantTemp', temp, 90);
        }
        
        // Update Engine Load
        if (data.engine_load) {
            const load = Math.round(data.engine_load.value);
            document.getElementById('engineLoad').textContent = load;
            document.getElementById('engineLoadBar').style.width = `${load}%`;
        }
        
        // Update Fuel Level
        if (data.fuel_level) {
            const fuel = Math.round(data.fuel_level.value);
            document.getElementById('fuelLevel').textContent = fuel;
            document.getElementById('fuelLevelBar').style.width = `${fuel}%`;
        }
        
        // Update MAF Flow
        if (data.maf) {
            document.getElementById('mafFlow').textContent = data.maf.value.toFixed(2);
        }
        
        // Update BMW specific parameters
        this.updateBMWParameters(data);
    }
    
    updateBMWParameters(data) {
        const paramMap = {
            'intake_pressure': 'intakePressure',
            'intake_temp': 'intakeTemp',
            'throttle_pos': 'throttlePos',
            'fuel_pressure': 'fuelPressure',
            'timing_advance': 'timingAdvance',
            'fuel_rate': 'fuelRate'
        };
        
        Object.entries(paramMap).forEach(([dataKey, elementId]) => {
            if (data[dataKey]) {
                const value = data[dataKey].value;
                const unit = data[dataKey].unit || '';
                const formattedValue = typeof value === 'number' ? value.toFixed(1) : value;
                document.getElementById(elementId).textContent = `${formattedValue} ${unit}`;
            }
        });
    }
    
    updateGauge(canvasId, value, maxValue, color) {
        const canvas = document.getElementById(canvasId);
        const ctx = canvas.getContext('2d');
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = 80;
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Background arc
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0.75 * Math.PI, 0.25 * Math.PI);
        ctx.lineWidth = 8;
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.stroke();
        
        // Value arc
        const angle = 0.75 * Math.PI + (value / maxValue) * 1.5 * Math.PI;
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0.75 * Math.PI, angle);
        ctx.lineWidth = 8;
        ctx.lineCap = 'round';
        
        // Gradient for the gauge
        const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
        gradient.addColorStop(0, color);
        gradient.addColorStop(1, color + '80');
        ctx.strokeStyle = gradient;
        ctx.stroke();
        
        // Center dot
        ctx.beginPath();
        ctx.arc(centerX, centerY, 4, 0, 2 * Math.PI);
        ctx.fillStyle = color;
        ctx.fill();
    }
    
    updateTrendIndicator(elementId, currentValue, threshold) {
        const element = document.getElementById(elementId).parentElement;
        const indicator = element.querySelector('.trend-indicator');
        
        if (indicator) {
            indicator.className = 'trend-indicator';
            if (currentValue > threshold) {
                indicator.classList.add('trend-up');
            } else if (currentValue < threshold * 0.8) {
                indicator.classList.add('trend-down');
            }
        }
    }
    
    createCharts() {
        const ctx = document.getElementById('liveChart').getContext('2d');
        
        this.charts.liveChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'RPM',
                        data: [],
                        borderColor: '#007AFF',
                        backgroundColor: 'rgba(0, 122, 255, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Speed (km/h)',
                        data: [],
                        borderColor: '#32D74B',
                        backgroundColor: 'rgba(50, 215, 75, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y1'
                    },
                    {
                        label: 'Engine Load (%)',
                        data: [],
                        borderColor: '#FF9500',
                        backgroundColor: 'rgba(255, 149, 0, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y2'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        display: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.8)'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.8)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: false,
                        position: 'right'
                    },
                    y2: {
                        type: 'linear',
                        display: false,
                        position: 'right'
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: 'rgba(255, 255, 255, 0.8)'
                        }
                    }
                },
                elements: {
                    point: {
                        radius: 0
                    }
                }
            }
        });
    }
    
    updateCharts(data) {
        const currentTime = new Date().toLocaleTimeString();
        
        // Add new data point
        this.charts.liveChart.data.labels.push(currentTime);
        
        // Update RPM
        if (data.rpm) {
            this.charts.liveChart.data.datasets[0].data.push(data.rpm.value);
        }
        
        // Update Speed
        if (data.speed) {
            this.charts.liveChart.data.datasets[1].data.push(data.speed.value);
        }
        
        // Update Engine Load
        if (data.engine_load) {
            this.charts.liveChart.data.datasets[2].data.push(data.engine_load.value);
        }
        
        // Keep only last 50 data points
        if (this.charts.liveChart.data.labels.length > this.maxDataPoints) {
            this.charts.liveChart.data.labels.shift();
            this.charts.liveChart.data.datasets.forEach(dataset => {
                dataset.data.shift();
            });
        }
        
        this.charts.liveChart.update('none');
    }
    
    async refreshDTCs() {
        try {
            const response = await fetch('/api/dtcs');
            const data = await response.json();
            this.displayDTCs(data.dtcs);
        } catch (error) {
            console.error('Error fetching DTCs:', error);
        }
    }
    
    displayDTCs(dtcs) {
        const dtcList = document.getElementById('dtcList');
        
        if (dtcs.length === 0) {
            dtcList.innerHTML = '<div class="no-codes">No diagnostic trouble codes found</div>';
        } else {
            dtcList.innerHTML = dtcs.map(dtc => `
                <div class="dtc-item">
                    <span class="dtc-code">${dtc.code}</span>
                    <span class="dtc-description">${dtc.description}</span>
                </div>
            `).join('');
        }
    }
    
    async clearDTCs() {
        if (confirm('Are you sure you want to clear all diagnostic trouble codes?')) {
            try {
                const response = await fetch('/api/clear_dtcs', { method: 'POST' });
                const data = await response.json();
                
                if (data.cleared) {
                    this.refreshDTCs();
                    this.showNotification('DTCs cleared successfully', 'success');
                } else {
                    this.showNotification('Failed to clear DTCs', 'error');
                }
            } catch (error) {
                console.error('Error clearing DTCs:', error);
                this.showNotification('Error clearing DTCs', 'error');
            }
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--glass-bg);
            backdrop-filter: var(--backdrop-blur);
            border: 1px solid var(--glass-border);
            border-radius: var(--border-radius);
            padding: 16px 20px;
            color: var(--text-primary);
            z-index: 1000;
            box-shadow: var(--shadow-glass);
            transform: translateX(400px);
            transition: transform 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(400px)';
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// Global functions
async function toggleConnection() {
    const app = window.bmwApp;
    
    if (app.isConnected) {
        try {
            const response = await fetch('/api/disconnect', { method: 'POST' });
            const data = await response.json();
            
            if (data.disconnected) {
                app.showNotification('Disconnected from OBD2 adapter', 'info');
            }
        } catch (error) {
            console.error('Error disconnecting:', error);
            app.showNotification('Error disconnecting', 'error');
        }
    } else {
        try {
            const response = await fetch('/api/connect', { method: 'POST' });
            const data = await response.json();
            
            if (data.connected) {
                app.showNotification('Connected to OBD2 adapter', 'success');
                // Start fast polling for live data
                app.checkConnectionStatus();
            } else {
                app.showNotification('Failed to connect to OBD2 adapter', 'error');
            }
        } catch (error) {
            console.error('Error connecting:', error);
            app.showNotification('Error connecting to OBD2 adapter', 'error');
        }
    }
}

function refreshDTCs() {
    window.bmwApp.refreshDTCs();
}

function clearDTCs() {
    window.bmwApp.clearDTCs();
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.bmwApp = new BMWDiagnosticsApp();
    
    // Initial DTC load
    window.bmwApp.refreshDTCs();
});