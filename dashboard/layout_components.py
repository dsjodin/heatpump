"""
Thermia Dashboard Layout - SVENSK VERSION
Alla UI-komponenter och layoutstruktur med Sankey energiflödesdiagram
"""

from dash import dcc, html
import dash_bootstrap_components as dbc


def create_header():
    """Skapa dashboard-header"""
    return dbc.Row([
        dbc.Col([
            html.Div([
                html.H1([
                    html.I(className="fas fa-fire me-3"),
                    "Thermia Värmepump Monitor"
                ], className="text-center mb-3 dashboard-title"),
                html.P(
                    "Avancerad övervakning med COP, kostnader och prestandaanalys",
                    className="text-center text-muted dashboard-subtitle"
                )
            ], className="header-section")
        ])
    ])


def create_controls():
    """Skapa kontrollpanel med tidsintervall och prisinmatning"""
    return dbc.Row([
        dbc.Col([
            dbc.Label("Tidsintervall:", className="fw-bold"),
            dcc.Dropdown(
                id='time-range-dropdown',
                options=[
                    {'label': '⏰ Senaste timmen', 'value': '1h'},
                    {'label': '⏰ Senaste 6 timmarna', 'value': '6h'},
                    {'label': '⏰ Senaste 24 timmarna', 'value': '24h'},
                    {'label': '📅 Senaste 7 dagarna', 'value': '7d'},
                    {'label': '📅 Senaste 30 dagarna', 'value': '30d'},
                ],
                value='24h',
                clearable=False,
                className="custom-dropdown"
            )
        ], md=3),
        dbc.Col([
            dbc.Label("Elpris (kr/kWh):", className="fw-bold"),
            dbc.Input(
                id='price-input',
                type='number',
                value=2.0,
                min=0.5,
                max=10,
                step=0.1,
                className="custom-input"
            )
        ], md=2),
        dbc.Col([
            html.Div(id='last-update', className="text-end mt-4 text-muted update-time")
        ], md=7)
    ], className="mb-4 control-panel")


def create_kpi_cards():
    """Skapa KPI-prestationskort"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-chart-line kpi-icon"),
                        html.H6("Medel COP", className="card-title mb-2"),
                    ], className="d-flex align-items-center"),
                    html.H2(id="avg-cop", children="--", className="mb-1 kpi-value"),
                    html.Small("Värmefaktor", className="text-muted")
                ], className="kpi-card-body")
            ], className="kpi-card kpi-success")
        ], xs=12, sm=6, md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-money-bill-wave kpi-icon"),
                        html.H6("Energikostnad", className="card-title mb-2"),
                    ], className="d-flex align-items-center"),
                    html.H2(id="energy-cost", children="-- kr", className="mb-1 kpi-value"),
                    html.Small(id="energy-kwh", className="text-muted")
                ], className="kpi-card-body")
            ], className="kpi-card kpi-primary")
        ], xs=12, sm=6, md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-cog kpi-icon"),
                        html.H6("Kompressor", className="card-title mb-2"),
                    ], className="d-flex align-items-center"),
                    html.H2(id="comp-runtime", children="-- %", className="mb-1 kpi-value"),
                    html.Small(id="comp-hours", className="text-muted")
                ], className="kpi-card-body")
            ], className="kpi-card kpi-info")
        ], xs=12, sm=6, md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-fire-alt kpi-icon"),
                        html.H6("Tillskottsvärme", className="card-title mb-2"),
                    ], className="d-flex align-items-center"),
                    html.H2(id="aux-runtime", children="-- %", className="mb-1 kpi-value"),
                    html.Small(id="aux-hours", className="text-muted")
                ], className="kpi-card-body")
            ], className="kpi-card kpi-warning")
        ], xs=12, sm=6, md=3),
    ], className="mb-4 kpi-section")


def create_temperature_cards():
    """Skapa huvudtemperaturkort"""
    cards = [
        {
            'id': 'outdoor',
            'icon': 'fa-cloud-sun',
            'title': 'Ute',
            'color': 'temp-outdoor'
        },
        {
            'id': 'indoor',
            'icon': 'fa-home',
            'title': 'Inne',
            'color': 'temp-indoor'
        },
        {
            'id': 'hot-water',
            'icon': 'fa-tint',
            'title': 'Varmvatten',
            'color': 'temp-hot-water'
        },
        {
            'id': 'power',
            'icon': 'fa-bolt',
            'title': 'Effekt',
            'color': 'temp-power'
        },
    ]
    
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className=f"fas {card['icon']} temp-icon"),
                        html.H6(card['title'], className="card-title mb-1"),
                    ], className="d-flex align-items-center mb-2"),
                    html.H3(
                        id=f"{card['id']}-temp" if card['id'] != 'power' else 'power-consumption',
                        children="--°C" if card['id'] != 'power' else "-- W",
                        className="mb-1 temp-value"
                    ),
                    html.Small(
                        id=f"{card['id']}-temp-minmax" if card['id'] != 'power' else 'power-minmax',
                        className="text-muted minmax-text"
                    )
                ], className="temp-card-body")
            ], className=f"temp-card {card['color']}")
        ], xs=12, sm=6, md=3)
        for card in cards
    ], className="mb-3")


def create_secondary_temp_cards():
    """Skapa sekundära temperaturkort (köldbärare och radiatorer)"""
    cards = [
        {'id': 'brine-in', 'title': 'KB In', 'icon': 'fa-snowflake'},
        {'id': 'brine-out', 'title': 'KB Ut', 'icon': 'fa-snowflake'},
        {'id': 'radiator-forward', 'title': 'Fram', 'icon': 'fa-arrow-right'},
        {'id': 'radiator-return', 'title': 'Retur', 'icon': 'fa-arrow-left'},
    ]
    
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className=f"fas {card['icon']} me-2 small-icon"),
                        html.H6(card['title'], className="card-title mb-1 small-title"),
                    ], className="d-flex align-items-center"),
                    html.H4(id=f"{card['id']}-temp", children="--°C", className="mb-1 small-value"),
                    html.Small(id=f"{card['id']}-minmax", className="text-muted minmax-small")
                ], className="py-2 secondary-card-body")
            ], className="secondary-temp-card")
        ], xs=12, sm=6, md=3, xl=2)
        for card in cards
    ], className="mb-4")


def create_status_section():
    """Skapa systemstatussektion"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-info-circle me-2"),
                        html.H6("Systemstatus", className="mb-3 d-inline")
                    ]),
                    html.Div(id="status-indicators", className="status-badges")
                ], className="status-card-body")
            ], className="status-card")
        ])
    ], className="mb-4")


