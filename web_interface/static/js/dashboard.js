/**
 * BMW OBD2 Diagnostics - Dashboard JavaScript
 * Handles WebSocket connections, data updates, and UI interactions
 */

// Global variables
let socket = null;
let connectionStatus = false;
let lastDataUpdate = null;

// Initialize WebSocket connection
function initializeWebSocket() {
    try {
        socket = io();
        window.socket = socket; // Make socket globally available
        
        // Connection events
        socket.on('connect', function() {
            console.log('WebSocket connected');
            showNotification('Connected to BMW Diagnostics Server', 'success');
        });
        
        socket.on('disconnect', function() {
            console.log('WebSocket disconnected');
            showNotification('Disconnected from server', 'error');
        });
        
        socket.on('connection_response', function(data) {
            console.log('Connection response:', data);
        });
        
        // Live data updates
        socket.on('live_data_update', function(data) {
            console.log('Live data update received:', data);
            if (typeof handleLiveDataUpdate === 'function') {
                handleLiveDataUpdate(data);
            }
            lastDataUpdate = new Date();
        });
        
        // Error handling
        socket.on('connect_error', function(error) {
            console.error('WebSocket connection error:', error);
            showNotification('Connection error: ' + error.message, 'error');
        });
        
    } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
        showNotification('Failed to initialize WebSocket connection', 'error');
    }
}

// Update connection status
async function updateConnectionStatus() {
    try {
        const response = await fetch('/api/connection-status');
        const data = await response.json();
        
        connectionStatus = data.connected;
        const statusElement = document.getElementById('connection-status');
        const statusText = document.getElementById('connection-text');
        const connectBtn = document.getElementById('connect-btn');
        
        if (data.connected) {
            statusElement.className = 'status-indicator connected';
            statusText.textContent = 'Connected';
            connectBtn.innerHTML = '<i class="fas fa-unlink me-1"></i>Disconnect';
            connectBtn.className = 'btn btn-outline-danger btn-sm me-2';
        } else {
            statusElement.className = 'status-indicator disconnected';
            statusText.textContent = 'Disconnected';
            connectBtn.innerHTML = '<i class="fas fa-plug me-1"></i>Connect';
            connectBtn.className = 'btn btn-outline-primary btn-sm me-2';
        }
        
    } catch (error) {
        console.error('Error updating connection status:', error);
    }
}

