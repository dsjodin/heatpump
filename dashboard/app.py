#!/usr/bin/env python3
"""
Heat Pump Dashboard - Flask + WebSocket Version
Modern architecture with ECharts and Socket.IO
Supports: Thermia, IVT, NIBE
"""

import os
import sys
import logging
import yaml
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import eventlet

# Add parent directory to path for provider imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from providers import get_provider
from data_query import HeatPumpDataQuery
from config_colors import THERMIA_COLORS

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'heatpump-dashboard-secret-key')
CORS(app)

# Initialize Socket.IO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    ping_timeout=60,
    ping_interval=25
)

# Load provider from config
def load_provider():
    """Load heat pump provider from config"""
    config_path = '/app/config.yaml'
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            brand = config.get('brand', 'thermia')
        else:
            brand = os.getenv('HEATPUMP_BRAND', 'thermia')

        provider = get_provider(brand)
        logger.info(f"✅ Loaded provider: {provider.get_display_name()}")
        return provider
    except Exception as e:
        logger.error(f"Failed to load provider: {e}, defaulting to Thermia")
        from providers.thermia.provider import ThermiaProvider
        return ThermiaProvider()


# Initialize global objects
provider = load_provider()
data_query = HeatPumpDataQuery()

# Store connected clients and their time ranges
connected_clients = {}


# ==================== HTTP Routes ====================

@app.route('/')
def index():
    """Serve main dashboard page"""
    return render_template('dashboard.html',
                         brand_name=provider.get_display_name(),
                         dashboard_title=provider.get_dashboard_title())

@app.route('/test')
def test():
    """Serve test dashboard page"""
    return render_template('index.html',
                         brand_name=provider.get_display_name(),
                         dashboard_title=provider.get_dashboard_title())


@app.route('/api/config')
def get_config():
    """Get dashboard configuration"""
    return jsonify({
        'brand': provider.get_brand_name(),
        'display_name': provider.get_display_name(),
        'colors': THERMIA_COLORS
    })


@app.route('/api/initial-data')
def get_initial_data():
    """Load all graph data for initial page load"""
    time_range = request.args.get('range', '24h')

    try:
        logger.info(f"📥 Loading initial data for range: {time_range}")

        data = {
            'cop': get_cop_data(time_range),
            'temperature': get_temperature_data(time_range),
            'runtime': get_runtime_data(time_range),
            'sankey': get_sankey_data(time_range),
            'performance': get_performance_data(time_range),
            'power': get_power_data(time_range),
            'valve': get_valve_data(time_range),
            'status': get_status_data(),
            'events': get_event_log(20),
            'kpi': get_kpi_data(time_range),
            'config': {
                'brand': provider.get_brand_name(),
                'display_name': provider.get_display_name(),
                'colors': THERMIA_COLORS
            }
        }

        logger.info(f"✅ Initial data loaded successfully")
        return jsonify(data)

    except Exception as e:
        logger.error(f"❌ Error loading initial data: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== Data Extraction Functions ====================

def get_cop_data(time_range):
    """Extract COP data from data_query"""
    try:
        cop_df = data_query.calculate_cop(time_range)

        if cop_df.empty or 'estimated_cop' not in cop_df.columns:
            return {'timestamps': [], 'values': [], 'avg': 0}

        return {
            'timestamps': cop_df['_time'].astype(str).tolist(),
            'values': cop_df['estimated_cop'].tolist(),
            'avg': float(cop_df['estimated_cop'].mean())
        }
    except Exception as e:
        logger.error(f"Error getting COP data: {e}")
        return {'timestamps': [], 'values': [], 'avg': 0}


def get_temperature_data(time_range):
    """Extract temperature data from data_query"""
    try:
        metrics = [
            'outdoor_temp', 'indoor_temp', 'radiator_forward',
            'radiator_return', 'hot_water_top',
            'brine_in_evaporator', 'brine_out_condenser'
        ]

        df = data_query.query_metrics(metrics, time_range)

        result = {'timestamps': []}

        if not df.empty:
            # Get common timestamps from first metric
            first_metric = df[df['name'] == metrics[0]]
            if not first_metric.empty:
                result['timestamps'] = first_metric['_time'].astype(str).tolist()

            # Extract data for each metric
            for metric in metrics:
                metric_df = df[df['name'] == metric]
                if not metric_df.empty:
                    result[metric] = metric_df['_value'].tolist()

        return result
    except Exception as e:
        logger.error(f"Error getting temperature data: {e}")
        return {'timestamps': []}


def get_runtime_data(time_range):
    """Extract runtime statistics"""
    try:
        runtime_stats = data_query.calculate_runtime_stats(time_range)
        return {
            'compressor_percent': runtime_stats.get('compressor_runtime_percent', 0),
            'aux_heater_percent': runtime_stats.get('aux_heater_runtime_percent', 0),
            'inactive_percent': 100 - runtime_stats.get('compressor_runtime_percent', 0) -
                              runtime_stats.get('aux_heater_runtime_percent', 0)
        }
    except Exception as e:
        logger.error(f"Error getting runtime data: {e}")
        return {'compressor_percent': 0, 'aux_heater_percent': 0, 'inactive_percent': 100}


def get_sankey_data(time_range):
    """Build Sankey diagram data"""
    try:
        cop_df = data_query.calculate_cop(time_range)
        runtime_stats = data_query.calculate_runtime_stats(time_range)

        # Calculate energy flows (same logic as Plotly version)
        if cop_df.empty or 'estimated_cop' not in cop_df.columns:
            avg_cop = 3.0
            has_data = False
        else:
            avg_cop = float(cop_df['estimated_cop'].mean())
            has_data = True

        # Ensure reasonable COP value
        if avg_cop < 1.5 or avg_cop > 6.0:
            avg_cop = 3.0

        # Calculate energy flows (normalized to 100 units electric power)
        electric_power = 100
        ground_energy = electric_power * (avg_cop - 1)
        aux_heater_percent = runtime_stats.get('aux_heater_runtime_percent', 0)
        aux_heater_power = (aux_heater_percent / 100) * 50 if aux_heater_percent > 0 else 0
        total_heat = electric_power + ground_energy + aux_heater_power
        free_energy_percent = (ground_energy / total_heat * 100) if total_heat > 0 else 0

        # Build nodes and links
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
            'free_energy_percent': free_energy_percent,
            'has_data': has_data
        }
    except Exception as e:
        logger.error(f"Error getting Sankey data: {e}")
        return {
            'nodes': [],
            'links': [],
            'cop': 0,
            'free_energy_percent': 0,
            'has_data': False
        }


