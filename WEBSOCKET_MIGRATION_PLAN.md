# 🚀 WebSocket Migration Plan: Dash → Flask + ECharts + Socket.IO

## Executive Summary

**Goal:** Migrate from Dash/Plotly to Flask + ECharts + WebSockets for:
- ✅ True bi-directional real-time communication
- ✅ Better performance (smaller bundle size)
- ✅ More control and flexibility
- ✅ Modern architecture for future features

**Timeline:** 3-4 weeks (60-80 hours)

**Risk Level:** Medium (architectural change, but data layer stays intact)

---

## 📊 Current Architecture Analysis

### What You Have Now:

```
┌─────────────────────────────────────────────────────────────┐
│                     DASH APPLICATION                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  app.py (main)                                              │
│    ├─→ Dash server init                                     │
│    ├─→ Load provider (Thermia/IVT/NIBE)                    │
│    └─→ Register callbacks                                   │
│                                                             │
│  layout.py + layout_components.py                           │
│    ├─→ dcc.Graph components (Plotly)                        │
│    ├─→ dcc.Interval (30s auto-refresh)                      │
│    ├─→ dcc.Dropdown (time range selector)                   │
│    └─→ dbc Bootstrap components                             │
│                                                             │
│  callbacks_graphs.py (7 graph callbacks)                    │
│    ├─→ update_sankey_diagram()                              │
│    ├─→ update_cop_graph()                                   │
│    ├─→ update_runtime_pie()                                 │
│    ├─→ update_temperature_graph()                           │
│    ├─→ update_performance_graph()                           │
│    ├─→ update_power_graph()                                 │
│    └─→ update_valve_status_graph()                          │
│                                                             │
│  callbacks_kpi.py (KPI card callbacks)                      │
│  callbacks_status.py (status/alarm callbacks)               │
│                                                             │
│  data_query.py ⭐ CAN BE REUSED!                            │
│    └─→ HeatPumpDataQuery class                              │
│        ├─→ query_metrics()                                  │
│        ├─→ calculate_cop()                                  │
│        ├─→ calculate_runtime_stats()                        │
│        └─→ InfluxDB client                                  │
│                                                             │
│  config_colors.py ⭐ CAN BE REUSED!                         │
│  providers/ ⭐ CAN BE REUSED!                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  InfluxDB    │
                    │  Time Series │
                    └──────────────┘
```

---

## 🎯 Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│               FLASK + SOCKET.IO APPLICATION                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  app.py (Flask)                                             │
│    ├─→ Flask server init                                    │
│    ├─→ Socket.IO setup                                      │
│    ├─→ Load provider (Thermia/IVT/NIBE) ⭐ REUSE           │
│    └─→ Background tasks (data push every 30s)              │
│                                                             │
│  routes.py                                                  │
│    ├─→ @app.route('/') → serve index.html                  │
│    ├─→ @app.route('/api/initial-data') → first load        │
│    └─→ @app.route('/api/config') → provider config         │
│                                                             │
│  websocket_handlers.py                                      │
│    ├─→ @socketio.on('connect')                             │
│    ├─→ @socketio.on('change_time_range')                   │
│    ├─→ @socketio.on('request_graph_update')                │
│    └─→ @socketio.on('disconnect')                          │
│                                                             │
│  graph_builder.py                                           │
│    ├─→ build_sankey_option()                               │
│    ├─→ build_cop_option()                                  │
│    ├─→ build_runtime_pie_option()                          │
│    ├─→ build_temperature_option()                          │
│    ├─→ build_performance_option()                          │
│    ├─→ build_power_option()                                │
│    └─→ build_valve_status_option()                         │
│                                                             │
│  data_query.py ⭐ REUSE AS-IS                               │
│  config_colors.py ⭐ REUSE (convert to dict)                │
│  providers/ ⭐ REUSE AS-IS                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
         WebSocket     WebSocket   WebSocket
         Connection    Connection  Connection
                │           │           │
