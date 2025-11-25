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

// ==================== Helper Functions ====================

// Make socket available globally if needed
window.dashboardSocket = socket;

console.log('🚀 Socket client initialized');