def create_alarm_section():
    """Skapa larmsektion - NYTT!"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        html.H6("Larmstatus", className="mb-3 d-inline")
                    ]),
                    html.Div(id="alarm-status", className="alarm-content")
                ], className="alarm-card-body")
            ], id="alarm-card", className="alarm-card")
        ])
    ], className="mb-4")


def create_event_log_section():
    """Skapa händelselogg - NYTT!"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-list-ul me-2"),
                        html.H5("Senaste Händelser", className="d-inline")
                    ], className="graph-title mb-3"),
                    html.Div(id="event-log", className="event-log-content")
                ], className="event-log-card-body")
            ], className="event-log-card")
        ], md=12)
    ], className="mb-4")


def create_sankey_section():
    """Skapa Sankey energiflödesdiagram - NYTT!"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-project-diagram me-2"),
                        html.H5("Energiflöde", className="d-inline")
                    ], className="graph-title mb-2"),
                    html.P(
                        "Visualisering av energiflödet från mark/luft genom värmepumpen till huset",
                        className="text-muted small mb-3"
                    ),
                    dcc.Graph(id='sankey-diagram', config={'displayModeBar': False})
                ], className="graph-card-body")
            ], className="graph-card sankey-card")
        ])
    ], className="mb-4")


def create_cop_section():
    """Skapa COP och runtime-analyssektion"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-chart-area me-2"),
                        html.H5("COP (Värmefaktor)", className="d-inline")
                    ], className="graph-title"),
                    dcc.Graph(id='cop-graph', config={'displayModeBar': False})
                ], className="graph-card-body")
            ], className="graph-card")
        ], md=8),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-clock me-2"),
                        html.H5("Drifttidsanalys", className="d-inline")
                    ], className="graph-title"),
                    dcc.Graph(id='runtime-pie-chart', config={'displayModeBar': False})
                ], className="graph-card-body")
            ], className="graph-card")
        ], md=4),
    ], className="mb-4")


def create_hot_water_section():
    """Skapa varmvattencykelsektion"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-water me-2"),
                        html.H5("Varmvattencykler", className="d-inline mb-3")
                    ], className="graph-title"),
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.I(className="fas fa-sync-alt hw-icon"),
                                html.H6("Totalt Cykler", className="text-muted mb-2"),
                                html.H3(id="hw-total-cycles", children="--", className="hw-value")
                            ], className="text-center hw-stat")
                        ], md=3),
                        dbc.Col([
                            html.Div([
                                html.I(className="fas fa-calendar-day hw-icon"),
                                html.H6("Cykler/Dag", className="text-muted mb-2"),
                                html.H3(id="hw-cycles-per-day", children="--", className="hw-value")
                            ], className="text-center hw-stat")
                        ], md=3),
                        dbc.Col([
                            html.Div([
                                html.I(className="fas fa-hourglass-half hw-icon"),
                                html.H6("Medel Varaktighet", className="text-muted mb-2"),
                                html.H3(id="hw-avg-duration", children="-- min", className="hw-value")
                            ], className="text-center hw-stat")
                        ], md=3),
                        dbc.Col([
                            html.Div([
                                html.I(className="fas fa-battery-half hw-icon"),
                                html.H6("Medel Energi", className="text-muted mb-2"),
                                html.H3(id="hw-avg-energy", children="-- kWh", className="hw-value")
                            ], className="text-center hw-stat")
                        ], md=3),
                    ], className="mt-3")
                ], className="hw-card-body")
            ], className="hw-card")
        ])
    ], className="mb-4")


def create_temperature_graph():
    """Skapa temperaturtrendgraf"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-thermometer-half me-2"),
                        html.H5("Temperaturtrender", className="d-inline")
                    ], className="graph-title"),
                    dcc.Graph(id='temperature-graph', config={'displayModeBar': False})
                ], className="graph-card-body")
            ], className="graph-card")
        ])
    ], className="mb-4")