┌───────────────┼───────────┼───────────┼───────────────┐
│               │ BROWSER (Client-Side) │               │
├───────────────┴───────────────────────┴───────────────┤
│                                                       │
│  index.html                                           │
│    ├─→ 7 × <div id="xxx-chart">                      │
│    ├─→ Time range dropdown                           │
│    └─→ KPI cards                                      │
│                                                       │
│  static/js/socket-client.js                           │
│    ├─→ io.connect()                                   │
│    ├─→ Listen: 'graph_update'                         │
│    ├─→ Emit: 'change_time_range'                     │
│    └─→ Handle reconnection                            │
│                                                       │
│  static/js/charts.js                                  │
│    ├─→ Initialize 7 ECharts instances                 │
│    ├─→ Update chart options on data receive           │
│    └─→ Responsive resize handlers                     │
│                                                       │
│  static/css/dashboard.css ⭐ PORT FROM DASH           │
│                                                       │
└───────────────────────────────────────────────────────┘
```

---

## 📦 What Can Be REUSED (70% of code!)

### ✅ Keep As-Is:
1. **`data_query.py`** (entire file!)
   - All InfluxDB queries
   - All calculations (COP, runtime stats, etc.)
   - Provider integration

2. **`providers/` directory** (entire folder!)
   - Thermia provider
   - IVT provider
   - NIBE provider
   - All alarm codes and configs

3. **`config_colors.py`** (color palette)
   - Just convert to dict format for JSON serialization

4. **Business logic**
   - All data processing stays the same
   - All calculations stay the same

### 🔄 Needs Translation:
1. **Plotly graphs → ECharts options**
   - Same data, different format

2. **Dash callbacks → Socket.IO handlers**
   - Same triggers, different mechanism

3. **Dash components → HTML + ECharts**
   - Same UI, different rendering

---

## 🗓️ Migration Phases

### **Phase 1: Setup & Infrastructure** (Week 1 - 8-12 hours)

#### Goals:
- [ ] Set up Flask + Socket.IO server
- [ ] Create basic WebSocket connection
- [ ] Test bi-directional communication
- [ ] Set up project structure

#### Tasks:

**1.1 Create new Flask app structure:**
```
heatpump/
├── dashboard_old/          # Rename current dashboard/
├── dashboard/              # New Flask app
│   ├── app.py             # Flask + Socket.IO server
│   ├── routes.py          # HTTP routes
│   ├── websocket_handlers.py  # Socket.IO events
│   ├── graph_builder.py   # ECharts option builders
│   ├── data_query.py      # ⭐ SYMLINK or COPY from old
│   ├── config_colors.py   # ⭐ SYMLINK or COPY from old
│   ├── templates/
│   │   └── index.html     # Main dashboard page
│   └── static/
│       ├── js/
│       │   ├── socket-client.js
│       │   └── charts.js
│       └── css/
│           └── dashboard.css
├── providers/             # ⭐ KEEP AS-IS
└── requirements.txt       # Update dependencies
```

**1.2 Install dependencies:**
```bash
pip install flask==3.0.0
pip install flask-socketio==5.3.5
pip install python-socketio==5.10.0
pip install eventlet==0.33.3
pip install flask-cors==4.0.0
# Keep existing:
# influxdb-client, pandas, PyYAML
```

**1.3 Create minimal Flask app:**
```python
# dashboard/app.py
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('ping')
def handle_ping():
    return 'pong'

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8050, debug=True)
```

**1.4 Create test client:**
```html
<!-- templates/index.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Heat Pump Dashboard - WebSocket</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
    <h1>WebSocket Test</h1>
    <div id="status">Connecting...</div>

    <script>
        const socket = io('http://localhost:8050');

        socket.on('connect', () => {
            document.getElementById('status').textContent = 'Connected!';
            socket.emit('ping');
        });

        socket.on('pong', (data) => {
            console.log('Received pong:', data);
        });
    </script>
</body>
</html>
```

**1.5 Test WebSocket connection:**
```bash
python dashboard/app.py
# Visit http://localhost:8050
# Verify "Connected!" appears
```

---

### **Phase 2: Data Layer Integration** (Week 1-2 - 8-12 hours)

#### Goals:
- [ ] Integrate HeatPumpDataQuery with Flask
- [ ] Create API endpoints for initial data load
- [ ] Set up background task for periodic updates
- [ ] Test data flow from InfluxDB to WebSocket

#### Tasks:

**2.1 Integrate data_query.py:**
```python
# dashboard/app.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_query import HeatPumpDataQuery
from providers import get_provider

# Initialize
provider = get_provider(os.getenv('HEATPUMP_BRAND', 'thermia'))
data_query = HeatPumpDataQuery()

print(f"✅ Loaded provider: {provider.get_display_name()}")
```

**2.2 Create initial data endpoint:**
```python
# dashboard/routes.py
from flask import jsonify, request

