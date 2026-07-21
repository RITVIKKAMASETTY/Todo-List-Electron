/**
 * Dashboard Controller — Real-Time Data Fetching and UI Updates
 * 
 * Polls the FastAPI backend every second and updates:
 *   - Metric cards (O2, temp, pressure, voltage)
 *   - Health ring gauge
 *   - Time-series charts
 *   - RUL countdown
 *   - Fault probability bars
 *   - Alert feed
 *   - Flight phase indicator
 *   - Simulator status
 */

// ── State ─────────────────────────────────────────────────────────
let updateInterval = null;
let isConnected = false;
let tickCount = 0;

// ── API Calls ─────────────────────────────────────────────────────
async function fetchJSON(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (err) {
        console.error(`Fetch error: ${url}`, err);
        return null;
    }
}

async function getSummary() {
    return fetchJSON('/api/dashboard/summary');
}

async function getTwinState() {
    return fetchJSON('/api/dashboard/twin');
}

async function getRecentAlerts() {
    return fetchJSON('/api/alerts/recent?limit=10');
}

// ── Update Metric Cards ──────────────────────────────────────────
function updateMetric(id, value, unit = '') {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = value !== null && value !== undefined
            ? `${value}${unit}` : '--';
    }
}

function updateMetricClass(id, value, thresholds = {}) {
    const el = document.getElementById(id);
    if (!el) return;

    el.classList.remove('health', 'warning', 'danger');
    if (thresholds.danger && value < thresholds.danger) {
        el.classList.add('danger');
    } else if (thresholds.warning && value < thresholds.warning) {
        el.classList.add('warning');
    } else {
        el.classList.add('health');
    }
}

// ── Update Health Ring ───────────────────────────────────────────
function updateHealthRing(score) {
    const circle = document.getElementById('healthRingProgress');
    const valueEl = document.getElementById('healthRingValue');
    const labelEl = document.getElementById('healthRingLabel');

    if (!circle || !valueEl) return;

    const circumference = 2 * Math.PI * 65; // r=65
    const offset = circumference - (score / 100) * circumference;

    circle.style.strokeDasharray = circumference;
    circle.style.strokeDashoffset = offset;

    // Color based on health
    if (score >= 85) {
        circle.style.stroke = '#10b981';
        valueEl.style.color = '#10b981';
    } else if (score >= 70) {
        circle.style.stroke = '#06b6d4';
        valueEl.style.color = '#06b6d4';
    } else if (score >= 50) {
        circle.style.stroke = '#f59e0b';
        valueEl.style.color = '#f59e0b';
    } else {
        circle.style.stroke = '#f43f5e';
        valueEl.style.color = '#f43f5e';
    }

    valueEl.textContent = score.toFixed(1);

    if (labelEl) {
        if (score >= 95) labelEl.textContent = 'EXCELLENT';
        else if (score >= 85) labelEl.textContent = 'GOOD';
        else if (score >= 70) labelEl.textContent = 'FAIR';
        else if (score >= 50) labelEl.textContent = 'POOR';
        else labelEl.textContent = 'CRITICAL';
    }
}

// ── Update RUL Display ───────────────────────────────────────────
function updateRUL(hours) {
    const valueEl = document.getElementById('rulValue');
    const barEl = document.getElementById('rulBarFill');

    if (valueEl) {
        valueEl.textContent = hours !== null ? Math.round(hours) : '--';
    }

    if (barEl) {
        const maxHours = 5000;
        const percent = Math.min((hours || 0) / maxHours * 100, 100);
        barEl.style.width = `${percent}%`;

        barEl.classList.remove('warning', 'danger');
        if (hours < 100) {
            barEl.style.background = 'linear-gradient(90deg, #f43f5e, #e11d48)';
        } else if (hours < 500) {
            barEl.style.background = 'linear-gradient(90deg, #f59e0b, #f43f5e)';
        } else {
            barEl.style.background = 'linear-gradient(90deg, #10b981, #06b6d4)';
        }
    }
}

// ── Update Fault Bars ────────────────────────────────────────────
function updateFaultBar(id, probability) {
    const barEl = document.getElementById(id);
    const valEl = document.getElementById(id + 'Val');

    if (barEl) {
        const percent = Math.min(probability * 100, 100);
        barEl.style.width = `${percent}%`;

        barEl.classList.remove('warning', 'danger');
        if (probability > 0.5) {
            barEl.classList.add('danger');
        } else if (probability > 0.2) {
            barEl.classList.add('warning');
        }
    }

    if (valEl) {
        valEl.textContent = `${(probability * 100).toFixed(1)}%`;
    }
}