def create_performance_graph():
    """Skapa systemprestandagraf"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-tachometer-alt me-2"),
                        html.H5("Systemprestanda", className="d-inline")
                    ], className="graph-title"),
                    dcc.Graph(id='performance-graph', config={'displayModeBar': False})
                ], className="graph-card-body")
            ], className="graph-card")
        ])
    ], className="mb-4")


def create_power_graph():
    """Skapa effektförbrukningsgraf"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-plug me-2"),
                        html.H5("Effektförbrukning & Drifttid", className="d-inline")
                    ], className="graph-title"),
                    dcc.Graph(id='power-graph', config={'displayModeBar': False})
                ], className="graph-card-body")
            ], className="graph-card")
        ])
    ], className="mb-4")


def create_valve_status_graph():
    """Skapa växelventilsstatusgraf för varmvattenproduktion"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-random me-2"),
                        html.H5("Växelventil & Varmvattenproduktion", className="d-inline")
                    ], className="graph-title"),
                    html.P([
                        "Visar när växelventilen slår över till varmvattengenerering ",
                        html.Code("(1 = Varmvatten, 0 = Uppvärmning)"),
                        " och kompressorstatus"
                    ], className="text-muted small mb-3"),
                    dcc.Graph(id='valve-status-graph', config={'displayModeBar': False})
                ], className="graph-card-body")
            ], className="graph-card")
        ])
    ], className="mb-4")


def create_heatpump_schema():
    """Skapa interaktiv värmepumpsschema-visualisering"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-project-diagram me-2"),
                        html.H5("Live Systemschema", className="d-inline")
                    ], className="graph-title"),
                    html.P([
                        "Visar värmepumpens aktuella driftläge med riktiga temperaturvärden och animationer"
                    ], className="text-muted small mb-3"),
                    
                    # Schema-container med relativ positionering
                    html.Div([
                        # Bakgrundsbild
                        html.Img(
                            src='/assets/schema/BV_main2.png',
                            id='schema-background',
                            className='schema-background'
                        ),
                        
                        # Temperaturrutor (positioneras med CSS)
                        html.Div(id='temp-utetemp', className='schema-temp-box temp-outdoor', children='--°C'),
                        html.Div(id='temp-varmvatten', className='schema-temp-box temp-hotwater', children='--°C'),
                        html.Div(id='temp-kb-in', className='schema-temp-box temp-brine-in', children='--°C'),
                        html.Div(id='temp-kb-ut', className='schema-temp-box temp-brine-out', children='--°C'),
                        html.Div(id='temp-framledning', className='schema-temp-box temp-forward', children='--°C'),
                        html.Div(id='temp-radiator-retur', className='schema-temp-box temp-return', children='--°C'),
                        
                        # Animerade komponenter
                        html.Img(
                            src='/assets/schema/BV_komp_anim.png',
                            id='schema-kompressor',
                            className='schema-kompressor',
                            style={'display': 'none'}  # Visas bara när kompressor PÅ
                        ),
                        
                        html.Img(
                            src='/assets/schema/KB-snurr.png',
                            id='schema-kb-pump',
                            className='schema-kb-pump rotating',
                            style={'display': 'none'}  # Visas bara när KB-pump PÅ
                        ),
                        
                        html.Img(
                            src='/assets/schema/VB-snurr.png',
                            id='schema-rad-pump',
                            className='schema-rad-pump rotating',
                            style={'display': 'none'}  # Visas bara när radiatorpump PÅ
                        ),
                        
                        html.Img(
                            src='/assets/schema/3kw-off.png',
                            id='schema-3kw',
                            className='schema-3kw'
                        ),
                        
                        html.Img(
                            src='/assets/schema/RAD-hot.png',
                            id='schema-radiator',
                            className='schema-radiator',
                            style={'display': 'none'}  # Visas när radiator varm
                        ),
                        
                        html.Img(
                            src='/assets/schema/RAD-pil.png',
                            id='schema-valve-arrow',
                            className='schema-valve-arrow'
                        ),
                        
                    ], className='schema-container', id='schema-container')
                ], className="graph-card-body")
            ], className="graph-card")
        ])
    ], className="mb-4")