@app.route('/api/initial-data')
def get_initial_data():
    """Load all graph data for initial page load"""
    time_range = request.args.get('range', '24h')

    try:
        data = {
            'cop': get_cop_data(time_range),
            'temperature': get_temperature_data(time_range),
            'runtime': get_runtime_data(time_range),
            'sankey': get_sankey_data(time_range),
            'performance': get_performance_data(time_range),
            'power': get_power_data(time_range),
            'valve': get_valve_data(time_range),
            'config': {
                'brand': provider.get_brand_name(),
                'display_name': provider.get_display_name(),
                'colors': get_color_config()
            }
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_cop_data(time_range):
    """Extract COP data from data_query"""
    cop_df = data_query.calculate_cop(time_range)

    if cop_df.empty:
        return {'timestamps': [], 'values': [], 'avg': 0}

    return {
        'timestamps': cop_df['_time'].astype(str).tolist(),
        'values': cop_df['estimated_cop'].tolist(),
        'avg': float(cop_df['estimated_cop'].mean())
    }

# Similar functions for other graphs...
```

**2.3 Create background update task:**
```python
# dashboard/websocket_handlers.py
from flask_socketio import emit
import eventlet

def background_updates():
    """Background task to push updates every 30 seconds"""
    while True:
        eventlet.sleep(30)  # 30 second interval (matches current Dash)

        # Get current time range from connected clients
        # (stored in session or global dict)
        time_range = '24h'  # Default

        try:
            # Query all data
            update_data = {
                'cop': get_cop_data(time_range),
                'temperature': get_temperature_data(time_range),
                # ... other graphs
            }

            # Broadcast to all connected clients
            socketio.emit('graph_update', update_data, broadcast=True)
            print(f"✅ Pushed update at {datetime.now()}")

        except Exception as e:
            print(f"❌ Error in background update: {e}")

# Start background task when server starts
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    # Start background task (only once)
    if not hasattr(socketio, 'background_task_started'):
        socketio.background_task_started = True
        socketio.start_background_task(background_updates)
```

**2.4 Handle time range changes:**
```python
# dashboard/websocket_handlers.py
@socketio.on('change_time_range')
def handle_time_range_change(data):
    """React to user changing time range dropdown"""
    time_range = data.get('range', '24h')

    print(f"🔄 User changed time range to: {time_range}")

    # Immediately send updated data for this client
    update_data = {
        'cop': get_cop_data(time_range),
        'temperature': get_temperature_data(time_range),
        'runtime': get_runtime_data(time_range),
        # ... all other graphs
    }

    # Send to requesting client only
    emit('graph_update', update_data)
```

---

### **Phase 3: Frontend Foundation** (Week 2 - 12-16 hours)

#### Goals:
- [ ] Create HTML structure matching Dash layout
- [ ] Set up ECharts initialization
- [ ] Implement WebSocket client
- [ ] Port CSS styles from Dash

#### Tasks:

**3.1 Create main dashboard HTML:**
```html
<!-- templates/index.html -->
<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Värmepump Dashboard</title>

    <!-- Bootstrap CSS (same as Dash) -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <!-- Custom CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/dashboard.css') }}">

    <!-- ECharts -->
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>

    <!-- Socket.IO -->
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
    <!-- Header -->
    <nav class="navbar navbar-dark bg-primary">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">🔥 Thermia Värmepump Dashboard</span>
            <span class="badge bg-success" id="connection-status">Ansluten</span>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <!-- Controls Row -->
        <div class="row mb-3">
            <div class="col-md-3">
                <label for="time-range" class="form-label">Tidsperiod:</label>
                <select id="time-range" class="form-select">
                    <option value="1h">Senaste timme</option>
                    <option value="6h">Senaste 6 timmar</option>
                    <option value="24h" selected>Senaste 24 timmar</option>
                    <option value="7d">Senaste vecka</option>
                    <option value="30d">Senaste månad</option>
                </select>
            </div>
            <div class="col-md-9">
                <div class="alert alert-info mb-0" id="last-update">
                    Senast uppdaterad: Laddar...
                </div>
            </div>
        </div>

        <!-- KPI Cards Row -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h6 class="card-subtitle mb-2 text-muted">COP</h6>
                        <h3 class="card-title" id="kpi-cop">--</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h6 class="card-subtitle mb-2 text-muted">Kompressor</h6>
                        <h3 class="card-title" id="kpi-compressor">--</h3>
                    </div>
                </div>
            </div>
            <!-- More KPI cards... -->
        </div>

        <!-- Charts Row 1: Sankey + COP -->
        <div class="row mb-4">
            <div class="col-lg-6">
                <div class="card">
                    <div class="card-header">Energiflöde</div>
                    <div class="card-body">
                        <div id="sankey-chart" style="height: 400px;"></div>
                    </div>
                </div>
            </div>
            <div class="col-lg-6">
                <div class="card">
                    <div class="card-header">COP (Värmefaktor)</div>
                    <div class="card-body">
                        <div id="cop-chart" style="height: 400px;"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Row 2: Temperature + Runtime -->
        <div class="row mb-4">
            <div class="col-lg-8">
                <div class="card">
                    <div class="card-header">Temperaturer</div>
                    <div class="card-body">
                        <div id="temperature-chart" style="height: 400px;"></div>
                    </div>
                </div>
            </div>
            <div class="col-lg-4">
                <div class="card">
                    <div class="card-header">Drifttid</div>
                    <div class="card-body">
                        <div id="runtime-chart" style="height: 400px;"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Row 3: Performance -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">Systemprestanda</div>
                    <div class="card-body">
                        <div id="performance-chart" style="height: 600px;"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Row 4: Power -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">Effektförbrukning</div>
                    <div class="card-body">
                        <div id="power-chart" style="height: 600px;"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Row 5: Valve Status -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">Växelventilsstatus</div>
                    <div class="card-body">
                        <div id="valve-chart" style="height: 700px;"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- JavaScript -->
    <script src="{{ url_for('static', filename='js/charts.js') }}"></script>
    <script src="{{ url_for('static', filename='js/socket-client.js') }}"></script>
</body>
</html>
```

**3.2 Create WebSocket client:**
```javascript
// static/js/socket-client.js

// Connect to WebSocket server
const socket = io('http://localhost:8050', {
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: 10
});

let currentTimeRange = '24h';

// Connection status handling
socket.on('connect', () => {
    console.log('✅ WebSocket connected');
    updateConnectionStatus(true);

    // Load initial data
    loadInitialData(currentTimeRange);
});

socket.on('disconnect', () => {
    console.log('❌ WebSocket disconnected');
    updateConnectionStatus(false);
});

socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
    updateConnectionStatus(false);
});