// ── Update Alert Feed ────────────────────────────────────────────
function updateAlerts(alerts) {
    const container = document.getElementById('alertFeed');
    if (!container || !alerts) return;

    if (alerts.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">✓</div>
                <div>No active alerts</div>
            </div>`;
        return;
    }

    container.innerHTML = alerts.map(alert => {
        const severity = alert.severity || 'info';
        const time = alert.timestamp
            ? new Date(alert.timestamp).toLocaleTimeString('en-US', { hour12: false })
            : '';

        return `
            <div class="alert-item ${severity}">
                <span class="alert-severity ${severity}">${severity.toUpperCase()}</span>
                <span class="alert-message">${alert.message || ''}</span>
                <span class="alert-time">${time}</span>
            </div>`;
    }).join('');
}

// ── Update Flight Phase ──────────────────────────────────────────
function updateFlightPhase(phase) {
    const phases = ['ground', 'climb', 'cruise', 'descent'];
    phases.forEach(p => {
        const el = document.getElementById(`phase-${p}`);
        if (el) {
            el.classList.toggle('active', p === phase);
        }
    });
}

// ── Update Connection Status ─────────────────────────────────────
function updateConnectionStatus(connected) {
    const dot = document.getElementById('statusDot');
    const text = document.getElementById('statusText');

    if (dot) {
        dot.className = `status-dot ${connected ? '' : 'critical'}`;
    }
    if (text) {
        text.textContent = connected ? 'Live' : 'Disconnected';
    }
    isConnected = connected;
}

// ── Main Update Loop ─────────────────────────────────────────────
async function updateDashboard() {
    tickCount++;

    // Fetch summary data
    const summary = await getSummary();
    if (!summary || summary.status !== 'ok') {
        updateConnectionStatus(false);
        return;
    }

    updateConnectionStatus(true);

    const sensor = summary.sensor;
    const health = summary.health;
    const prediction = summary.prediction;
    const alerts = summary.recent_alerts;
    const stats = summary.statistics;

    // ── Update Sensor Metrics ──────────────────────────────────
    if (sensor) {
        updateMetric('oxygenValue', sensor.oxygen?.toFixed(1), '%');
        updateMetric('tempValue', sensor.temperature?.toFixed(1), '°C');
        updateMetric('pressureValue', sensor.pressure?.toFixed(1), ' psi');
        updateMetric('voltageValue', sensor.voltage?.toFixed(3), ' V');
        updateMetric('currentValue', sensor.current?.toFixed(3), ' A');
        updateMetric('flowValue', sensor.flow?.toFixed(1), ' L/min');
        updateMetric('humidityValue', sensor.humidity?.toFixed(1), '%');
        updateMetric('altitudeValue', Math.round(sensor.altitude || 0), ' ft');
        updateMetric('heaterTempValue', sensor.heater_temp?.toFixed(0), '°C');
        updateMetric('flightHoursValue', sensor.flight_hours?.toFixed(1), ' hrs');
        updateMetric('thermalCyclesValue', sensor.thermal_cycles, '');
        updateMetric('vibrationValue', sensor.vibration?.toFixed(2), ' g');

        // Update charts
        const timeLabel = DashboardCharts.formatTime(sensor.timestamp);
        DashboardCharts.addData(DashboardCharts.charts.oxygen, timeLabel, sensor.oxygen);
        DashboardCharts.addData(DashboardCharts.charts.temperature, timeLabel, sensor.heater_temp || sensor.temperature);
        DashboardCharts.addData(DashboardCharts.charts.voltage, timeLabel, sensor.voltage, sensor.current);
        DashboardCharts.addData(DashboardCharts.charts.pressure, timeLabel, sensor.pressure, sensor.flow);
    }

    // ── Update Health ──────────────────────────────────────────
    if (health) {
        updateHealthRing(health.health_score || 100);
        updateMetric('driftValue', health.drift?.toFixed(3), '%');
        updateMetric('noiseValue', health.noise?.toFixed(4), '');
        updateMetric('agingValue', (health.aging_factor * 100)?.toFixed(1), '%');
        updateMetric('sensitivityValue', health.sensitivity?.toFixed(3), '');
        updateMetric('faultProbValue', (health.fault_probability * 100)?.toFixed(1), '%');

        // Health chart
        const timeLabel = DashboardCharts.formatTime(health.timestamp);
        DashboardCharts.addData(DashboardCharts.charts.health, timeLabel, health.health_score);

        // Drift chart
        DashboardCharts.addData(DashboardCharts.charts.drift, timeLabel, health.drift);

        // Fault bars
        updateFaultBar('faultOverall', health.fault_probability || 0);
    }

    // ── Update Prediction / RUL ────────────────────────────────
    if (prediction) {
        updateRUL(prediction.remaining_life);
        updateMetric('predOxygenValue', prediction.predicted_oxygen?.toFixed(1), '%');
        updateMetric('predTempValue', prediction.predicted_temperature?.toFixed(0), '°C');
        updateMetric('predHealthValue', prediction.predicted_health?.toFixed(1), '');
        updateMetric('confidenceValue', (prediction.confidence * 100)?.toFixed(0), '%');
    }

    // ── Update Alerts ──────────────────────────────────────────
    updateAlerts(alerts);

    // ── Update Simulator Status ────────────────────────────────
    if (stats && stats.simulator_status) {
        const sim = stats.simulator_status;
        updateFlightPhase(sim.current_phase);
        updateMetric('simTickValue', stats.pipeline_summary?.tick_count || 0);
        updateMetric('totalReadingsValue', stats.total_readings || 0);
    }
}

// ── Initialize Dashboard ─────────────────────────────────────────
function initDashboard() {
    DashboardCharts.init();
    updateDashboard(); // Initial fetch
    updateInterval = setInterval(updateDashboard, 1000); // Poll every 1s
}

// ── Cleanup ──────────────────────────────────────────────────────
function stopDashboard() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
}

// ── Fault Injection UI ───────────────────────────────────────────
async function injectFault(type, severity = 0.5) {
    const result = await fetchJSON(
        `/api/sensor/fault?fault_type=${type}&severity=${severity}`
    );
    if (result) {
        console.log('Fault injected:', result);
    }
}

async function clearFaults() {
    const result = await fetchJSON('/api/sensor/clear-faults');
    if (result) {
        console.log('Faults cleared:', result);
    }
}

// ── Start on DOM Ready ───────────────────────────────────────────
document.addEventListener('DOMContentLoaded', initDashboard);
window.addEventListener('beforeunload', stopDashboard);

// Export for console access
window.Dashboard = {
    update: updateDashboard,
    stop: stopDashboard,
    injectFault: injectFault,
    clearFaults: clearFaults
};
