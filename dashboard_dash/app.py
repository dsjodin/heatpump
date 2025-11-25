#!/usr/bin/env python3
"""
Heat Pump Dashboard - Multi-Brand Support
Modular structure with separated callbacks and layout components
Supports: Thermia, IVT
"""

import os
import sys
import logging
import yaml
from dash import Dash
import dash_bootstrap_components as dbc

# Add parent directory to path for provider imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from providers import get_provider
from data_query import HeatPumpDataQuery
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
        logger.info(f"Loaded provider: {provider.get_display_name()}")
        return provider
    except Exception as e:
        logger.error(f"Failed to load provider: {e}, defaulting to Thermia")
        from providers.thermia.provider import ThermiaProvider
        return ThermiaProvider()


# Load provider
provider = load_provider()

# Initiera Dash-app med Bootstrap-tema
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title=provider.get_dashboard_title(),
    suppress_callback_exceptions=True
)

# Fixa UTF-8 encoding för svenska tecken
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Initiera datafrågor
data_query = HeatPumpDataQuery()

# Sätt layout (passes provider for brand-specific components)
app.layout = create_layout(provider)

# Registrera alla callbacks från separata moduler
logger.info("Registrerar status callbacks...")
register_status_callbacks(app, data_query)

logger.info("Registrerar KPI callbacks...")
register_kpi_callbacks(app, data_query)

logger.info("Registrerar graf callbacks...")
register_graph_callbacks(app, data_query)

# Registrera märkesspecifika callbacks
brand_name = provider.get_brand_name()
if brand_name == 'thermia':
    logger.info("Registrerar Thermia-specifika callbacks...")
    from providers.thermia.callbacks import register_thermia_callbacks
    register_thermia_callbacks(app, data_query)
elif brand_name == 'ivt':
    logger.info("Registrerar IVT-specifika callbacks...")
    from providers.ivt.callbacks import register_ivt_callbacks
    register_ivt_callbacks(app, data_query)
elif brand_name == 'nibe':
    logger.info("Registrerar NIBE-specifika callbacks...")
    from providers.nibe.callbacks import register_nibe_callbacks
    register_nibe_callbacks(app, data_query)

# Server för deployment
server = app.server


if __name__ == '__main__':
    logger.info(f"🔥 Startar {provider.get_display_name()} Dashboard...")
    logger.info("📊 Svensk version med Sankey energiflödesdiagram")
    logger.info("📦 Modulär struktur:")
    logger.info("   - callbacks_status.py (larm & händelser)")
    logger.info("   - callbacks_kpi.py (KPI-kort)")
    logger.info("   - callbacks_graphs.py (alla grafer)")
    logger.info("   - layout_components.py (UI-komponenter)")
    logger.info("   - config_colors.py (färgpalett)")
    logger.info(f"   - providers/{provider.get_brand_name()}/ (märkesspecifik)")
    logger.info("🌐 Dashboard kommer vara tillgänglig på http://localhost:8050")
    app.run_server(host='0.0.0.0', port=8050, debug=False)