// Listen for graph updates from server
socket.on('graph_update', (data) => {
    console.log('📊 Received graph update', data);
    updateAllCharts(data);
    updateLastUpdateTime();
});

// Load initial data via HTTP (faster than WebSocket for bulk data)
async function loadInitialData(timeRange) {
    try {
        const response = await fetch(`/api/initial-data?range=${timeRange}`);
        const data = await response.json();

        console.log('📥 Loaded initial data', data);

        // Initialize all charts with data
        initializeCharts(data);
        updateKPIs(data);
        updateLastUpdateTime();

    } catch (error) {
        console.error('Failed to load initial data:', error);
    }
}

// Handle time range changes
document.getElementById('time-range').addEventListener('change', (event) => {
    currentTimeRange = event.target.value;
    console.log(`🔄 Time range changed to: ${currentTimeRange}`);

    // Request new data via WebSocket
    socket.emit('change_time_range', { range: currentTimeRange });
});

// Update connection status indicator
function updateConnectionStatus(connected) {
    const badge = document.getElementById('connection-status');
    if (connected) {
        badge.className = 'badge bg-success';
        badge.textContent = 'Ansluten';
    } else {
        badge.className = 'badge bg-danger';
        badge.textContent = 'Frånkopplad';
    }
}

// Update last update timestamp
function updateLastUpdateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('sv-SE');
    document.getElementById('last-update').textContent = `Senast uppdaterad: ${timeString}`;
}

// Update KPI cards
function updateKPIs(data) {
    if (data.cop && data.cop.avg) {
        document.getElementById('kpi-cop').textContent = data.cop.avg.toFixed(2);
    }

    if (data.runtime) {
        document.getElementById('kpi-compressor').textContent =
            `${data.runtime.compressor_percent.toFixed(0)}%`;
    }

    // ... update other KPIs
}
```

**3.3 Port CSS from Dash:**
```css
/* static/css/dashboard.css */