def get_performance_data(time_range):
    """Extract performance graph data (delta temperatures + compressor status)"""
    try:
        metrics = [
            'brine_in_evaporator',
            'brine_out_condenser',
            'radiator_forward',
            'radiator_return',
            'compressor_status'
        ]

        df = data_query.query_metrics(metrics, time_range)

        result = {
            'brine_delta': [],
            'radiator_delta': [],
            'compressor_status': [],
            'timestamps': []
        }

        if not df.empty:
            # Calculate brine delta (ΔT)
            brine_in = df[df['name'] == 'brine_in_evaporator']
            brine_out = df[df['name'] == 'brine_out_condenser']

            if not brine_in.empty and not brine_out.empty:
                import pandas as pd
                brine_delta = pd.merge(
                    brine_in[['_time', '_value']],
                    brine_out[['_time', '_value']],
                    on='_time',
                    suffixes=('_in', '_out')
                )
                brine_delta['delta'] = brine_delta['_value_in'] - brine_delta['_value_out']

                result['brine_delta'] = [
                    [row['_time'].isoformat(), float(row['delta'])]
                    for _, row in brine_delta.iterrows()
                ]

            # Calculate radiator delta (ΔT)
            rad_forward = df[df['name'] == 'radiator_forward']
            rad_return = df[df['name'] == 'radiator_return']

            if not rad_forward.empty and not rad_return.empty:
                import pandas as pd
                rad_delta = pd.merge(
                    rad_forward[['_time', '_value']],
                    rad_return[['_time', '_value']],
                    on='_time',
                    suffixes=('_fwd', '_ret')
                )
                rad_delta['delta'] = rad_delta['_value_fwd'] - rad_delta['_value_ret']

                result['radiator_delta'] = [
                    [row['_time'].isoformat(), float(row['delta'])]
                    for _, row in rad_delta.iterrows()
                ]

            # Get compressor status
            comp = df[df['name'] == 'compressor_status']
            if not comp.empty:
                result['compressor_status'] = [
                    [row['_time'].isoformat(), float(row['_value'])]
                    for _, row in comp.iterrows()
                ]
                result['timestamps'] = comp['_time'].astype(str).tolist()

        return result
    except Exception as e:
        logger.error(f"Error getting performance data: {e}")
        return {
            'brine_delta': [],
            'radiator_delta': [],
            'compressor_status': [],
            'timestamps': []
        }


