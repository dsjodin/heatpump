/**
 * WebSocket Client for Heat Pump Dashboard
 * Handles all real-time communication with Flask backend
 */

// Global state
let currentTimeRange = '24h';
let connected = false;

// Connect to WebSocket server
console.log('Initializing Socket.IO client...');
const socket = io(window.location.origin, {
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: 10,
    timeout: 10000
});

// ==================== Connection Event Handlers ====================

socket.on('connect', () => {
    console.log('✅ WebSocket connected');
    connected = true;
    updateConnectionStatus(true);

    // Load initial data via HTTP (faster for bulk data)
    loadInitialData(currentTimeRange);
});

socket.on('disconnect', () => {
    console.log('❌ WebSocket disconnected');
    connected = false;
    updateConnectionStatus(false);
});

socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
    updateConnectionStatus(false);
});

socket.on('connection_status', (data) => {
    console.log('📡', data.message);
});

// ==================== Data Update Handlers ====================

socket.on('graph_update', (data) => {
    console.log('📊 Received graph update');

    // Update all charts with new data
    if (window.updateAllCharts) {
        window.updateAllCharts(data);
    }

    // Update KPI cards
    if (window.updateKPIs) {
        window.updateKPIs(data);
    }

    // Update alarm status
    if (data.status) {
        updateAlarmStatus(data.status);
    }

    // Update event log
    if (data.events) {
        updateEventLog(data.events);
    }

    // Update last update time
    updateLastUpdateTime();
});

socket.on('error', (data) => {
    console.error('❌ Server error:', data.message);
    showError(data.message);
});

// ==================== HTTP Data Loading ====================

async function loadInitialData(timeRange) {
    try {
        console.log(`📥 Loading initial data for range: ${timeRange}`);

        const response = await fetch(`/api/initial-data?range=${timeRange}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('✅ Initial data loaded', data);

        // Initialize charts with data
        if (window.initializeCharts) {
            window.initializeCharts(data);
        }

        // Update KPIs
        if (window.updateKPIs) {
            window.updateKPIs(data);
        }

        // Update alarm status
        if (data.status) {
            updateAlarmStatus(data.status);
        }

        // Update event log
        if (data.events) {
            updateEventLog(data.events);
        }

        updateLastUpdateTime();

    } catch (error) {
        console.error('❌ Failed to load initial data:', error);
        showError('Failed to load dashboard data. Please refresh the page.');
    }
}

// ==================== User Interface Updates ====================

function updateConnectionStatus(isConnected) {
    const badge = document.getElementById('connection-status');
    if (isConnected) {
        badge.className = 'badge connection-badge connected';
        badge.textContent = 'Ansluten';
    } else {
        badge.className = 'badge connection-badge disconnected';
        badge.textContent = 'Frånkopplad';
    }
}

function updateLastUpdateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('sv-SE');
    document.getElementById('last-update').textContent = `Uppdaterad: ${timeString}`;
}

function showError(message) {
    // Simple error display (could be enhanced with toast notifications)
    console.error('Error:', message);
    // Could add a toast notification here
}

// ==================== User Interaction Handlers ====================

// Time range change
document.addEventListener('DOMContentLoaded', () => {
    const timeRangeSelect = document.getElementById('time-range');
    if (timeRangeSelect) {
        timeRangeSelect.addEventListener('change', (event) => {
            currentTimeRange = event.target.value;
            console.log(`🔄 Time range changed to: ${currentTimeRange}`);

            if (connected) {
                // Request new data via WebSocket
                socket.emit('change_time_range', { range: currentTimeRange });
            } else {
                // Fallback to HTTP if not connected
                loadInitialData(currentTimeRange);
            }
        });
    }

    // Manual refresh button
    const refreshButton = document.getElementById('btn-refresh');
    if (refreshButton) {
        refreshButton.addEventListener('click', () => {
            console.log('🔄 Manual refresh requested');

            if (connected) {
                socket.emit('request_update', { range: currentTimeRange });
            } else {
                loadInitialData(currentTimeRange);
            }
        });
    }
});

// ==================== Status Update Functions ====================

function updateAlarmStatus(status) {
    const alarmCard = document.getElementById('alarm-card');
    const alarmContent = document.getElementById('alarm-content');

    if (!status || !status.alarm) {
        return;
    }

    const alarm = status.alarm;

    if (alarm.is_active) {
        // ALARM ACTIVE
        alarmCard.className = 'chart-card alarm-active';

        let alarmTime = 'Okänd';
        let duration = '';

        if (alarm.time) {
            try {
                const alarmDate = new Date(alarm.time);
                alarmTime = alarmDate.toLocaleString('sv-SE');

                const now = new Date();
                const durationMs = now - alarmDate;
                const hours = Math.floor(durationMs / (1000 * 60 * 60));
                const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));

                if (hours > 0) {
                    duration = `${hours}h ${minutes}min`;
                } else {
                    duration = `${minutes}min`;
                }
            } catch (e) {
                console.error('Error parsing alarm time:', e);
            }
        }

        alarmContent.innerHTML = `
            <div class="text-center alarm-icon">
                <i class="fas fa-exclamation-circle"></i>
            </div>
            <h4 class="text-danger text-center mb-3">⚠️ LARM AKTIVT!</h4>
            <div class="alarm-description mb-2">
                <strong>Larmkod ${alarm.code || 'N/A'}: </strong>
                <span>${alarm.description || 'Okänd beskrivning'}</span>
            </div>
            <hr>
            <div class="alarm-details">
                <div class="mb-2">
                    <i class="fas fa-clock me-2"></i>
                    <strong>Aktiverad: </strong>
                    <span>${alarmTime}</span>
                </div>
                ${duration ? `
                <div>
                    <i class="fas fa-hourglass-half me-2"></i>
                    <strong>Varaktighet: </strong>
                    <span>${duration}</span>
                </div>
                ` : ''}
            </div>
            <hr>
            <div class="mt-3">
                <i class="fas fa-info-circle me-2"></i>
                <span class="text-muted">Kontrollera värmepumpen och återställ larmet efter åtgärd.</span>
            </div>
        `;
    } else {
        // NO ALARM
        alarmCard.className = 'chart-card alarm-ok';
        alarmContent.innerHTML = `
            <div class="text-center alarm-icon">
                <i class="fas fa-check-circle"></i>
            </div>
            <h5 class="text-success text-center mb-2">✅ Inget aktivt larm</h5>
            <p class="text-muted text-center mb-0">Systemet fungerar normalt</p>
        `;
    }
}

function updateEventLog(events) {
    const eventLog = document.getElementById('event-log');

    if (!events || events.length === 0) {
        eventLog.innerHTML = '<div class="text-center text-muted p-3">Inga händelser att visa</div>';
        return;
    }

    let html = '';
    events.forEach(event => {
        const eventType = event.type || 'info';
        let eventTime = 'Okänd tid';

        try {
            if (event.time) {
                const date = new Date(event.time);
                eventTime = date.toLocaleString('sv-SE', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }
        } catch (e) {
            console.error('Error parsing event time:', e);
        }

        html += `
            <div class="event-item">
                <div class="d-flex justify-content-between align-items-start">
                    <span class="event-time">${eventTime}</span>
                    <span class="event-type ${eventType}">${eventType}</span>
                </div>
                <div class="event-description">${event.description || 'No description'}</div>
                ${event.value ? `<div class="event-value">Värde: ${event.value}</div>` : ''}
            </div>
        `;
    });

    eventLog.innerHTML = html;
}

// ==================== Helper Functions ====================

// Make socket available globally if needed
window.dashboardSocket = socket;

console.log('🚀 Socket client initialized');