/* Port styles from dashboard/assets/style.css */
body {
    background-color: #f8f9fa;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}

.card {
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 1rem;
}

.card-header {
    background-color: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
    font-weight: 600;
}

/* ECharts container styling (matches Plotly) */
[id$="-chart"] {
    border-radius: 8px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .card {
        margin-bottom: 1.5rem;
    }
}

/* Loading spinner */
.chart-loading {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
}

/* Connection status pulse animation */
.badge.bg-success {
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}
```

---

### **Phase 4: ECharts Integration** (Week 2-3 - 16-24 hours)

#### Goals:
- [ ] Migrate all 7 graphs from Plotly to ECharts
- [ ] Create reusable chart update functions
- [ ] Match styling and behavior of Plotly charts
- [ ] Test interactivity (hover, zoom, etc.)

#### Tasks:

**4.1 Create chart initialization:**
```javascript
// static/js/charts.js

// Store chart instances globally
const charts = {};

// Initialize all chart instances
function initializeCharts(data) {
    // Initialize each chart
    charts.cop = echarts.init(document.getElementById('cop-chart'));
    charts.temperature = echarts.init(document.getElementById('temperature-chart'));
    charts.runtime = echarts.init(document.getElementById('runtime-chart'));
    charts.sankey = echarts.init(document.getElementById('sankey-chart'));
    charts.performance = echarts.init(document.getElementById('performance-chart'));
    charts.power = echarts.init(document.getElementById('power-chart'));
    charts.valve = echarts.init(document.getElementById('valve-chart'));

    // Update with initial data
    updateAllCharts(data);

    // Make charts responsive
    window.addEventListener('resize', () => {
        Object.values(charts).forEach(chart => chart.resize());
    });
}

// Update all charts with new data
function updateAllCharts(data) {
    if (data.cop) updateCopChart(data.cop);
    if (data.temperature) updateTemperatureChart(data.temperature);
    if (data.runtime) updateRuntimeChart(data.runtime);
    if (data.sankey) updateSankeyChart(data.sankey);
    if (data.performance) updatePerformanceChart(data.performance);
    if (data.power) updatePowerChart(data.power);
    if (data.valve) updateValveChart(data.valve);
}

// Individual chart update functions
function updateCopChart(data) {
    const option = {
        grid: {
            left: 40,
            right: 40,
            top: 20,
            bottom: 40,
            backgroundColor: 'transparent'
        },
        xAxis: {
            type: 'time',
            name: 'Tid',
            nameLocation: 'middle',
            nameGap: 30,
            axisLine: { lineStyle: { color: '#999' } }
        },
        yAxis: {
            type: 'value',
            name: 'COP (Värmefaktor)',
            min: 0,
            max: 6,
            axisLine: { lineStyle: { color: '#999' } }
        },
        series: [{
            type: 'line',
            name: 'COP',
            data: data.timestamps.map((t, i) => [t, data.values[i]]),
            smooth: true,
            lineStyle: {
                color: '#4CAF50',
                width: 3
            },
            areaStyle: {
                color: 'rgba(76, 175, 80, 0.2)'
            },
            markLine: {
                silent: false,
                lineStyle: {
                    type: 'dashed',
                    color: '#ff9800'
                },
                data: [{
                    yAxis: data.avg,
                    label: {
                        position: 'end',
                        formatter: `Medel: ${data.avg.toFixed(2)}`
                    }
                }]
            }
        }],
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross',
                label: { backgroundColor: '#6a7985' }
            }
        },
        backgroundColor: 'transparent'
    };

    charts.cop.setOption(option, true);
}

function updateTemperatureChart(data) {
    // Multi-line chart similar to Plotly
    const series = [];

    // Define line order and colors (match Plotly)
    const metrics = [
        { key: 'hot_water_top', name: 'Varmvatten', color: '#ff9800' },
        { key: 'radiator_forward', name: 'Radiator Fram ↑', color: '#dc143c' },
        { key: 'radiator_return', name: 'Radiator Retur ↓', color: '#ffd700' },
        { key: 'indoor_temp', name: 'Inne', color: '#4caf50' },
        { key: 'outdoor_temp', name: 'Ute', color: '#64b5f6' },
        { key: 'brine_in_evaporator', name: 'KB In →', color: '#00d4ff' },
        { key: 'brine_out_condenser', name: 'KB Ut ←', color: '#1565c0' }
    ];

    metrics.forEach(metric => {
        if (data[metric.key]) {
            series.push({
                type: 'line',
                name: metric.name,
                data: data[metric.key].map((v, i) => [data.timestamps[i], v]),
                smooth: true,
                lineStyle: { color: metric.color, width: 2.5 }
            });
        }
    });

    const option = {
        grid: {
            left: 40,
            right: 40,
            top: 60,
            bottom: 40,
            backgroundColor: 'transparent'
        },
        legend: {
            data: metrics.map(m => m.name),
            top: 10,
            right: 10,
            orient: 'horizontal',
            textStyle: { fontSize: 11 }
        },
        xAxis: {
            type: 'time',
            name: 'Tid',
            axisLine: { lineStyle: { color: '#999' } }
        },
        yAxis: {
            type: 'value',
            name: 'Temperatur (°C)',
            axisLine: { lineStyle: { color: '#999' } }
        },
        series: series,
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross' }
        },
        backgroundColor: 'transparent'
    };

    charts.temperature.setOption(option, true);
}

