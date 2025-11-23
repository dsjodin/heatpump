"""
Thermia Dashboard - Graf Callbacks
Hanterar alla grafer och visualiseringar
"""

import logging
from dash import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from config_colors import THERMIA_COLORS, LINE_WIDTH_NORMAL, LINE_WIDTH_THICK, LINE_WIDTH_THIN

logger = logging.getLogger(__name__)


def register_graph_callbacks(app, data_query):
    """Registrera alla graf-relaterade callbacks"""
    
    # ==================== NYTT: Sankey Energiflödesdiagram ====================
    @app.callback(
        Output('sankey-diagram', 'figure'),
        [Input('interval-component', 'n_intervals'),
         Input('time-range-dropdown', 'value')]
    )
    def update_sankey_diagram(n, time_range):
        """
        Uppdatera Sankey energiflödesdiagram
        
        Visar energiflöden:
        - Markenergi (blå) → Värmepump (grön)
        - Elkraft (gul) → Värmepump (grön)
        - Tillsattsvärme (röd) → Hus (orange) [om aktiv]
        - Värmepump (grön) → Hus (orange)
        """
        try:
            # Hämta COP-data
            cop_df = data_query.calculate_cop(time_range)
            runtime_stats = data_query.calculate_runtime_stats(time_range)
            
            # Standardvärden om ingen data
            if cop_df.empty or 'estimated_cop' not in cop_df.columns:
                avg_cop = 3.0
                has_data = False
            else:
                avg_cop = cop_df['estimated_cop'].mean()
                has_data = True
            
            # Säkerställ rimligt COP-värde
            if pd.isna(avg_cop) or avg_cop < 1.5 or avg_cop > 6.0:
                avg_cop = 3.0
            
            # Beräkna energiflöden (normaliserade till 100 enheter elkraft)
            electric_power = 100  # Baseline
            
            # Markenergi baserat på COP: Qmark = Qel * (COP - 1)
            ground_energy = electric_power * (avg_cop - 1)
            
            # Tillsattsvärme (om aktiv)
            aux_heater_percent = runtime_stats.get('aux_heater_runtime_percent', 0)
            aux_heater_power = (aux_heater_percent / 100) * 50 if aux_heater_percent > 0 else 0
            
            # Total värmeenergi: Qtot = Qel + Qmark + Qtillsats
            total_heat = electric_power + ground_energy + aux_heater_power
            
            # Beräkna gratis energi från marken
            free_energy_percent = (ground_energy / total_heat * 100) if total_heat > 0 else 0
            
            # Bygg Sankey-diagram
            # Noder: 0=Mark, 1=Elkraft, 2=Värmepump, 3=Hus, 4=Tillsats (om aktiv)
            node_labels = [
                "🌍 Markenergi",
                "⚡ Elkraft",
                "🔄 Värmepump",
                "🏠 Värme till Hus"
            ]
            
            node_colors = [
                'rgba(0, 212, 255, 0.8)',    # Cyan - Mark (kallt)
                'rgba(255, 215, 0, 0.8)',     # Gul - Elkraft
                'rgba(76, 175, 80, 0.8)',     # Grön - Värmepump
                'rgba(255, 152, 0, 0.8)'      # Orange - Hus (varmt)
            ]
            
            # Länkar (flöden)
            sources = []
            targets = []
            values = []
            link_colors = []
            link_labels = []
            
            # Mark → Värmepump
            sources.append(0)
            targets.append(2)
            values.append(ground_energy)
            link_colors.append('rgba(0, 212, 255, 0.4)')
            link_labels.append(f'{ground_energy:.0f} ({free_energy_percent:.0f}% gratis)')
            
            # Elkraft → Värmepump
            sources.append(1)
            targets.append(2)
            values.append(electric_power)
            link_colors.append('rgba(255, 215, 0, 0.4)')
            link_labels.append(f'{electric_power:.0f}')
            
            # Om tillsattsvärme är aktiv
            if aux_heater_power > 5:  # Bara visa om > 5 enheter
                node_labels.append("🔥 Tillsattsvärme")
                node_colors.append('rgba(231, 76, 60, 0.8)')  # Röd
                
                # Tillsats → Hus
                sources.append(4)
                targets.append(3)
                values.append(aux_heater_power)
                link_colors.append('rgba(231, 76, 60, 0.4)')
                link_labels.append(f'{aux_heater_power:.0f}')
                
                # Värmepump → Hus (minus tillsats)
                heat_from_hp = total_heat - aux_heater_power
            else:
                heat_from_hp = total_heat
            
            # Värmepump → Hus
            sources.append(2)
            targets.append(3)
            values.append(heat_from_hp)
            link_colors.append('rgba(255, 152, 0, 0.4)')
            link_labels.append(f'{heat_from_hp:.0f}')
            
            # Skapa Sankey
            fig = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=20,
                    thickness=30,
                    line=dict(color="white", width=2),
                    label=node_labels,
                    color=node_colors,
                    customdata=[f"Energi: {v:.0f}" for v in [ground_energy, electric_power, total_heat, total_heat]],
                    hovertemplate='%{label}<br>%{customdata}<extra></extra>'
                ),
                link=dict(
                    source=sources,
                    target=targets,
                    value=values,
                    color=link_colors,
                    customdata=link_labels,
                    hovertemplate='%{source.label} → %{target.label}<br>Energi: %{customdata}<extra></extra>'
                )
            )])
            
            # Layout
            title_text = f"Energiflöde (COP: {avg_cop:.2f}, {free_energy_percent:.0f}% gratis från mark)"
            if not has_data:
                title_text += " - Estimerat (ingen data)"
            
            fig.update_layout(
                title=dict(
                    text=title_text,
                    font=dict(size=14, color="gray")
                ),
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=10, r=10, t=50, b=10),
                font=dict(size=11, color="gray"),
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating Sankey diagram: {e}")
            # Returnera tom figur vid fel
            return go.Figure().update_layout(
                title="Energiflöde - Data ej tillgänglig",
                height=400
            )
    
    
    # ==================== COP-graf ====================
    @app.callback(
        Output('cop-graph', 'figure'),
        [Input('interval-component', 'n_intervals'),
         Input('time-range-dropdown', 'value')]
    )
    def update_cop_graph(n, time_range):
        """Uppdatera COP-graf"""
        cop_df = data_query.calculate_cop(time_range)
        
        fig = go.Figure()
        
        if not cop_df.empty and 'estimated_cop' in cop_df.columns:
            fig.add_trace(go.Scatter(
                x=cop_df['_time'],
                y=cop_df['estimated_cop'],
                mode='lines',
                name='COP',
                line=dict(color=THERMIA_COLORS['cop'], width=LINE_WIDTH_THICK),
                fill='tozeroy',
                fillcolor='rgba(76, 175, 80, 0.2)'
            ))
            
            # Lägg till genomsnittslinje
            avg_cop = cop_df['estimated_cop'].mean()
            fig.add_hline(
                y=avg_cop,
                line_dash="dash",
                line_color=THERMIA_COLORS['cop_avg'],
                annotation_text=f"Medel: {avg_cop:.2f}",
                annotation_position="right"
            )
        
        fig.update_layout(
            xaxis_title="Tid",
            yaxis_title="COP (Värmefaktor)",
            hovermode='x unified',
            height=350,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=40, r=40, t=20, b=40),
            yaxis=dict(range=[0, 6])
        )
        
        return fig
    
    
    # ==================== Runtime cirkeldiagram ====================
    @app.callback(
        Output('runtime-pie-chart', 'figure'),
        [Input('interval-component', 'n_intervals'),
         Input('time-range-dropdown', 'value')]
    )
    def update_runtime_pie(n, time_range):
        """Uppdatera runtime-cirkeldiagram"""
        runtime = data_query.calculate_runtime_stats(time_range)
        
        labels = ['Kompressor', 'Tillsats', 'Inaktiv']
        values = [
            runtime['compressor_runtime_percent'],
            runtime['aux_heater_runtime_percent'],
            100 - runtime['compressor_runtime_percent'] - runtime['aux_heater_runtime_percent']
        ]
        colors = [THERMIA_COLORS['compressor'], THERMIA_COLORS['aux_heater'], '#e9ecef']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker=dict(colors=colors),
            textinfo='label+percent',
            textposition='outside'
        )])
        
        fig.update_layout(
            showlegend=False,
            height=350,
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=20, b=20)
        )
        
        return fig
    
    
    # ==================== Temperaturgraf - FÖRBÄTTRAD FÄRGSÄTTNING ====================
    @app.callback(
        Output('temperature-graph', 'figure'),
        [Input('interval-component', 'n_intervals'),
         Input('time-range-dropdown', 'value')]
    )
    def update_temperature_graph(n, time_range):
        """Uppdatera temperaturgraf med förbättrad färgsättning"""
        metrics = [
            'outdoor_temp',
            'indoor_temp',
            'radiator_forward',
            'radiator_return',
            'hot_water_top',
            'brine_in_evaporator',
            'brine_out_condenser'
        ]
        
        df = data_query.query_metrics(metrics, time_range)
        
        fig = go.Figure()
        
        # Svenska namn - ordning för legend
        display_names = {
            'outdoor_temp': 'Ute',
            'indoor_temp': 'Inne',
            'hot_water_top': 'Varmvatten',
            'radiator_forward': 'Radiator Fram ↑',
            'radiator_return': 'Radiator Retur ↓',
            'brine_in_evaporator': 'KB In →',
            'brine_out_condenser': 'KB Ut ←'
        }
        
        # Ordning för att lägga till traces (påverkar legend)
        metric_order = [
            'hot_water_top',
            'radiator_forward',
            'radiator_return',
            'indoor_temp',
            'outdoor_temp',
            'brine_in_evaporator',
            'brine_out_condenser'
        ]
        
        if not df.empty:
            for name in metric_order:
                if name in df['name'].unique():
                    metric_df = df[df['name'] == name]
                    fig.add_trace(go.Scatter(
                        x=metric_df['_time'],
                        y=metric_df['_value'],
                        mode='lines',
                        name=display_names.get(name, name),
                        line=dict(width=LINE_WIDTH_NORMAL, color=THERMIA_COLORS.get(name, '#6c757d'))
                    ))
        
        fig.update_layout(
            xaxis_title="Tid",
            yaxis_title="Temperatur (°C)",
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=11)
            ),
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=40, r=40, t=20, b=40)
        )
        
        return fig
    
    
    # ==================== Prestandagraf - FÖRBÄTTRAD FÄRGSÄTTNING ====================
    @app.callback(
        Output('performance-graph', 'figure'),
        [Input('interval-component', 'n_intervals'),
         Input('time-range-dropdown', 'value')]
    )
    def update_performance_graph(n, time_range):
        """Uppdatera systemprestandagraf med förbättrad färgsättning"""
        metrics = [
            'brine_in_evaporator',
            'brine_out_condenser',
            'radiator_forward',
            'radiator_return',
            'compressor_status'
        ]
        
        df = data_query.query_metrics(metrics, time_range)
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Temperaturdifferenser', 'Kompressor Drifttid'),
            vertical_spacing=0.15,
            row_heights=[0.6, 0.4]
        )
        
        if not df.empty:
            brine_in = df[df['name'] == 'brine_in_evaporator']
            brine_out = df[df['name'] == 'brine_out_condenser']
            rad_forward = df[df['name'] == 'radiator_forward']
            rad_return = df[df['name'] == 'radiator_return']
            
            if not brine_in.empty and not brine_out.empty:
                brine_delta = pd.merge(
                    brine_in[['_time', '_value']],
                    brine_out[['_time', '_value']],
                    on='_time',
                    suffixes=('_in', '_out')
                )
                brine_delta['delta'] = brine_delta['_value_in'] - brine_delta['_value_out']
                
                fig.add_trace(
                    go.Scatter(
                        x=brine_delta['_time'],
                        y=brine_delta['delta'],
                        mode='lines',
                        name='KB ΔT',
                        line=dict(color=THERMIA_COLORS['delta_brine'], width=LINE_WIDTH_NORMAL)
                    ),
                    row=1, col=1
                )
            
            if not rad_forward.empty and not rad_return.empty:
                rad_delta = pd.merge(
                    rad_forward[['_time', '_value']],
                    rad_return[['_time', '_value']],
                    on='_time',
                    suffixes=('_fwd', '_ret')
                )
                rad_delta['delta'] = rad_delta['_value_fwd'] - rad_delta['_value_ret']
                
                fig.add_trace(
                    go.Scatter(
                        x=rad_delta['_time'],
                        y=rad_delta['delta'],
                        mode='lines',
                        name='Radiator ΔT',
                        line=dict(color=THERMIA_COLORS['delta_radiator'], width=LINE_WIDTH_NORMAL)
                    ),
                    row=1, col=1
                )
            
            comp = df[df['name'] == 'compressor_status']
            if not comp.empty:
                fig.add_trace(
                    go.Scatter(
                        x=comp['_time'],
                        y=comp['_value'],
                        mode='lines',
                        name='Kompressor',
                        fill='tozeroy',
                        fillcolor='rgba(76, 175, 80, 0.3)',
                        line=dict(color=THERMIA_COLORS['compressor'], width=LINE_WIDTH_NORMAL)
                    ),
                    row=2, col=1
                )
        
        fig.update_xaxes(title_text="Tid", row=2, col=1)
        fig.update_yaxes(title_text="ΔT (°C)", row=1, col=1)
        fig.update_yaxes(title_text="Status", row=2, col=1)
        
        fig.update_layout(
            height=600,
            hovermode='x unified',
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    
    # ==================== Effektgraf - FÖRBÄTTRAD FÄRGSÄTTNING ====================
    @app.callback(
        Output('power-graph', 'figure'),
        [Input('interval-component', 'n_intervals'),
         Input('time-range-dropdown', 'value')]
    )
    def update_power_graph(n, time_range):
        """Uppdatera effektförbrukningsgraf med förbättrad färgsättning"""
        metrics = [
            'power_consumption',
            'compressor_status',
            'additional_heat_percent'
        ]
        
        df = data_query.query_metrics(metrics, time_range)
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Effektförbrukning', 'Systemstatus'),
            vertical_spacing=0.15,
            specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
        )
        
        if not df.empty:
            power = df[df['name'] == 'power_consumption']
            if not power.empty:
                fig.add_trace(
                    go.Scatter(
                        x=power['_time'],
                        y=power['_value'],
                        mode='lines',
                        name='Effekt',
                        line=dict(color=THERMIA_COLORS['power'], width=LINE_WIDTH_NORMAL),
                        fill='tozeroy',
                        fillcolor='rgba(155, 89, 182, 0.2)'
                    ),
                    row=1, col=1
                )
            
            comp = df[df['name'] == 'compressor_status']
            if not comp.empty:
                fig.add_trace(
                    go.Scatter(
                        x=comp['_time'],
                        y=comp['_value'],
                        mode='lines',
                        name='Kompressor',
                        line=dict(color=THERMIA_COLORS['compressor'], width=LINE_WIDTH_NORMAL)
                    ),
                    row=2, col=1
                )
            
            heater = df[df['name'] == 'additional_heat_percent']
            if not heater.empty:
                fig.add_trace(
                    go.Scatter(
                        x=heater['_time'],
                        y=heater['_value'],
                        mode='lines',
                        name='Tillsats %',
                        line=dict(color=THERMIA_COLORS['aux_heater'], width=LINE_WIDTH_NORMAL)
                    ),
                    row=2, col=1
                )
        
        fig.update_xaxes(title_text="Tid", row=2, col=1)
        fig.update_yaxes(title_text="Effekt (W)", row=1, col=1)
        fig.update_yaxes(title_text="Status / %", row=2, col=1)
        
        fig.update_layout(
            height=600,
            hovermode='x unified',
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    
    # ==================== NYTT: Växelventilsgraf ====================
    @app.callback(
        Output('valve-status-graph', 'figure'),
        [Input('interval-component', 'n_intervals'),
         Input('time-range-dropdown', 'value')]
    )
    def update_valve_status_graph(n, time_range):
        """
        Uppdatera växelventilsstatusgraf för att analysera varmvattenproduktion
        
        Visar:
        - Växelventilens läge (0=uppvärmning, 1=varmvatten)
        - Kompressorstatus (för att se aktiv produktion)
        - Varmvattentemperatur (för att se temperaturökning)
        """
        metrics = [
            'switch_valve_status',      # Växelventil
            'compressor_status',         # Kompressor
            'hot_water_top'             # Varmvattentemperatur
        ]
        
        df = data_query.query_metrics(metrics, time_range)
        
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=(
                'Växelventilsläge (1=Varmvatten, 0=Uppvärmning)',
                'Kompressorstatus (1=PÅ, 0=AV)', 
                'Varmvattentemperatur (°C)'
            ),
            vertical_spacing=0.12,
            specs=[[{"secondary_y": False}], [{"secondary_y": False}], [{"secondary_y": False}]]
        )
        
        if not df.empty:
            # Växelventil
            valve = df[df['name'] == 'switch_valve_status']
            if not valve.empty:
                fig.add_trace(
                    go.Scatter(
                        x=valve['_time'],
                        y=valve['_value'],
                        mode='lines',
                        name='Växelventil',
                        line=dict(color='#ff9800', width=3),  # Orange
                        fill='tozeroy',
                        fillcolor='rgba(255, 152, 0, 0.3)'
                    ),
                    row=1, col=1
                )
            
            # Kompressor
            comp = df[df['name'] == 'compressor_status']
            if not comp.empty:
                fig.add_trace(
                    go.Scatter(
                        x=comp['_time'],
                        y=comp['_value'],
                        mode='lines',
                        name='Kompressor',
                        line=dict(color=THERMIA_COLORS['compressor'], width=LINE_WIDTH_NORMAL),
                        fill='tozeroy',
                        fillcolor='rgba(76, 175, 80, 0.2)'
                    ),
                    row=2, col=1
                )
            
            # Varmvattentemperatur
            hw_temp = df[df['name'] == 'hot_water_top']
            if not hw_temp.empty:
                fig.add_trace(
                    go.Scatter(
                        x=hw_temp['_time'],
                        y=hw_temp['_value'],
                        mode='lines',
                        name='VV Temp',
                        line=dict(color=THERMIA_COLORS['hot_water_top'], width=LINE_WIDTH_NORMAL)
                    ),
                    row=3, col=1
                )
        
        # Uppdatera axlar
        fig.update_xaxes(title_text="Tid", row=3, col=1)
        fig.update_yaxes(title_text="Status", row=1, col=1, range=[-0.1, 1.1])
        fig.update_yaxes(title_text="Status", row=2, col=1, range=[-0.1, 1.1])
        fig.update_yaxes(title_text="Temperatur (°C)", row=3, col=1)
        
        fig.update_layout(
            height=700,
            hovermode='x unified',
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig

