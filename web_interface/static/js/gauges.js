/**
 * BMW OBD2 Diagnostics - Gauges JavaScript
 * Handles creation and animation of circular gauges, turbo PSI monitors, and other visualizations
 */

// Gauge instances
let rpmGauge = null;
let turbo1Gauge = null;
let turbo2Gauge = null;

// BMW color scheme
const bmwColors = {
    blue: '#1C69D4',
    blueDark: '#1557B3',
    blueLight: '#4A8AE8',
    white: '#FFFFFF',
    silver: '#C0C0C0',
    red: '#F44336',
    orange: '#FF9800',
    green: '#4CAF50',
    yellow: '#FFC107'
};

// Initialize all gauges
function initializeGauges() {
    initializeRPMGauge();
    console.log('Standard gauges initialized');
}

// Initialize turbo gauges
function initializeTurboGauges() {
    initializeTurbo1Gauge();
    initializeTurbo2Gauge();
    console.log('Turbo gauges initialized');
}

// Create RPM gauge
function initializeRPMGauge() {
    const ctx = document.getElementById('rpm-gauge');
    if (!ctx) return;

    const config = {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [0, 100],
                backgroundColor: [bmwColors.blue, 'rgba(255, 255, 255, 0.1)'],
                borderColor: [bmwColors.blue, 'rgba(255, 255, 255, 0.2)'],
                borderWidth: 2,
                cutout: '75%',
                circumference: 270,
                rotation: 225
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            },
            animation: {
                animateRotate: true,
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    };

    rpmGauge = new Chart(ctx, config);
}

// Create Turbo 1 PSI gauge
function initializeTurbo1Gauge() {
    const ctx = document.getElementById('turbo1-gauge');
    if (!ctx) return;

    turbo1Gauge = createTurboGauge(ctx, 'Turbo 1');
}

// Create Turbo 2 PSI gauge
function initializeTurbo2Gauge() {
    const ctx = document.getElementById('turbo2-gauge');
    if (!ctx) return;

    turbo2Gauge = createTurboGauge(ctx, 'Turbo 2');
}

// Create turbo PSI gauge
function createTurboGauge(ctx, label) {
    const config = {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [50, 50], // Default to center (0 PSI)
                backgroundColor: [
                    createTurboGradient(ctx),
                    'rgba(255, 255, 255, 0.1)'
                ],
                borderColor: [bmwColors.blue, 'rgba(255, 255, 255, 0.2)'],
                borderWidth: 3,
                cutout: '70%',
                circumference: 270,
                rotation: 225
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            },
            animation: {
                animateRotate: true,
                duration: 800,
                easing: 'easeOutCubic'
            }
        }
    };

    return new Chart(ctx, config);
}

// Create gradient for turbo gauges
function createTurboGradient(ctx) {
    const canvas = ctx.canvas || ctx;
    const context = canvas.getContext('2d');
    
    const gradient = context.createLinearGradient(0, 0, 0, canvas.height);
    gradient.addColorStop(0, bmwColors.red);     // High boost (red)
    gradient.addColorStop(0.3, bmwColors.orange); // Medium boost (orange)
    gradient.addColorStop(0.5, bmwColors.yellow); // Low boost (yellow)
    gradient.addColorStop(0.7, bmwColors.green);  // Atmospheric (green)
    gradient.addColorStop(1, bmwColors.blue);     // Vacuum (blue)
    
    return gradient;
}

// Update all gauges with live data
function updateAllGauges(liveData) {
    if (!liveData || !liveData.data) return;

    // Update RPM
    const rpmData = liveData.data.RPM;
    if (rpmData && rpmData.value !== null) {
        updateRPMGauge(rpmData.value);
        updateRPMDisplay(rpmData.value, rpmData.bmw_interpretation);
    }

    // Update Speed
    const speedData = liveData.data.SPEED;
    if (speedData && speedData.value !== null) {
        updateSpeedDisplay(speedData.value);
    }

    // Update Coolant Temperature
    const coolantData = liveData.data.COOLANT_TEMP;
    if (coolantData && coolantData.value !== null) {
        updateCoolantTemp(coolantData.value, coolantData.bmw_interpretation);
    }

    // Update Engine Load
    const loadData = liveData.data.ENGINE_LOAD;
    if (loadData && loadData.value !== null) {
        updateEngineLoad(loadData.value, loadData.bmw_interpretation);
    }

    // Update Throttle Position
    const throttleData = liveData.data.THROTTLE_POS;
    if (throttleData && throttleData.value !== null) {
        updateThrottlePosition(throttleData.value);
    }

    // Update additional parameters
    updateAdditionalParameters(liveData.data);
}