function updateRuntimeChart(data) {
    // Pie/donut chart
    const option = {
        series: [{
            type: 'pie',
            radius: ['40%', '70%'],  // Donut
            data: [
                { value: data.compressor_percent, name: 'Kompressor', itemStyle: { color: '#4caf50' } },
                { value: data.aux_heater_percent, name: 'Tillsats', itemStyle: { color: '#ffc107' } },
                { value: 100 - data.compressor_percent - data.aux_heater_percent, name: 'Inaktiv', itemStyle: { color: '#e9ecef' } }
            ],
            label: {
                formatter: '{b}: {d}%'
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }],
        backgroundColor: 'transparent'
    };

    charts.runtime.setOption(option, true);
}

function updateSankeyChart(data) {
    // Sankey energy flow diagram
    const option = {
        title: {
            text: `Energiflöde (COP: ${data.cop.toFixed(2)}, ${data.free_energy_percent.toFixed(0)}% gratis från mark)`,
            textStyle: { fontSize: 14, color: 'gray' }
        },
        series: [{
            type: 'sankey',
            layout: 'none',
            emphasis: { focus: 'adjacency' },
            data: data.nodes,
            links: data.links,
            lineStyle: {
                color: 'gradient',
                curveness: 0.5
            },
            itemStyle: {
                borderWidth: 2,
                borderColor: '#fff'
            },
            label: {
                color: '#333',
                fontSize: 11
            }
        }],
        backgroundColor: 'transparent'
    };

    charts.sankey.setOption(option, true);
}

function updatePerformanceChart(data) {
    // Multi-subplot chart (2 rows)
    const option = {
        grid: [
            { left: 40, right: 40, top: 60, height: '35%' },   // Top subplot
            { left: 40, right: 40, top: '55%', height: '35%' }  // Bottom subplot
        ],
        xAxis: [
            { gridIndex: 0, type: 'time' },
            { gridIndex: 1, type: 'time', name: 'Tid' }
        ],
        yAxis: [
            { gridIndex: 0, name: 'ΔT (°C)' },
            { gridIndex: 1, name: 'Status' }
        ],
        series: [
            {
                name: 'KB ΔT',
                type: 'line',
                xAxisIndex: 0,
                yAxisIndex: 0,
                data: data.brine_delta,
                lineStyle: { color: '#26c6da', width: 2.5 }
            },
            {
                name: 'Radiator ΔT',
                type: 'line',
                xAxisIndex: 0,
                yAxisIndex: 0,
                data: data.radiator_delta,
                lineStyle: { color: '#ff5722', width: 2.5 }
            },
            {
                name: 'Kompressor',
                type: 'line',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: data.compressor_status,
                areaStyle: { color: 'rgba(76, 175, 80, 0.3)' },
                lineStyle: { color: '#4caf50', width: 2.5 }
            }
        ],
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross' }
        },
        backgroundColor: 'transparent'
    };

    charts.performance.setOption(option, true);
}

function updatePowerChart(data) {
    // Similar multi-subplot structure
    // ... (implement similar to performance chart)
}

function updateValveChart(data) {
    // 3-row subplot chart
    // ... (implement similar to performance chart)
}
```

**4.2 Create Python ECharts option builders:**
```python
# dashboard/graph_builder.py
"""Build ECharts options from data"""

def build_cop_option(cop_df, colors):
    """Build COP chart option"""
    if cop_df.empty:
        return {
            'title': {'text': 'Ingen data tillgänglig'},
            'xAxis': {'type': 'time'},
            'yAxis': {'type': 'value'}
        }

    timestamps = cop_df['_time'].astype(str).tolist()
    values = cop_df['estimated_cop'].tolist()
    avg_cop = float(cop_df['estimated_cop'].mean())

    return {
        'timestamps': timestamps,
        'values': values,
        'avg': avg_cop
    }

def build_temperature_option(df, colors):
    """Build temperature chart option"""
    metrics = [
        'outdoor_temp', 'indoor_temp', 'radiator_forward',
        'radiator_return', 'hot_water_top',
        'brine_in_evaporator', 'brine_out_condenser'
    ]

    result = {'timestamps': []}

    if not df.empty:
        # Get common timestamps
        first_metric = df[df['name'] == metrics[0]]
        if not first_metric.empty:
            result['timestamps'] = first_metric['_time'].astype(str).tolist()

        # Extract data for each metric
        for metric in metrics:
            metric_df = df[df['name'] == metric]
            if not metric_df.empty:
                result[metric] = metric_df['_value'].tolist()

    return result

