"""
Heat Pump Dashboard Layout - Multi-Brand Support
Imports components and creates complete dashboard (Hybrid: Common + Brand-Specific)
"""

import sys
import os
from dash import dcc, html
import dash_bootstrap_components as dbc

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importera alla UI-komponenter
from layout_components import (
    create_header,
    create_topbar_quickstats,
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
    create_heatpump_schema
)


def create_layout(provider=None):
    """
    Create complete dashboard layout with tab-based organization and sticky topbar

    Args:
        provider: Heat pump provider instance (Thermia, IVT, etc.)

    Returns:
        Dash layout component
    """
    # Import brand-specific components if provider is set
    brand_specific_section = None
    if provider:
        brand_name = provider.get_brand_name()
        if brand_name == 'thermia':
            from providers.thermia.dashboard_components import create_thermia_specific_section
            brand_specific_section = create_thermia_specific_section()
        elif brand_name == 'ivt':
            from providers.ivt.dashboard_components import create_ivt_specific_section
            brand_specific_section = create_ivt_specific_section()
        elif brand_name == 'nibe':
            from providers.nibe.dashboard_components import create_nibe_specific_section
            brand_specific_section = create_nibe_specific_section()

    # TAB 0: LIVE VY
    tab_live = dbc.Tab(
        label="🔴 Live Vy",
        tab_id="tab-live",
        children=[
            dbc.Container([
                # Live Systemschema
                create_heatpump_schema(),
            ], fluid=True, className="tab-content-container")
        ]
    )

    # TAB 1: ÖVERSIKT (KPI + Status + Energiflöde)
    tab_oversikt = dbc.Tab(
        label="📊 Översikt",
        tab_id="tab-oversikt",
        children=[
            dbc.Container([
                # KPI-kort
                create_kpi_cards(),

                # Status & Larm
                create_status_section(),
                create_alarm_section(),

                # Sankey Energiflöde (visuell översikt)
                create_sankey_section(),
            ], fluid=True, className="tab-content-container")
        ]
    )

    # TAB 2: TEMPERATURER (Alla temperaturkort + grafer)
    tab_temp = dbc.Tab(
        label="🌡️ Temperaturer",
        tab_id="tab-temp",
        children=[
            dbc.Container([
                # Alla temperaturkort
                create_temperature_cards(),
                create_secondary_temp_cards(),

                # Temperaturgrafer
                create_temperature_graph(),
            ], fluid=True, className="tab-content-container")
        ]
    )

    # TAB 3: ENERGI & PRESTANDA (COP, Effekt, Varmvatten, Prestanda)
    tab_energi_components = [
        dbc.Container([
            # COP & Runtime
            create_cop_section(),

            # Systemprestanda
            create_performance_graph(),

            # Effektförbrukning
            create_power_graph(),

            # Växelventil & Varmvatten
            create_valve_status_graph(),

            # Varmvattencykler
            create_hot_water_section(),
        ], fluid=True, className="tab-content-container")
    ]

    # Add brand-specific section if available
    if brand_specific_section:
        tab_energi_components[0].children.append(brand_specific_section)

    tab_energi = dbc.Tab(
        label="⚡ Energi & Prestanda",
        tab_id="tab-energi",
        children=tab_energi_components
    )

    # TAB 5: HÄNDELSER
    tab_handelser = dbc.Tab(
        label="📋 Händelser",
        tab_id="tab-handelser",
        children=[
            dbc.Container([
                # Larmstatus
                create_alarm_section(),

                # Händelselogg
                create_event_log_section(),
            ], fluid=True, className="tab-content-container")
        ]
    )

    # Build complete layout
    layout = dbc.Container([
        # Header
        create_header(),

        # Sticky Topbar med Quick Stats
        create_topbar_quickstats(),

        # Kontroller (tid & pris)
        create_controls(),

        # Tabs
        dbc.Tabs(
            id="main-tabs",
            active_tab="tab-live",
            children=[
                tab_live,
                tab_oversikt,
                tab_temp,
                tab_energi,
                tab_handelser,
            ],
            className="mb-3 custom-tabs"
        ),

        # Auto-uppdateringsintervall
        dcc.Interval(
            id='interval-component',
            interval=30*1000,  # 30 sekunder
            n_intervals=0
        )
    ], fluid=True, className="dashboard-container")

    return layout