def get_power_data(time_range):
    """Extract power graph data (power consumption + system status)"""
    try:
        metrics = [
            'power_consumption',
            'compressor_status',
            'additional_heat_percent'
        ]

        df = data_query.query_metrics(metrics, time_range)

        result = {
            'power_consumption': [],
            'compressor_status': [],
            'additional_heat_percent': [],
            'timestamps': []
        }

        if not df.empty:
            # Get power consumption
            power = df[df['name'] == 'power_consumption']
            if not power.empty:
                result['power_consumption'] = [
                    [row['_time'].isoformat(), float(row['_value'])]
                    for _, row in power.iterrows()
                ]
                result['timestamps'] = power['_time'].astype(str).tolist()

            # Get compressor status
            comp = df[df['name'] == 'compressor_status']
            if not comp.empty:
                result['compressor_status'] = [
                    [row['_time'].isoformat(), float(row['_value'])]
                    for _, row in comp.iterrows()
                ]

            # Get auxiliary heater percentage
            heater = df[df['name'] == 'additional_heat_percent']
            if not heater.empty:
                result['additional_heat_percent'] = [
                    [row['_time'].isoformat(), float(row['_value'])]
                    for _, row in heater.iterrows()
                ]

        return result
    except Exception as e:
        logger.error(f"Error getting power data: {e}")
        return {
            'power_consumption': [],
            'compressor_status': [],
            'additional_heat_percent': [],
            'timestamps': []
        }


def get_valve_data(time_range):
    """Extract valve status graph data (valve + compressor + hot water temp)"""
    try:
        metrics = [
            'switch_valve_status',
            'compressor_status',
            'hot_water_top'
        ]

        df = data_query.query_metrics(metrics, time_range)

        result = {
            'valve_status': [],
            'compressor_status': [],
            'hot_water_temp': [],
            'timestamps': []
        }

        if not df.empty:
            # Get valve status
            valve = df[df['name'] == 'switch_valve_status']
            if not valve.empty:
                result['valve_status'] = [
                    [row['_time'].isoformat(), float(row['_value'])]
                    for _, row in valve.iterrows()
                ]
                result['timestamps'] = valve['_time'].astype(str).tolist()

            # Get compressor status
            comp = df[df['name'] == 'compressor_status']
            if not comp.empty:
                result['compressor_status'] = [
                    [row['_time'].isoformat(), float(row['_value'])]
                    for _, row in comp.iterrows()
                ]

            # Get hot water temperature
            hw_temp = df[df['name'] == 'hot_water_top']
            if not hw_temp.empty:
                result['hot_water_temp'] = [
                    [row['_time'].isoformat(), float(row['_value'])]
                    for _, row in hw_temp.iterrows()
                ]

        return result
    except Exception as e:
        logger.error(f"Error getting valve data: {e}")
        return {
            'valve_status': [],
            'compressor_status': [],
            'hot_water_temp': [],
            'timestamps': []
        }


def get_status_data():
    """Get current system status including alarm, compressor, and current metrics"""
    try:
        # Get alarm status
        alarm = data_query.get_alarm_status()

        # Get current metrics for status display
        current_metrics = data_query.get_latest_values()

        # Calculate current COP if possible
        current_cop = None
        try:
            cop_data = data_query.get_cop('1h')  # Get last hour for current COP
            if cop_data and len(cop_data) > 0:
                current_cop = round(cop_data[-1], 2) if cop_data[-1] is not None else None
        except:
            pass

        status = {
            'alarm': {
                'is_active': alarm.get('is_alarm', False),
                'code': alarm.get('alarm_code'),
                'description': alarm.get('alarm_description'),
                'time': alarm['alarm_time'].isoformat() if alarm.get('alarm_time') else None
            },
            'current': {
                'outdoor_temp': round(current_metrics.get('outdoor_temp', 0), 1) if current_metrics.get('outdoor_temp') is not None else None,
                'indoor_temp': round(current_metrics.get('indoor_temp', 0), 1) if current_metrics.get('indoor_temp') is not None else None,
                'hot_water': round(current_metrics.get('hot_water_top', 0), 1) if current_metrics.get('hot_water_top') is not None else None,
                'compressor_running': bool(current_metrics.get('compressor_status', 0)),
                'brine_temp': round(current_metrics.get('brine_in_evaporator', 0), 1) if current_metrics.get('brine_in_evaporator') is not None else None,
                'radiator_temp': round(current_metrics.get('radiator_forward', 0), 1) if current_metrics.get('radiator_forward') is not None else None,
                'current_cop': current_cop
            },
            'timestamp': datetime.now().isoformat()
        }

        return status
    except Exception as e:
        logger.error(f"Error getting status data: {e}")
        return {
            'alarm': {'is_active': False, 'code': None, 'description': None, 'time': None},
            'current': {},
            'timestamp': datetime.now().isoformat()
        }