// Toggle connection
async function toggleConnection() {
    const connectBtn = document.getElementById('connect-btn');
    const originalContent = connectBtn.innerHTML;
    
    try {
        // Show loading state
        connectBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Connecting...';
        connectBtn.disabled = true;
        
        if (connectionStatus) {
            // Disconnect
            const response = await fetch('/api/disconnect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();
            
            if (data.success) {
                showNotification('Disconnected from vehicle', 'info');
            } else {
                showNotification('Disconnect failed: ' + data.message, 'error');
            }
        } else {
            // Connect
            const response = await fetch('/api/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const data = await response.json();
            
            if (data.success) {
                showNotification('Connected to BMW vehicle', 'success');
            } else {
                showNotification('Connection failed: ' + data.message, 'error');
            }
        }
        
        // Update status after a short delay
        setTimeout(updateConnectionStatus, 1000);
        
    } catch (error) {
        console.error('Error toggling connection:', error);
        showNotification('Connection error: ' + error.message, 'error');
    } finally {
        // Restore button state
        connectBtn.innerHTML = originalContent;
        connectBtn.disabled = false;
    }
}

// Show notifications
function showNotification(message, type = 'info') {
    const toast = document.getElementById('notification-toast');
    const toastIcon = document.getElementById('toast-icon');
    const toastTitle = document.getElementById('toast-title');
    const toastBody = document.getElementById('toast-body');
    const toastTime = document.getElementById('toast-time');
    
    // Set icon and style based on type
    let iconClass = 'fas fa-info-circle';
    let titleText = 'BMW Diagnostics';
    
    switch (type) {
        case 'success':
            iconClass = 'fas fa-check-circle text-success';
            titleText = 'Success';
            break;
        case 'error':
            iconClass = 'fas fa-exclamation-circle text-danger';
            titleText = 'Error';
            break;
        case 'warning':
            iconClass = 'fas fa-exclamation-triangle text-warning';
            titleText = 'Warning';
            break;
        default:
            iconClass = 'fas fa-info-circle text-info';
            titleText = 'Info';
    }
    
    toastIcon.className = iconClass + ' me-2';
    toastTitle.textContent = titleText;
    toastBody.textContent = message;
    toastTime.textContent = 'now';
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

// Refresh data
function refreshData() {
    if (socket && socket.connected) {
        socket.emit('request_live_data');
        showNotification('Refreshing data...', 'info');
    } else {
        showNotification('Not connected to server', 'warning');
    }
}

// Export data functionality
function exportData() {
    if (!connectionStatus) {
        showNotification('Connect to vehicle first', 'warning');
        return;
    }
    
    fetch('/api/live-data')
        .then(response => response.json())
        .then(data => {
            const dataStr = JSON.stringify(data, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            
            const link = document.createElement('a');
            link.href = URL.createObjectURL(dataBlob);
            link.download = `bmw_diagnostics_${new Date().toISOString().slice(0, 19)}.json`;
            link.click();
            
            showNotification('Data exported successfully', 'success');
        })
        .catch(error => {
            console.error('Export error:', error);
            showNotification('Export failed: ' + error.message, 'error');
        });
}

// Export table data
function exportTableData() {
    const table = document.getElementById('live-data-table');
    const rows = Array.from(table.querySelectorAll('tr'));
    
    let csvContent = '';
    rows.forEach(row => {
        const cells = Array.from(row.querySelectorAll('th, td'));
        const rowData = cells.map(cell => '"' + cell.textContent.replace(/"/g, '""') + '"');
        csvContent += rowData.join(',') + '\n';
    });
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `bmw_live_data_${new Date().toISOString().slice(0, 19)}.csv`;
    link.click();
    
    showNotification('Table data exported successfully', 'success');
}

// Toggle units (metric/imperial)
let useMetricUnits = true;
function toggleUnits() {
    useMetricUnits = !useMetricUnits;
    showNotification(`Switched to ${useMetricUnits ? 'metric' : 'imperial'} units`, 'info');
    
    // Refresh data to apply new units
    if (socket && socket.connected) {
        socket.emit('request_live_data');
    }
}

// Show about dialog
function showAbout() {
    const aboutHtml = `
        <div class="modal fade" id="aboutModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content bg-dark text-white">
                    <div class="modal-header">
                        <h5 class="modal-title"><i class="fas fa-car-side me-2 text-primary"></i>BMW OBD2 Diagnostics</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p><strong>Premium BMW OBD2 Diagnostics Tool</strong></p>
                        <p>Features:</p>
                        <ul>
                            <li>Real-time dual turbo PSI monitoring</li>
                            <li>BMW F13 generation support</li>
                            <li>Live engine diagnostics</li>
                            <li>Professional automotive UI</li>
                            <li>WebSocket real-time updates</li>
                        </ul>
                        <hr>
                        <p><small>Version 1.0 - Premium Interface</small></p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('aboutModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', aboutHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('aboutModal'));
    modal.show();
    
    // Remove modal from DOM when hidden
    document.getElementById('aboutModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// Update live data table
function updateLiveDataTable(liveData) {
    const tbody = document.getElementById('live-data-tbody');
    
    if (!liveData || !liveData.data) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted">
                    <i class="fas fa-exclamation-triangle me-2"></i>No data available
                </td>
            </tr>
        `;
        return;
    }
    
    let rows = '';
    Object.entries(liveData.data).forEach(([key, data]) => {
        if (data && typeof data === 'object') {
            const value = data.value !== null && data.value !== undefined ? data.value : '--';
            const unit = data.unit || '';
            const bmwNotes = data.bmw_notes || '';
            const interpretation = data.bmw_interpretation || 'Normal';
            
            // Apply unit conversion if needed
            let displayValue = value;
            let displayUnit = unit;
            
            if (!useMetricUnits) {
                // Convert to imperial units where applicable
                if (unit === 'celsius' && typeof value === 'number') {
                    displayValue = Math.round((value * 9/5) + 32);
                    displayUnit = '°F';
                } else if (unit === 'kilometer_per_hour' && typeof value === 'number') {
                    displayValue = Math.round(value * 0.621371);
                    displayUnit = 'mph';
                }
            }
            
            rows += `
                <tr>
                    <td><strong>${key.replace(/_/g, ' ')}</strong></td>
                    <td><span class="text-primary">${displayValue}</span></td>
                    <td><small class="text-muted">${displayUnit}</small></td>
                    <td><span class="badge bg-info">${interpretation}</span></td>
                    <td><small class="text-muted">${bmwNotes}</small></td>
                </tr>
            `;
        }
    });
    
    if (rows) {
        tbody.innerHTML = rows;
    } else {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted">
                    <i class="fas fa-hourglass-half me-2"></i>Loading data...
                </td>
            </tr>
        `;
    }
}

// Utility functions
function formatValue(value, decimals = 1) {
    if (value === null || value === undefined || isNaN(value)) {
        return '--';
    }
    return Number(value).toFixed(decimals);
}

function getStatusColor(value, thresholds) {
    if (!thresholds || value === null || value === undefined) {
        return 'text-muted';
    }
    
    if (value < thresholds.low) return 'text-success';
    if (value < thresholds.medium) return 'text-warning';
    return 'text-danger';
}

// Error handling for failed requests
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showNotification('An error occurred: ' + event.reason.message, 'error');
});

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});