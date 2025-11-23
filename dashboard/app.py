#!/usr/bin/env python3
"""
Thermia Heat Pump Dashboard - SVENSK VERSION MED SANKEY
Modulär struktur med separerade callbacks och layout-komponenter
"""

import logging
from dash import Dash
import dash_bootstrap_components as dbc

from data_query import ThermiaDataQuery
from layout import create_layout

# Importera alla callback-moduler
from callbacks_status import register_status_callbacks
from callbacks_kpi import register_kpi_callbacks
from callbacks_graphs import register_graph_callbacks

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initiera Dash-app med Bootstrap-tema
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Thermia Värmepump Monitor",
    suppress_callback_exceptions=True
)

# Initiera datafrågor
data_query = ThermiaDataQuery()

# Sätt layout
app.layout = create_layout()

# Registrera alla callbacks från separata moduler
logger.info("Registrerar status callbacks...")
register_status_callbacks(app, data_query)

logger.info("Registrerar KPI callbacks...")
register_kpi_callbacks(app, data_query)

logger.info("Registrerar graf callbacks...")
register_graph_callbacks(app, data_query)

# Server för deployment
server = app.server


if __name__ == '__main__':
    logger.info("🔥 Startar Thermia Värmepump Dashboard...")
    logger.info("📊 Svensk version med Sankey energiflödesdiagram")
    logger.info("📦 Modulär struktur:")
    logger.info("   - callbacks_status.py (larm & händelser)")
    logger.info("   - callbacks_kpi.py (KPI-kort)")
    logger.info("   - callbacks_graphs.py (alla grafer)")
    logger.info("   - layout_components.py (UI-komponenter)")
    logger.info("   - config_colors.py (färgpalett)")
    logger.info("🌐 Dashboard kommer vara tillgänglig på http://localhost:8050")
    app.run_server(host='0.0.0.0', port=8050, debug=False)