def get_event_log(limit=20):
    """Get recent event log entries"""
    try:
        events = data_query.get_event_log(limit=limit)

        event_list = []
        for event in events:
            event_list.append({
                'time': event.get('time', '').isoformat() if hasattr(event.get('time', ''), 'isoformat') else str(event.get('time', '')),
                'type': event.get('type', 'unknown'),
                'description': event.get('description', 'No description'),
                'value': event.get('value')
            })

        return event_list
    except Exception as e:
        logger.error(f"Error getting event log: {e}")
        return []


def get_kpi_data(time_range='24h', price_per_kwh=2.0):
    """Get extended KPI metrics (energy, runtime, hot water)"""
    try:
        # Calculate energy costs
        energy_costs = data_query.calculate_energy_costs(time_range, price_per_kwh)

        # Calculate runtime statistics
        runtime_stats = data_query.calculate_runtime_stats(time_range)

        # Analyze hot water cycles (use longer period for meaningful stats)
        hw_time_range = '7d' if time_range in ['1h', '6h', '24h'] else time_range
        hot_water_stats = data_query.analyze_hot_water_cycles(hw_time_range)

        kpi = {
            'energy': {
                'total_kwh': energy_costs.get('total_kwh', 0),
                'total_cost': energy_costs.get('total_cost', 0),
                'avg_power': energy_costs.get('avg_power', 0),
                'peak_power': energy_costs.get('peak_power', 0)
            },
            'runtime': {
                'compressor_hours': runtime_stats.get('compressor_runtime_hours', 0),
                'compressor_percent': runtime_stats.get('compressor_runtime_percent', 0),
                'aux_heater_hours': runtime_stats.get('aux_heater_runtime_hours', 0),
                'aux_heater_percent': runtime_stats.get('aux_heater_runtime_percent', 0),
                'total_hours': runtime_stats.get('total_hours', 0)
            },
            'hot_water': {
                'total_cycles': hot_water_stats.get('total_cycles', 0),
                'cycles_per_day': hot_water_stats.get('cycles_per_day', 0),
                'avg_duration_minutes': hot_water_stats.get('avg_cycle_duration_minutes', 0),
                'avg_energy_kwh': hot_water_stats.get('avg_energy_per_cycle_kwh', 0)
            }
        }

        return kpi
    except Exception as e:
        logger.error(f"Error getting KPI data: {e}")
        return {
            'energy': {'total_kwh': 0, 'total_cost': 0, 'avg_power': 0, 'peak_power': 0},
            'runtime': {'compressor_hours': 0, 'compressor_percent': 0, 'aux_heater_hours': 0, 'aux_heater_percent': 0, 'total_hours': 0},
            'hot_water': {'total_cycles': 0, 'cycles_per_day': 0, 'avg_duration_minutes': 0, 'avg_energy_kwh': 0}
        }


# ==================== WebSocket Handlers ====================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.sid
    connected_clients[client_id] = {'time_range': '24h', 'connected_at': datetime.now()}
    logger.info(f"✅ Client connected: {client_id} (Total: {len(connected_clients)})")

    # Send welcome message
    emit('connection_status', {'status': 'connected', 'message': 'WebSocket ansluten'})

    # Start background task if not already running
    if not hasattr(socketio, 'background_task_started'):
        socketio.background_task_started = True
        logger.info("🚀 Starting background update task...")
        socketio.start_background_task(background_updates)


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid
    if client_id in connected_clients:
        del connected_clients[client_id]
    logger.info(f"❌ Client disconnected: {client_id} (Total: {len(connected_clients)})")


