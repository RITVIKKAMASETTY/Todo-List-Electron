/**
 * Chart.js Configuration and Real-Time Update Logic
 * 
 * Creates and manages all dashboard charts:
 *   - Oxygen concentration (time series)
 *   - Temperature (time series)
 *   - Health score history
 *   - Voltage & Current
 *   - Drift tracking
 *   - Pressure & Flow
 */

// ── Chart.js Defaults ─────────────────────────────────────────────
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.05)';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 11;
Chart.defaults.plugins.legend.display = false;
Chart.defaults.animation.duration = 500;

// ── Color Palette ─────────────────────────────────────────────────
const COLORS = {
    blue: { line: '#3b82f6', fill: 'rgba(59, 130, 246, 0.1)' },
    cyan: { line: '#06b6d4', fill: 'rgba(6, 182, 212, 0.1)' },
    emerald: { line: '#10b981', fill: 'rgba(16, 185, 129, 0.1)' },
    amber: { line: '#f59e0b', fill: 'rgba(245, 158, 11, 0.1)' },
    rose: { line: '#f43f5e', fill: 'rgba(244, 63, 94, 0.1)' },
    purple: { line: '#8b5cf6', fill: 'rgba(139, 92, 246, 0.1)' },
    indigo: { line: '#6366f1', fill: 'rgba(99, 102, 241, 0.1)' },
};

const MAX_DATA_POINTS = 60;

// ── Chart Store ───────────────────────────────────────────────────
const charts = {};

// ── Utility: Create Gradient Fill ─────────────────────────────────
function createGradient(ctx, colorTop, colorBottom) {
    const gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
    gradient.addColorStop(0, colorTop);
    gradient.addColorStop(1, colorBottom);
    return gradient;
}

// ── Base Chart Options ────────────────────────────────────────────
function baseOptions(yLabel = '', yMin = null, yMax = null) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: 'index',
            intersect: false,
        },
        scales: {
            x: {
                display: true,
                grid: { display: false },
                ticks: {
                    maxTicksLimit: 6,
                    font: { size: 10 },
                    color: '#64748b'
                }
            },
            y: {
                display: true,
                min: yMin,
                max: yMax,
                grid: {
                    color: 'rgba(255, 255, 255, 0.03)',
                    drawBorder: false
                },
                ticks: {
                    font: { size: 10 },
                    color: '#64748b',
                    padding: 8
                },
                title: {
                    display: !!yLabel,
                    text: yLabel,
                    color: '#64748b',
                    font: { size: 10 }
                }
            }
        },
        plugins: {
            tooltip: {
                backgroundColor: 'rgba(17, 24, 39, 0.95)',
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 1,
                padding: 10,
                titleFont: { size: 11, weight: '600' },
                bodyFont: { family: "'JetBrains Mono', monospace", size: 11 },
                cornerRadius: 8
            }
        },
        elements: {
            point: { radius: 0, hoverRadius: 4 },
            line: { tension: 0.3, borderWidth: 2 }
        }
    };
}

// ── Create Time Series Dataset ────────────────────────────────────
function createDataset(label, color, data = []) {
    return {
        label: label,
        data: data,
        borderColor: color.line,
        backgroundColor: color.fill,
        fill: true,
        pointRadius: 0,
        pointHoverRadius: 4,
        pointHoverBackgroundColor: color.line,
    };
}

// ── Initialize All Charts ─────────────────────────────────────────
function initCharts() {
    // Oxygen Chart
    const oxygenCtx = document.getElementById('oxygenChart');
    if (oxygenCtx) {
        charts.oxygen = new Chart(oxygenCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [createDataset('Oxygen', COLORS.cyan)]
            },
            options: baseOptions('O₂ %', 85, 100)
        });
    }

    // Temperature Chart
    const tempCtx = document.getElementById('temperatureChart');
    if (tempCtx) {
        charts.temperature = new Chart(tempCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [createDataset('Temperature', COLORS.amber)]
            },
            options: baseOptions('°C', 650, 750)
        });
    }

    // Health Chart
    const healthCtx = document.getElementById('healthChart');
    if (healthCtx) {
        charts.health = new Chart(healthCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [createDataset('Health', COLORS.emerald)]
            },
            options: baseOptions('Score', 0, 100)
        });
    }

    // Voltage & Current Chart
    const voltageCtx = document.getElementById('voltageChart');
    if (voltageCtx) {
        charts.voltage = new Chart(voltageCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    createDataset('Voltage', COLORS.blue),
                    createDataset('Current', COLORS.purple)
                ]
            },
            options: {
                ...baseOptions('V / A'),
                plugins: {
                    ...baseOptions().plugins,
                    legend: { display: true, position: 'top', labels: { boxWidth: 12, padding: 15, font: { size: 10 } } }
                }
            }
        });
    }

    // Drift Chart
    const driftCtx = document.getElementById('driftChart');
    if (driftCtx) {
        charts.drift = new Chart(driftCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [createDataset('Drift', COLORS.rose)]
            },
            options: baseOptions('Drift %')
        });
    }

    // Pressure & Flow Chart
    const pressureCtx = document.getElementById('pressureChart');
    if (pressureCtx) {
        charts.pressure = new Chart(pressureCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    createDataset('Pressure', COLORS.indigo),
                    createDataset('Flow', COLORS.emerald)
                ]
            },
            options: {
                ...baseOptions(),
                plugins: {
                    ...baseOptions().plugins,
                    legend: { display: true, position: 'top', labels: { boxWidth: 12, padding: 15, font: { size: 10 } } }
                }
            }
        });
    }
}

// ── Update Chart Data ─────────────────────────────────────────────
function addChartData(chart, label, ...values) {
    if (!chart) return;

    chart.data.labels.push(label);
    values.forEach((val, i) => {
        if (chart.data.datasets[i]) {
            chart.data.datasets[i].data.push(val);
        }
    });

    // Keep limited data points for performance
    if (chart.data.labels.length > MAX_DATA_POINTS) {
        chart.data.labels.shift();
        chart.data.datasets.forEach(ds => ds.data.shift());
    }

    chart.update('none'); // 'none' disables animation for perf
}

// ── Format Timestamp for Chart Label ──────────────────────────────
function formatTime(timestamp) {
    if (!timestamp) return '';
    const d = new Date(timestamp);
    return d.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// ── Export ─────────────────────────────────────────────────────────
window.DashboardCharts = {
    init: initCharts,
    charts: charts,
    addData: addChartData,
    formatTime: formatTime,
    COLORS: COLORS
};