// Update RPM gauge
function updateRPMGauge(rpm) {
    if (!rpmGauge) return;

    const maxRpm = 7000; // BMW F13 redline
    const percentage = Math.min((rpm / maxRpm) * 100, 100);
    
    rpmGauge.data.datasets[0].data = [percentage, 100 - percentage];
    
    // Change color based on RPM
    let color = bmwColors.green;
    if (rpm > 6000) color = bmwColors.red;
    else if (rpm > 4000) color = bmwColors.orange;
    else if (rpm > 2000) color = bmwColors.yellow;
    
    rpmGauge.data.datasets[0].backgroundColor[0] = color;
    rpmGauge.update('none');
}

// Update RPM display
function updateRPMDisplay(rpm, interpretation) {
    const rpmValue = document.getElementById('rpm-value');
    const rpmStatus = document.getElementById('rpm-status');
    
    if (rpmValue) rpmValue.textContent = Math.round(rpm);
    if (rpmStatus) rpmStatus.textContent = interpretation || 'Normal';
}

// Update speed display
function updateSpeedDisplay(speed) {
    const speedValue = document.getElementById('speed-value');
    const speedStatus = document.getElementById('speed-status');
    
    if (speedValue) speedValue.textContent = Math.round(speed);
    if (speedStatus) {
        if (speed === 0) speedStatus.textContent = 'Stationary';
        else if (speed < 50) speedStatus.textContent = 'City Driving';
        else if (speed < 100) speedStatus.textContent = 'Highway';
        else speedStatus.textContent = 'High Speed';
    }
}

// Update coolant temperature
function updateCoolantTemp(temp, interpretation) {
    const coolantValue = document.getElementById('coolant-value');
    const coolantStatus = document.getElementById('coolant-status');
    const coolantFill = document.getElementById('coolant-fill');
    
    if (coolantValue) coolantValue.textContent = Math.round(temp);
    if (coolantStatus) coolantStatus.textContent = interpretation || 'Normal';
    
    if (coolantFill) {
        // Temperature range: 0°C to 120°C
        const percentage = Math.max(0, Math.min(100, ((temp - 0) / 120) * 100));
        coolantFill.style.height = percentage + '%';
    }
}

// Update engine load
function updateEngineLoad(load, interpretation) {
    const loadValue = document.getElementById('load-value');
    const loadStatus = document.getElementById('load-status');
    const loadProgress = document.getElementById('load-progress');
    
    if (loadValue) loadValue.textContent = Math.round(load);
    if (loadStatus) loadStatus.textContent = interpretation || 'Normal';
    if (loadProgress) loadProgress.style.width = load + '%';
}

// Update throttle position
function updateThrottlePosition(throttle) {
    const throttleValue = document.getElementById('throttle-value');
    const throttleFill = document.getElementById('throttle-fill');
    
    if (throttleValue) throttleValue.textContent = Math.round(throttle);
    if (throttleFill) throttleFill.style.width = throttle + '%';
}

// Update turbo gauges
function updateTurboGauges(turboData) {
    if (!turboData) return;

    // Update Turbo 1
    if (turbo1Gauge && turboData.turbo1_psi !== null) {
        updateTurboGauge(turbo1Gauge, turboData.turbo1_psi, '1');
        updateTurboDisplay(turboData.turbo1_psi, turboData.turbo1_status, '1');
    }

    // Update Turbo 2
    if (turbo2Gauge && turboData.turbo2_psi !== null) {
        updateTurboGauge(turbo2Gauge, turboData.turbo2_psi, '2');
        updateTurboDisplay(turboData.turbo2_psi, turboData.turbo2_status, '2');
    }
}

// Update individual turbo gauge
function updateTurboGauge(gauge, psi, turboNumber) {
    if (!gauge) return;

    // PSI range: -14.7 to +15.0 (total range of ~30 PSI)
    // Convert PSI to percentage (0-100%)
    const minPsi = -14.7;
    const maxPsi = 15.0;
    const totalRange = maxPsi - minPsi;
    const normalizedPsi = ((psi - minPsi) / totalRange) * 100;
    const percentage = Math.max(0, Math.min(100, normalizedPsi));

    gauge.data.datasets[0].data = [percentage, 100 - percentage];
    
    // Update gauge color based on PSI value
    let color = bmwColors.green; // Default atmospheric
    
    if (psi < -10) color = bmwColors.blue;      // High vacuum
    else if (psi < -5) color = bmwColors.blueLight; // Moderate vacuum
    else if (psi < 0) color = bmwColors.green;   // Light vacuum
    else if (psi < 0.5) color = bmwColors.green; // Atmospheric
    else if (psi < 5) color = bmwColors.yellow;  // Light boost
    else if (psi < 10) color = bmwColors.orange; // Moderate boost
    else color = bmwColors.red;                  // High boost

    gauge.data.datasets[0].backgroundColor[0] = color;
    gauge.update('none');
}

