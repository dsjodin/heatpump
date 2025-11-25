"""
Thermia Dashboard - KPI Callbacks
Hanterar KPI-kort, temperaturkort och aktuella värden
"""

import logging
from datetime import datetime
from dash import Input, Output, html
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)


def register_kpi_callbacks(app, data_query):
    """Registrera alla KPI-relaterade callbacks"""
    
    # ==================== KPI-kort ====================
    @app.callback(
        [Output('avg-cop', 'children'),
         Output('energy-cost', 'children'),
         Output('energy-kwh', 'children'),
         Output('comp-runtime', 'children'),
         Output('comp-hours', 'children'),
         Output('aux-runtime', 'children'),
         Output('aux-hours', 'children')],
        [Input('interval-component', 'n_intervals'),
         Input('time-range-dropdown', 'value'),
         Input('price-input', 'value')]
    )
    def update_kpi_cards(n, time_range, price):
        """Uppdatera KPI-kort"""
        
        # Beräkna COP
        cop_df = data_query.calculate_cop(time_range)
        if not cop_df.empty and 'estimated_cop' in cop_df.columns:
            avg_cop = cop_df['estimated_cop'].mean()
            cop_display = f"{avg_cop:.2f}"
        else:
            cop_display = "--"
        
        # Beräkna energikostnader
        costs = data_query.calculate_energy_costs(time_range, price)
        cost_display = f"{costs['total_cost']:.0f} kr"
        energy_display = f"{costs['total_kwh']:.1f} kWh"
        
        # Beräkna runtime stats
        runtime = data_query.calculate_runtime_stats(time_range)
        comp_runtime_display = f"{runtime['compressor_runtime_percent']:.0f}%"
        comp_hours_display = f"{runtime['compressor_runtime_hours']:.1f} timmar"
        aux_runtime_display = f"{runtime['aux_heater_runtime_percent']:.0f}%"
        aux_hours_display = f"{runtime['aux_heater_runtime_hours']:.1f} timmar"
        
        return (cop_display, cost_display, energy_display,
                comp_runtime_display, comp_hours_display,
                aux_runtime_display, aux_hours_display)
    
    
    # ==================== Varmvattencykler ====================
    @app.callback(
        [Output('hw-total-cycles', 'children'),
         Output('hw-cycles-per-day', 'children'),
         Output('hw-avg-duration', 'children'),
         Output('hw-avg-energy', 'children')],
        [Input('interval-component', 'n_intervals'),
         Input('time-range-dropdown', 'value')]
    )
    def update_hot_water_stats(n, time_range):
        """Uppdatera varmvattencykelstatistik"""
        
        hw_stats = data_query.analyze_hot_water_cycles(time_range)
        
        return (
            str(hw_stats['total_cycles']),
            f"{hw_stats['cycles_per_day']:.1f}",
            f"{hw_stats['avg_cycle_duration_minutes']:.0f} min",
            f"{hw_stats['avg_energy_per_cycle_kwh']:.1f} kWh"
        )
    
    
    # ==================== Aktuella värden & Status ====================
    @app.callback(
        [Output('outdoor-temp', 'children'),
         Output('outdoor-temp-minmax', 'children'),
         Output('indoor-temp', 'children'),
         Output('indoor-temp-minmax', 'children'),
         Output('hot-water-temp', 'children'),
         Output('hot-water-temp-minmax', 'children'),
         Output('power-consumption', 'children'),
         Output('power-minmax', 'children'),
         Output('brine-in-temp', 'children'),
         Output('brine-in-minmax', 'children'),
         Output('brine-out-temp', 'children'),
         Output('brine-out-minmax', 'children'),
         Output('radiator-forward-temp', 'children'),
         Output('radiator-forward-minmax', 'children'),
         Output('radiator-return-temp', 'children'),
         Output('radiator-return-minmax', 'children'),
         Output('status-indicators', 'children'),
         Output('last-update', 'children')],
        [Input('interval-component', 'n_intervals'),
         Input('time-range-dropdown', 'value')]
    )
    def update_current_values(n, time_range):
        """Uppdatera aktuella värden och MIN/MAX för valt tidsintervall"""
        latest = data_query.get_latest_values()
        min_max = data_query.get_min_max_values(time_range)
        
        def format_value(metric_name, unit="°C"):
            value = latest.get(metric_name, {}).get('value', None)
            if value is not None:
                value_str = f"{value:.1f}{unit}"
            else:
                value_str = f"--{unit}"
            
            minmax_data = min_max.get(metric_name, {})
            min_val = minmax_data.get('min')
            max_val = minmax_data.get('max')
            
            if min_val is not None and max_val is not None:
                minmax_str = f"Min: {min_val:.1f}{unit} | Max: {max_val:.1f}{unit}"
            else:
                minmax_str = ""
            
            return value_str, minmax_str
        
        outdoor_val, outdoor_mm = format_value('outdoor_temp')
        indoor_val, indoor_mm = format_value('indoor_temp')
        hot_water_val, hot_water_mm = format_value('hot_water_top')
        
        power = latest.get('power_consumption', {}).get('value', None)
        if power is not None:
            power_val = f"{power:.0f} W"
        else:
            power_val = "-- W"
        
        power_minmax_data = min_max.get('power_consumption', {})
        power_min = power_minmax_data.get('min')
        power_max = power_minmax_data.get('max')
        if power_min is not None and power_max is not None:
            power_mm = f"Min: {power_min:.0f} W | Max: {power_max:.0f} W"
        else:
            power_mm = ""
        
        brine_in_val, brine_in_mm = format_value('brine_in_evaporator')
        brine_out_val, brine_out_mm = format_value('brine_out_condenser')
        radiator_forward_val, radiator_forward_mm = format_value('radiator_forward')
        radiator_return_val, radiator_return_mm = format_value('radiator_return')
        
        # Status badges
        comp_on = latest.get('compressor_status', {}).get('value', 0) > 0
        heater_pct = latest.get('additional_heat_percent', {}).get('value', 0)
        heater_on = heater_pct > 0
        brine_on = latest.get('brine_pump_status', {}).get('value', 0) > 0
        radiator_on = latest.get('radiator_pump_status', {}).get('value', 0) > 0
        valve_status = latest.get('switch_valve_status', {}).get('value', 0)  # 0=Radiator, 1=Varmvatten
        alarm_on = latest.get('alarm_status', {}).get('value', 0) > 0
        
        badges = []
        
        badges.append(dbc.Badge(
            [html.I(className="fas fa-compress-arrows-alt me-2"), 
             "Kompressor " + ("PÅ" if comp_on else "AV")],
            color="success" if comp_on else "secondary",
            className="me-2"
        ))
        
        if heater_on:
            badges.append(dbc.Badge(
                [html.I(className="fas fa-fire me-2"), 
                 f"Tillsats {heater_pct:.0f}%"],
                color="warning" if heater_on else "secondary",
                className="me-2"
            ))
        else:
            badges.append(dbc.Badge(
                [html.I(className="fas fa-fire me-2"), "Tillsats AV"],
                color="secondary",
                className="me-2"
            ))
        
        badges.append(dbc.Badge(
            [html.I(className="fas fa-tint me-2"), 
             "KB-pump " + ("PÅ" if brine_on else "AV")],
            color="info" if brine_on else "secondary",
            className="me-2"
        ))
        
        badges.append(dbc.Badge(
            [html.I(className="fas fa-water me-2"), 
             "Radiator " + ("PÅ" if radiator_on else "AV")],
            color="info" if radiator_on else "secondary",
            className="me-2"
        ))
        
        # Växelventil - visar vad systemet gör
        if valve_status > 0:
            badges.append(dbc.Badge(
                [html.I(className="fas fa-random me-2"), "🔄 Varmvatten"],
                color="warning",
                className="me-2"
            ))
        else:
            badges.append(dbc.Badge(
                [html.I(className="fas fa-home me-2"), "🏠 Radiatorvärme"],
                color="primary",
                className="me-2"
            ))
        
        if alarm_on:
            badges.append(dbc.Badge(
                [html.I(className="fas fa-exclamation-triangle me-2"), "LARM!"],
                color="danger",
                className="me-2"
            ))
        
        status_badges = html.Div(badges, className="status-badges")
        
        # Senaste uppdatering
        now = datetime.now()
        last_update = f"Senast uppdaterad: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return (outdoor_val, outdoor_mm, indoor_val, indoor_mm,
                hot_water_val, hot_water_mm, power_val, power_mm,
                brine_in_val, brine_in_mm, brine_out_val, brine_out_mm,
                radiator_forward_val, radiator_forward_mm,
                radiator_return_val, radiator_return_mm,
                status_badges, last_update)
    
    
    # ==================== Live Systemschema ====================
    @app.callback(
        [Output('temp-utetemp', 'children'),
         Output('temp-varmvatten', 'children'),
         Output('temp-kb-in', 'children'),
         Output('temp-kb-ut', 'children'),
         Output('temp-framledning', 'children'),
         Output('temp-radiator-retur', 'children'),
         Output('schema-kompressor', 'style'),
         Output('schema-kb-pump', 'style'),
         Output('schema-rad-pump', 'style'),
         Output('schema-3kw', 'src'),
         Output('schema-radiator', 'style'),
         Output('schema-vv-on', 'style'),
         Output('schema-valve-radiator', 'style'),
         Output('schema-valve-varmvatten', 'style')],
        [Input('interval-component', 'n_intervals')]
    )
    def update_heatpump_schema(n):
        """Uppdatera live systemschema med aktuella värden och animationer"""
        latest = data_query.get_latest_values()
        
        # Hämta temperaturvärden
        outdoor = latest.get('outdoor_temp', {}).get('value')
        hot_water = latest.get('hot_water_top', {}).get('value')
        brine_in = latest.get('brine_in_evaporator', {}).get('value')
        brine_out = latest.get('brine_out_condenser', {}).get('value')
        forward = latest.get('radiator_forward', {}).get('value')
        ret = latest.get('radiator_return', {}).get('value')
        
        # Formatera temperaturvärden
        temp_outdoor = f"{outdoor:.1f}°C" if outdoor is not None else "--°C"
        temp_hotwater = f"{hot_water:.1f}°C" if hot_water is not None else "--°C"
        temp_brine_in = f"{brine_in:.1f}°C" if brine_in is not None else "--°C"
        temp_brine_out = f"{brine_out:.1f}°C" if brine_out is not None else "--°C"
        temp_forward = f"{forward:.1f}°C" if forward is not None else "--°C"
        temp_return = f"{ret:.1f}°C" if ret is not None else "--°C"
        
        # Hämta status
        comp_on = latest.get('compressor_status', {}).get('value', 0) > 0
        kb_on = latest.get('brine_pump_status', {}).get('value', 0) > 0
        rad_on = latest.get('radiator_pump_status', {}).get('value', 0) > 0
        aux_pct = latest.get('additional_heat_percent', {}).get('value', 0)
        valve_status = latest.get('switch_valve_status', {}).get('value', 0)  # 0=Rad, 1=VV
        
        # Kompressor animation (visa GIF när PÅ)
        komp_style = {'display': 'block'} if comp_on else {'display': 'none'}
        
        # KB-pump rotation (visa när PÅ)
        kb_style = {'display': 'block'} if kb_on else {'display': 'none'}
        
        # Radiatorpump rotation (visa när PÅ)
        rad_pump_style = {'display': 'block'} if rad_on else {'display': 'none'}
        
        # 3kW värme (orange när PÅ, grå när AV)
        aux_on = aux_pct > 0
        aux_src = '/assets/schema/3kw-on.png' if aux_on else '/assets/schema/3kw-off.png'
        
        # Radiator varm (visa när forward temp > 30°C)
        rad_hot = forward is not None and forward > 30
        rad_style = {'display': 'block'} if rad_hot else {'display': 'none'}
        
        # Växelventil pil (rotera baserat på läge)
        # 0 = Radiator (ingen rotation), 1 = Varmvatten (rotera 90°)
        # valve_rotation = 90 if valve_status > 0 else 0
        # valve_style = {'transform': f'rotate({valve_rotation}deg)', 'transition': 'transform 0.5s ease'}
        valve_rad_style = {'display': 'block'} if valve_status == 0 else {'display': 'none'}
        valve_vv_style = {'display': 'block'} if valve_status > 0 else {'display': 'none'}
        vv_hot_style = {'display': 'block'} if valve_status > 0 else {'display': 'none'}
        
        return (temp_outdoor, temp_hotwater, temp_brine_in, temp_brine_out,
                temp_forward, temp_return, komp_style, kb_style, rad_pump_style,
                aux_src, rad_style, vv_hot_style, valve_rad_style, valve_vv_style)


    # ==================== Topbar Quick Stats ====================
    @app.callback(
        [Output('topbar-outdoor', 'children'),
         Output('topbar-indoor', 'children'),
         Output('topbar-hotwater', 'children'),
         Output('topbar-cop', 'children'),
         Output('topbar-power', 'children'),
         Output('topbar-status', 'children'),
         Output('topbar-status-icon', 'className')],
        [Input('interval-component', 'n_intervals'),
         Input('time-range-dropdown', 'value')]
    )
    def update_topbar_quickstats(n, time_range):
        """Uppdatera topbar quick stats"""
        latest = data_query.get_latest_values()

        # Temperaturer
        outdoor = latest.get('outdoor_temp', {}).get('value')
        indoor = latest.get('indoor_temp', {}).get('value')
        hotwater = latest.get('hot_water_top', {}).get('value')

        outdoor_str = f"{outdoor:.1f}°C" if outdoor is not None else "--°C"
        indoor_str = f"{indoor:.1f}°C" if indoor is not None else "--°C"
        hotwater_str = f"{hotwater:.1f}°C" if hotwater is not None else "--°C"

        # COP
        cop_df = data_query.calculate_cop(time_range)
        if not cop_df.empty and 'estimated_cop' in cop_df.columns:
            avg_cop = cop_df['estimated_cop'].mean()
            cop_str = f"{avg_cop:.2f}"
        else:
            cop_str = "--"

        # Effekt
        power = latest.get('power_consumption', {}).get('value')
        power_str = f"{power:.0f} W" if power is not None else "-- W"

        # Status - visa kompressor eller larm
        alarm_on = latest.get('alarm_status', {}).get('value', 0) > 0
        comp_on = latest.get('compressor_status', {}).get('value', 0) > 0

        if alarm_on:
            status_str = "LARM!"
            status_icon = "fas fa-exclamation-triangle me-2 topbar-icon text-danger"
        elif comp_on:
            status_str = "Kompressor PÅ"
            status_icon = "fas fa-check-circle me-2 topbar-icon text-success"
        else:
            status_str = "Vilande"
            status_icon = "fas fa-pause-circle me-2 topbar-icon text-secondary"

        return (outdoor_str, indoor_str, hotwater_str, cop_str, power_str,
                status_str, status_icon)