@socketio.on('ping')
def handle_ping():
    """Handle ping from client"""
    emit('pong', {'timestamp': datetime.now().isoformat()})


@socketio.on('change_time_range')
def handle_time_range_change(data):
    """Handle time range change from client"""
    client_id = request.sid
    time_range = data.get('range', '24h')

    logger.info(f"🔄 Client {client_id} changed time range to: {time_range}")

    # Update client's time range
    if client_id in connected_clients:
        connected_clients[client_id]['time_range'] = time_range

    # Send updated data immediately to this client
    try:
        update_data = {
            'cop': get_cop_data(time_range),
            'temperature': get_temperature_data(time_range),
            'runtime': get_runtime_data(time_range),
            'sankey': get_sankey_data(time_range),
            'performance': get_performance_data(time_range),
            'power': get_power_data(time_range),
            'valve': get_valve_data(time_range),
            'status': get_status_data(),
            'events': get_event_log(20),
            'kpi': get_kpi_data(time_range),
            'timestamp': datetime.now().isoformat()
        }

        emit('graph_update', update_data)
        logger.info(f"✅ Sent updated data to client {client_id}")

    except Exception as e:
        logger.error(f"❌ Error sending update to client {client_id}: {e}")
        emit('error', {'message': str(e)})


@socketio.on('request_update')
def handle_manual_update(data):
    """Handle manual update request from client"""
    client_id = request.sid
    time_range = data.get('range', '24h')

    logger.info(f"🔄 Client {client_id} requested manual update")

    try:
        update_data = {
            'cop': get_cop_data(time_range),
            'temperature': get_temperature_data(time_range),
            'runtime': get_runtime_data(time_range),
            'sankey': get_sankey_data(time_range),
            'performance': get_performance_data(time_range),
            'power': get_power_data(time_range),
            'valve': get_valve_data(time_range),
            'status': get_status_data(),
            'events': get_event_log(20),
            'kpi': get_kpi_data(time_range),
            'timestamp': datetime.now().isoformat()
        }

        emit('graph_update', update_data)

    except Exception as e:
        logger.error(f"❌ Error in manual update: {e}")
        emit('error', {'message': str(e)})


# ==================== Background Tasks ====================

def background_updates():
    """Background task to push updates every 30 seconds"""
    logger.info("🔄 Background update task started")

    while True:
        try:
            # Wait 30 seconds (matches Dash interval)
            eventlet.sleep(30)

            if not connected_clients:
                continue

            logger.info(f"📊 Pushing updates to {len(connected_clients)} clients...")

            # Send updates to all connected clients
            # Note: Each client might have different time_range, but we'll use 24h as default
            # for broadcast. Individual clients can request specific ranges.
            time_range = '24h'

            update_data = {
                'cop': get_cop_data(time_range),
                'temperature': get_temperature_data(time_range),
                'runtime': get_runtime_data(time_range),
                'sankey': get_sankey_data(time_range),
                'performance': get_performance_data(time_range),
                'power': get_power_data(time_range),
                'valve': get_valve_data(time_range),
                'status': get_status_data(),
                'events': get_event_log(20),
                'kpi': get_kpi_data(time_range),
                'timestamp': datetime.now().isoformat()
            }

            # Broadcast to all clients
            socketio.emit('graph_update', update_data, broadcast=True)

            logger.info(f"✅ Updates pushed at {datetime.now().strftime('%H:%M:%S')}")

        except Exception as e:
            logger.error(f"❌ Error in background update: {e}")
            eventlet.sleep(5)  # Wait a bit before retrying


# ==================== Main ====================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info(f"🔥 Starting {provider.get_display_name()} Dashboard")
    logger.info("=" * 60)
    logger.info("📊 WebSocket Dashboard with ECharts")
    logger.info(f"🏢 Provider: {provider.get_brand_name()}")
    logger.info("🔌 WebSocket support: Socket.IO")
    logger.info("📈 Charts: ECharts 5.4+")
    logger.info("⏱️  Auto-update: Every 30 seconds")
    logger.info("🌐 Dashboard will be available at http://localhost:8050")
    logger.info("=" * 60)

    socketio.run(
        app,
        host='0.0.0.0',
        port=8050,
        debug=True,
        use_reloader=False  # Disable reloader to prevent duplicate background tasks
    )