def build_sankey_option(cop_df, runtime_stats):
    """Build Sankey diagram option"""
    # Reuse calculation logic from callbacks_graphs.py
    if cop_df.empty:
        avg_cop = 3.0
    else:
        avg_cop = cop_df['estimated_cop'].mean()

    electric_power = 100
    ground_energy = electric_power * (avg_cop - 1)
    aux_heater_percent = runtime_stats.get('aux_heater_runtime_percent', 0)
    aux_heater_power = (aux_heater_percent / 100) * 50 if aux_heater_percent > 0 else 0
    total_heat = electric_power + ground_energy + aux_heater_power
    free_energy_percent = (ground_energy / total_heat * 100) if total_heat > 0 else 0

    nodes = [
        {'name': '🌍 Markenergi'},
        {'name': '⚡ Elkraft'},
        {'name': '🔄 Värmepump'},
        {'name': '🏠 Värme till Hus'}
    ]

    links = [
        {'source': '🌍 Markenergi', 'target': '🔄 Värmepump', 'value': ground_energy},
        {'source': '⚡ Elkraft', 'target': '🔄 Värmepump', 'value': electric_power},
        {'source': '🔄 Värmepump', 'target': '🏠 Värme till Hus', 'value': total_heat - aux_heater_power}
    ]

    if aux_heater_power > 5:
        nodes.append({'name': '🔥 Tillsattsvärme'})
        links.append({'source': '🔥 Tillsattsvärme', 'target': '🏠 Värme till Hus', 'value': aux_heater_power})

    return {
        'nodes': nodes,
        'links': links,
        'cop': avg_cop,
        'free_energy_percent': free_energy_percent
    }

# Similar builders for performance, power, valve charts...
```

---

### **Phase 5: Testing & Polish** (Week 3-4 - 8-12 hours)

#### Goals:
- [ ] Test all charts with real InfluxDB data
- [ ] Verify WebSocket reconnection logic
- [ ] Test time range changes
- [ ] Performance testing
- [ ] Cross-browser testing
- [ ] Mobile responsive testing

#### Tasks:

**5.1 Create test suite:**
```python
# tests/test_websocket.py
import pytest
from dashboard.app import app, socketio

def test_websocket_connection():
    """Test WebSocket connection"""
    client = socketio.test_client(app)
    assert client.is_connected()

def test_time_range_change():
    """Test time range change event"""
    client = socketio.test_client(app)
    client.emit('change_time_range', {'range': '7d'})
    received = client.get_received()
    assert len(received) > 0
    assert received[0]['name'] == 'graph_update'

def test_initial_data_endpoint():
    """Test initial data API"""
    with app.test_client() as client:
        response = client.get('/api/initial-data?range=24h')
        assert response.status_code == 200
        data = response.get_json()
        assert 'cop' in data
        assert 'temperature' in data
```

**5.2 Create load testing script:**
```python
# tests/load_test.py
import socketio
import time
import threading

def connect_client(client_id):
    """Simulate a client connection"""
    sio = socketio.Client()

    @sio.on('graph_update')
    def on_update(data):
        print(f"Client {client_id} received update")

    sio.connect('http://localhost:8050')

    # Change time range randomly
    for _ in range(10):
        time.sleep(5)
        sio.emit('change_time_range', {'range': '24h'})

    sio.disconnect()

