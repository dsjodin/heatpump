"""
Thermia Dashboard - Status Callbacks
Hanterar larmstatus och händelselogg
"""

import logging
from datetime import datetime
from dash import Input, Output, html
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)


def register_status_callbacks(app, data_query):
    """Registrera alla status-relaterade callbacks"""
    
    # ==================== Larmstatus ====================
    @app.callback(
        [Output('alarm-status', 'children'),
         Output('alarm-card', 'className')],
        [Input('interval-component', 'n_intervals')]
    )
    def update_alarm_status(n):
        """Uppdatera larmstatus"""
        alarm = data_query.get_alarm_status()
        
        if alarm['is_alarm']:
            # LARM AKTIVT
            alarm_time = alarm['alarm_time']
            if alarm_time:
                if hasattr(alarm_time, 'strftime'):
                    time_str = alarm_time.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    time_str = str(alarm_time)
                
                duration = datetime.now(alarm_time.tzinfo) - alarm_time
                hours = int(duration.total_seconds() / 3600)
                minutes = int((duration.total_seconds() % 3600) / 60)
                
                if hours > 0:
                    duration_str = f"{hours}h {minutes}min"
                else:
                    duration_str = f"{minutes}min"
            else:
                time_str = "Okänd"
                duration_str = "Okänd"
            
            content = html.Div([
                html.Div([
                    html.I(className="fas fa-exclamation-circle fa-3x text-danger mb-3"),
                ], className="text-center"),
                html.H4("⚠️ LARM AKTIVT!", className="text-danger text-center mb-3"),
                html.Div([
                    html.Strong(f"Larmkod {alarm['alarm_code']}: "),
                    html.Span(alarm['alarm_description'])
                ], className="mb-2 alarm-description"),
                html.Hr(),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-clock me-2"),
                        html.Strong("Aktiverad: "),
                        html.Span(time_str)
                    ], className="mb-2"),
                    html.Div([
                        html.I(className="fas fa-hourglass-half me-2"),
                        html.Strong("Varaktighet: "),
                        html.Span(duration_str)
                    ])
                ], className="alarm-details"),
                html.Hr(),
                html.Div([
                    html.I(className="fas fa-info-circle me-2"),
                    html.Span("Kontrollera värmepumpen och återställ larmet efter åtgärd.", 
                             className="text-muted")
                ], className="mt-3")
            ])
            
            card_class = "alarm-card alarm-active"
            
        else:
            # INGET LARM
            content = html.Div([
                html.Div([
                    html.I(className="fas fa-check-circle fa-2x text-success mb-2"),
                ], className="text-center"),
                html.H5("✅ Inget aktivt larm", className="text-success text-center mb-2"),
                html.P("Systemet fungerar normalt", className="text-muted text-center mb-0")
            ])
            
            card_class = "alarm-card alarm-ok"
        
        return content, card_class
    
    
    # ==================== Händelselogg ====================
    @app.callback(
        Output('event-log', 'children'),
        [Input('interval-component', 'n_intervals')]
    )
    def update_event_log(n):
        """Uppdatera händelselogg"""
        events = data_query.get_event_log(limit=10)
        
        if not events:
            # Visa varför det inte finns några händelser
            latest = data_query.get_latest_values()
            
            return html.Div([
                html.Div([
                    html.I(className="fas fa-info-circle fa-2x text-muted mb-3"),
                ], className="text-center"),
                html.H6("Inga händelser hittade senaste 24h", className="text-center text-muted mb-3"),
                html.Hr(),
                html.H6("Nuvarande tillstånd:", className="mb-2"),
                html.Div([
                    html.Div([
                        html.I(className="fas fa-circle me-2", 
                              style={'color': '#51cf66' if latest.get('compressor_status', {}).get('value', 0) > 0 else '#868e96'}),
                        html.Span(f"Kompressor: ", className="fw-bold"),
                        html.Span('PÅ' if latest.get('compressor_status', {}).get('value', 0) > 0 else 'AV')
                    ], className="mb-2"),
                    html.Div([
                        html.I(className="fas fa-circle me-2",
                              style={'color': '#51cf66' if latest.get('brine_pump_status', {}).get('value', 0) > 0 else '#868e96'}),
                        html.Span(f"Köldbärarpump: ", className="fw-bold"),
                        html.Span('PÅ' if latest.get('brine_pump_status', {}).get('value', 0) > 0 else 'AV')
                    ], className="mb-2"),
                    html.Div([
                        html.I(className="fas fa-circle me-2",
                              style={'color': '#51cf66' if latest.get('radiator_pump_status', {}).get('value', 0) > 0 else '#868e96'}),
                        html.Span(f"Radiatorpump: ", className="fw-bold"),
                        html.Span('PÅ' if latest.get('radiator_pump_status', {}).get('value', 0) > 0 else 'AV')
                    ], className="mb-2"),
                    html.Div([
                        html.I(className="fas fa-circle me-2",
                              style={'color': '#ffd43b' if latest.get('additional_heat_percent', {}).get('value', 0) > 0 else '#868e96'}),
                        html.Span(f"Tillsattsvärme: ", className="fw-bold"),
                        html.Span(f"{latest.get('additional_heat_percent', {}).get('value', 0):.0f}%")
                    ], className="mb-2"),
                ], className="p-3 bg-light rounded"),
                html.Hr(),
                html.P([
                    html.I(className="fas fa-clock me-2"),
                    "Händelser kommer visas när statusändringar sker (kompressor startar/stoppar, varmvattencykel, etc.)"
                ], className="text-muted small text-center mb-2"),
                html.P([
                    html.I(className="fas fa-sync me-2"),
                    "Uppdateras automatiskt var 30:e sekund"
                ], className="text-muted small text-center mb-0")
            ], className="text-start py-3")
        
        event_items = []
        
        for event in events:
            # Formatera tid
            event_time = event['time']
            if hasattr(event_time, 'strftime'):
                time_str = event_time.strftime('%Y-%m-%d %H:%M')
            else:
                time_str = str(event_time)
            
            # Färg baserat på typ
            if event['type'] == 'danger':
                badge_color = 'danger'
                text_class = 'text-danger'
            elif event['type'] == 'warning':
                badge_color = 'warning'
                text_class = 'text-warning'
            elif event['type'] == 'success':
                badge_color = 'success'
                text_class = 'text-success'
            else:
                badge_color = 'info'
                text_class = 'text-muted'
            
            event_item = html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Span(event['icon'], className="event-icon me-2"),
                        html.Span(time_str, className="event-time text-muted")
                    ], width=3, className="text-start"),
                    dbc.Col([
                        html.Span(event['event'], className=f"event-text {text_class}")
                    ], width=9, className="text-start")
                ], className="align-items-center")
            ], className="event-log-item")
            
            event_items.append(event_item)
        
        return html.Div(event_items)
