"""
Thermia Dashboard Layout - HUVUDLAYOUT
Importerar komponenter och sätter ihop komplett dashboard
"""

from dash import dcc
import dash_bootstrap_components as dbc

# Importera alla UI-komponenter
from layout_components import (
    create_header,
    create_controls,
    create_kpi_cards,
    create_temperature_cards,
    create_secondary_temp_cards,
    create_status_section,
    create_alarm_section,
    create_event_log_section,
    create_sankey_section,
    create_cop_section,
    create_hot_water_section,
    create_temperature_graph,
    create_performance_graph,
    create_power_graph,
    create_valve_status_graph,
    create_heatpump_schema  # NYTT: Schemavisualisering
)


def create_layout():
    """Skapa komplett dashboard-layout"""
    return dbc.Container([
        # Header
        create_header(),
        
        # Kontroller
        create_controls(),
        
        # KPI-kort
        create_kpi_cards(),
        
        # Temperaturkort
        create_temperature_cards(),
        create_secondary_temp_cards(),
        
        # Status
        create_status_section(),
        
        # Larmstatus
        create_alarm_section(),
        
        # Händelselogg
        create_event_log_section(),
        
        # Sankey Energiflöde
        create_sankey_section(),
        
        # NYTT: Live Systemschema
        create_heatpump_schema(),
        
        # COP & Runtime
        create_cop_section(),
        
        # Varmvattencykler
        create_hot_water_section(),
        
        # Grafer
        create_temperature_graph(),
        create_performance_graph(),
        create_power_graph(),
        create_valve_status_graph(),
        
        # Auto-uppdateringsintervall
        dcc.Interval(
            id='interval-component',
            interval=30*1000,  # 30 sekunder
            n_intervals=0
        )
    ], fluid=True, className="dashboard-container")