# Simulate 50 concurrent clients
threads = []
for i in range(50):
    t = threading.Thread(target=connect_client, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("Load test complete!")
```

**5.3 Performance optimization checklist:**
- [ ] Enable gzip compression for static files
- [ ] Cache initial data API responses (5 seconds)
- [ ] Use Redis for session storage (if needed)
- [ ] Optimize InfluxDB queries (already done in data_query.py)
- [ ] Minify JavaScript/CSS for production
- [ ] Enable CDN for ECharts/Socket.IO (already using CDN)

**5.4 Create deployment guide:**
```bash
# docker-compose.yml updates
version: '3'
services:
  dashboard:
    build: ./dashboard
    ports:
      - "8050:8050"
    environment:
      - INFLUXDB_URL=http://influxdb:8086
      - INFLUXDB_TOKEN=${INFLUXDB_TOKEN}
      - HEATPUMP_BRAND=thermia
    depends_on:
      - influxdb
    restart: unless-stopped
```

---

### **Phase 6: Migration & Rollback Plan** (Week 4 - 4-8 hours)

#### Goals:
- [ ] Plan gradual migration
- [ ] Create rollback procedure
- [ ] Document differences for users
- [ ] Train/notify users

#### Tasks:

**6.1 Gradual migration strategy:**
```
Option A: Parallel deployment
- Run both Dash (port 8050) and Flask (port 8051) simultaneously
- Let users test new version
- Collect feedback
- Switch after 1 week

Option B: Feature flag
- Add environment variable USE_NEW_DASHBOARD=true/false
- Default to false initially
- Gradually enable for users
```

**6.2 Rollback plan:**
```bash
# Keep old Dash code in dashboard_old/
# If issues occur:
docker-compose down
# Edit docker-compose.yml to use dashboard_old/
docker-compose up -d

# Or use git:
git checkout dashboard_backup_branch
docker-compose restart dashboard
```

**6.3 User documentation:**
```markdown
# Dashboard Update Notes

## What's New:
✅ Faster loading (75% smaller bundle size)
✅ Smoother real-time updates (WebSocket)
✅ Same functionality, modern tech

## What's Changed:
- Graphs render faster
- Updates feel more responsive
- All features work the same

## Known Differences:
- Hover tooltips look slightly different
- Export functionality updated
- Mobile experience improved
```

---

## 📊 Effort Estimation Summary

| Phase | Tasks | Hours | Complexity |
|-------|-------|-------|------------|
| 1. Setup & Infrastructure | Flask + Socket.IO setup, test connection | 8-12 | Medium |
| 2. Data Layer Integration | Integrate data_query, API endpoints, background tasks | 8-12 | Low |
| 3. Frontend Foundation | HTML structure, CSS port, WebSocket client | 12-16 | Medium |
| 4. ECharts Integration | Migrate 7 charts, styling, interactivity | 16-24 | High |
| 5. Testing & Polish | Unit tests, load tests, cross-browser | 8-12 | Medium |
| 6. Migration & Rollback | Deployment, docs, rollback plan | 4-8 | Low |
| **TOTAL** | | **56-84 hours** | **3-4 weeks** |

---

## 🎯 Success Criteria

### Must Have:
- [ ] All 7 charts display correctly with real data
- [ ] WebSocket updates work every 30 seconds
- [ ] Time range dropdown works
- [ ] No data loss or incorrect calculations
- [ ] Mobile responsive
- [ ] Same or better performance than Dash

### Should Have:
- [ ] Reconnection handling works smoothly
- [ ] Loading states for charts
- [ ] Error messages for connection issues
- [ ] Cross-browser tested (Chrome, Firefox, Safari, Edge)

### Nice to Have:
- [ ] Export chart images
- [ ] Multiple simultaneous users (load tested)
- [ ] Chart zoom/pan persistence
- [ ] Dark mode theme

---

## 🚨 Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| WebSocket connection drops | High | Medium | Implement auto-reconnect with exponential backoff |
| ECharts feature parity | Medium | Low | Test all Plotly features have ECharts equivalent |
| Performance degradation | High | Low | Load test before deployment |
| Data calculation errors | High | Low | Reuse existing data_query.py (battle-tested) |
| User resistance to change | Low | Medium | Parallel deployment, rollback plan |
| Browser compatibility | Medium | Low | Test all major browsers |

---

## 📚 Resources & Documentation

### Learning Resources:
- **Socket.IO Docs:** https://socket.io/docs/v4/
- **ECharts Docs:** https://echarts.apache.org/en/option.html
- **Flask-SocketIO:** https://flask-socketio.readthedocs.io/
- **Your current code:** Reference for calculations and logic

### Key Files to Study:
- `dashboard/callbacks_graphs.py` - All graph logic (REUSE!)
- `dashboard/data_query.py` - Data queries (REUSE!)
- `dashboard/config_colors.py` - Colors (REUSE!)

---

## 🎬 Next Steps

Ready to start? Here's what we do next:

1. **Approve this plan** - Review and adjust timeline/phases
2. **Set up development environment** - Create new Flask structure
3. **Start with Phase 1** - Get basic WebSocket connection working
4. **Iterate phase by phase** - Complete one phase before moving to next
5. **Test frequently** - Don't wait until end to test

**Question for you:**
- Does this timeline work for you (3-4 weeks)?
- Do you want to do this yourself or want help implementing?
- Should we start with Phase 1 (setup) right now?

Let me know and we can begin! 🚀