// Update turbo display values
function updateTurboDisplay(psi, status, turboNumber) {
    const psiElement = document.getElementById(`turbo${turboNumber}-psi`);
    const statusElement = document.getElementById(`turbo${turboNumber}-status`);
    
    if (psiElement) {
        psiElement.textContent = psi !== null ? psi.toFixed(1) : '--';
    }
    
    if (statusElement) {
        statusElement.textContent = status || 'No Data';
        
        // Update status color
        statusElement.className = 'turbo-status';
        if (status) {
            if (status.includes('High Boost')) statusElement.classList.add('text-danger');
            else if (status.includes('Moderate Boost')) statusElement.classList.add('text-warning');
            else if (status.includes('Light Boost')) statusElement.classList.add('text-success');
            else if (status.includes('Vacuum')) statusElement.classList.add('text-info');
            else statusElement.classList.add('text-muted');
        }
    }
}

// Update additional parameters
function updateAdditionalParameters(data) {
    // Fuel Pressure
    const fuelPressureData = data.FUEL_PRESSURE;
    if (fuelPressureData && fuelPressureData.value !== null) {
        const fuelPressureValue = document.getElementById('fuel-pressure-value');
        if (fuelPressureValue) {
            fuelPressureValue.textContent = Math.round(fuelPressureData.value);
        }
    }

    // Intake Temperature
    const intakeTempData = data.INTAKE_TEMP;
    if (intakeTempData && intakeTempData.value !== null) {
        const intakeTempValue = document.getElementById('intake-temp-value');
        if (intakeTempValue) {
            intakeTempValue.textContent = Math.round(intakeTempData.value);
        }
    }

    // MAF Flow
    const mafData = data.MAF;
    if (mafData && mafData.value !== null) {
        const mafValue = document.getElementById('maf-value');
        if (mafValue) {
            mafValue.textContent = mafData.value.toFixed(2);
        }
    }
}

// Animate gauge value change
function animateGaugeValue(elementId, targetValue, duration = 1000) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const startValue = parseFloat(element.textContent) || 0;
    const difference = targetValue - startValue;
    const startTime = performance.now();

    function updateValue(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function (ease-out-cubic)
        const easedProgress = 1 - Math.pow(1 - progress, 3);
        
        const currentValue = startValue + (difference * easedProgress);
        
        if (element.id.includes('psi')) {
            element.textContent = currentValue.toFixed(1);
        } else {
            element.textContent = Math.round(currentValue);
        }

        if (progress < 1) {
            requestAnimationFrame(updateValue);
        }
    }

    requestAnimationFrame(updateValue);
}

// Create performance gauge (for future use)
function createPerformanceGauge(ctx, config = {}) {
    const defaultConfig = {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [0, 100],
                backgroundColor: [bmwColors.blue, 'rgba(255, 255, 255, 0.1)'],
                borderColor: [bmwColors.blue, 'rgba(255, 255, 255, 0.2)'],
                borderWidth: 2,
                cutout: '70%',
                circumference: 180,
                rotation: 270
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            },
            animation: {
                animateRotate: true,
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    };

    // Merge with custom config
    const mergedConfig = { ...defaultConfig, ...config };
    
    return new Chart(ctx, mergedConfig);
}

// Destroy all gauges (for cleanup)
function destroyGauges() {
    if (rpmGauge) {
        rpmGauge.destroy();
        rpmGauge = null;
    }
    if (turbo1Gauge) {
        turbo1Gauge.destroy();
        turbo1Gauge = null;
    }
    if (turbo2Gauge) {
        turbo2Gauge.destroy();
        turbo2Gauge = null;
    }
}

// Resize gauges on window resize
window.addEventListener('resize', function() {
    setTimeout(() => {
        if (rpmGauge) rpmGauge.resize();
        if (turbo1Gauge) turbo1Gauge.resize();
        if (turbo2Gauge) turbo2Gauge.resize();
    }, 100);
});

// Performance optimization: throttle gauge updates
let lastGaugeUpdate = 0;
const GAUGE_UPDATE_THROTTLE = 100; // ms

function throttledGaugeUpdate(updateFunction, ...args) {
    const now = performance.now();
    if (now - lastGaugeUpdate > GAUGE_UPDATE_THROTTLE) {
        updateFunction(...args);
        lastGaugeUpdate = now;
    }
}