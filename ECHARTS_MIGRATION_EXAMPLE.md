# ECharts Migration Example: COP Graph

## Original Plotly Implementation

```python
# callbacks_graphs.py (lines 179-223)
def update_cop_graph(n, time_range):
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
```

## ECharts Equivalent (Using dash-echarts)

### 1. Install Package
```bash
pip install dash-echarts
```

### 2. Update requirements.txt
```txt
dash==2.14.2
# plotly==5.18.0  # Remove or comment out
dash-echarts==0.1.0  # Add this
dash-bootstrap-components==1.5.0
influxdb-client==1.38.0
pandas==2.1.4
PyYAML==6.0.1
```

### 3. Update layout_components.py
```python
# Old import
from dash import dcc, html

# New import
from dash import html
from dash_echarts import DashECharts

# Old component
dcc.Graph(id='cop-graph', config={'displayModeBar': False})

# New component
DashECharts(
    id='cop-graph',
    style={'height': '350px'},
    option={}  # Will be populated by callback
)
```

### 4. Update callbacks_graphs.py
```python
@app.callback(
    Output('cop-graph', 'option'),  # Changed from 'figure' to 'option'
    [Input('interval-component', 'n_intervals'),
     Input('time-range-dropdown', 'value')]
)
def update_cop_graph(n, time_range):
    """Uppdatera COP-graf med ECharts"""
    cop_df = data_query.calculate_cop(time_range)

    # Prepare data
    if cop_df.empty or 'estimated_cop' not in cop_df.columns:
        return {
            'title': {'text': 'Ingen data tillgänglig'},
            'xAxis': {'type': 'time'},
            'yAxis': {'type': 'value'}
        }

    # Convert timestamps to ISO format for ECharts
    data_points = [
        [row['_time'].isoformat(), row['estimated_cop']]
        for _, row in cop_df.iterrows()
    ]

    # Calculate average
    avg_cop = cop_df['estimated_cop'].mean()

    # ECharts option configuration
    option = {
        'grid': {
            'left': 40,
            'right': 40,
            'top': 20,
            'bottom': 40,
            'backgroundColor': 'transparent'
        },
        'xAxis': {
            'type': 'time',
            'name': 'Tid',
            'nameLocation': 'middle',
            'nameGap': 30,
            'axisLine': {'lineStyle': {'color': '#999'}},
        },
        'yAxis': {
            'type': 'value',
            'name': 'COP (Värmefaktor)',
            'min': 0,
            'max': 6,
            'axisLine': {'lineStyle': {'color': '#999'}},
        },
        'series': [
            {
                'type': 'line',
                'name': 'COP',
                'data': data_points,
                'smooth': True,
                'lineStyle': {
                    'color': THERMIA_COLORS['cop'],
                    'width': LINE_WIDTH_THICK
                },
                'areaStyle': {
                    'color': 'rgba(76, 175, 80, 0.2)'
                },
                'emphasis': {
                    'focus': 'series'
                }
            }
        ],
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {
                'type': 'cross',
                'label': {
                    'backgroundColor': '#6a7985'
                }
            }
        },
        # Add average line using markLine
        'series': [
            {
                'type': 'line',
                'name': 'COP',
                'data': data_points,
                'smooth': True,
                'lineStyle': {
                    'color': THERMIA_COLORS['cop'],
                    'width': LINE_WIDTH_THICK
                },
                'areaStyle': {
                    'color': 'rgba(76, 175, 80, 0.2)'
                },
                'markLine': {
                    'silent': False,
                    'lineStyle': {
                        'type': 'dashed',
                        'color': THERMIA_COLORS['cop_avg']
                    },
                    'data': [
                        {
                            'yAxis': avg_cop,
                            'name': f'Medel: {avg_cop:.2f}',
                            'label': {
                                'position': 'end',
                                'formatter': f'Medel: {avg_cop:.2f}'
                            }
                        }
                    ]
                }
            }
        ],
        'backgroundColor': 'transparent'
    }

    return option
```

---

## Key Differences: Plotly vs ECharts

| Feature | Plotly | ECharts | Notes |
|---------|--------|---------|-------|
| **Data Format** | Direct arrays | Array of `[x, y]` pairs | ECharts requires paired data |
| **Time Axis** | Auto-detects datetime | Use `type: 'time'` + ISO strings | Must convert timestamps |
| **Area Fill** | `fill='tozeroy'` | `areaStyle: {}` | Similar effect |
| **Horizontal Line** | `fig.add_hline()` | `markLine` in series | Different approach |
| **Layout** | `fig.update_layout()` | Top-level `option` dict | Structure change |
| **Hover Mode** | `hovermode='x unified'` | `tooltip: {trigger: 'axis'}` | Similar UX |
| **Colors** | RGB/RGBA strings | RGB/RGBA strings | Same format ✅ |
| **Transparency** | `rgba(0,0,0,0)` | `'transparent'` | Both work |

---

## More Complex Example: Temperature Graph (Multi-line)

```python
def update_temperature_graph(n, time_range):
    """Uppdatera temperaturgraf med ECharts"""
    metrics = [
        'outdoor_temp', 'indoor_temp', 'radiator_forward',
        'radiator_return', 'hot_water_top',
        'brine_in_evaporator', 'brine_out_condenser'
    ]

    df = data_query.query_metrics(metrics, time_range)

    display_names = {
        'outdoor_temp': 'Ute',
        'indoor_temp': 'Inne',
        'hot_water_top': 'Varmvatten',
        'radiator_forward': 'Radiator Fram ↑',
        'radiator_return': 'Radiator Retur ↓',
        'brine_in_evaporator': 'KB In →',
        'brine_out_condenser': 'KB Ut ←'
    }

    # Build series for each metric
    series = []
    legend_data = []

    if not df.empty:
        for name in ['hot_water_top', 'radiator_forward', 'radiator_return',
                     'indoor_temp', 'outdoor_temp',
                     'brine_in_evaporator', 'brine_out_condenser']:
            if name in df['name'].unique():
                metric_df = df[df['name'] == name]
                data_points = [
                    [row['_time'].isoformat(), row['_value']]
                    for _, row in metric_df.iterrows()
                ]

                display_name = display_names.get(name, name)
                legend_data.append(display_name)

                series.append({
                    'type': 'line',
                    'name': display_name,
                    'data': data_points,
                    'smooth': True,
                    'lineStyle': {
                        'color': THERMIA_COLORS.get(name, '#6c757d'),
                        'width': LINE_WIDTH_NORMAL
                    },
                    'emphasis': {
                        'focus': 'series'
                    }
                })

    option = {
        'grid': {
            'left': 40,
            'right': 40,
            'top': 60,  # Space for legend
            'bottom': 40,
            'backgroundColor': 'transparent'
        },
        'legend': {
            'data': legend_data,
            'top': 10,
            'right': 10,
            'orient': 'horizontal',
            'textStyle': {'fontSize': 11}
        },
        'xAxis': {
            'type': 'time',
            'name': 'Tid',
            'nameLocation': 'middle',
            'nameGap': 30,
            'axisLine': {'lineStyle': {'color': '#999'}},
        },
        'yAxis': {
            'type': 'value',
            'name': 'Temperatur (°C)',
            'axisLine': {'lineStyle': {'color': '#999'}},
        },
        'series': series,
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {
                'type': 'cross',
                'animation': False,
                'label': {
                    'backgroundColor': '#6a7985'
                }
            }
        },
        'backgroundColor': 'transparent'
    }

    return option
```

---

## Sankey Diagram Migration

**Good News:** ECharts has excellent Sankey support!

```python
def update_sankey_diagram(n, time_range):
    """Sankey med ECharts - mycket lik Plotly!"""
    # ... existing calculation logic ...

    # Build nodes
    nodes = [
        {'name': '🌍 Markenergi'},
        {'name': '⚡ Elkraft'},
        {'name': '🔄 Värmepump'},
        {'name': '🏠 Värme till Hus'}
    ]

    # Build links
    links = [
        {
            'source': '🌍 Markenergi',
            'target': '🔄 Värmepump',
            'value': ground_energy
        },
        {
            'source': '⚡ Elkraft',
            'target': '🔄 Värmepump',
            'value': electric_power
        },
        {
            'source': '🔄 Värmepump',
            'target': '🏠 Värme till Hus',
            'value': heat_from_hp
        }
    ]

    if aux_heater_power > 5:
        nodes.append({'name': '🔥 Tillsattsvärme'})
        links.append({
            'source': '🔥 Tillsattsvärme',
            'target': '🏠 Värme till Hus',
            'value': aux_heater_power
        })

    option = {
        'title': {
            'text': f'Energiflöde (COP: {avg_cop:.2f}, {free_energy_percent:.0f}% gratis från mark)',
            'textStyle': {'fontSize': 14, 'color': 'gray'}
        },
        'series': [
            {
                'type': 'sankey',
                'layout': 'none',
                'emphasis': {
                    'focus': 'adjacency'
                },
                'data': nodes,
                'links': links,
                'lineStyle': {
                    'color': 'gradient',
                    'curveness': 0.5
                },
                'itemStyle': {
                    'borderWidth': 2,
                    'borderColor': '#fff'
                },
                'label': {
                    'color': '#333',
                    'fontSize': 11
                }
            }
        ],
        'backgroundColor': 'transparent'
    }

    return option
```

---

## Subplots/Grid Layout in ECharts

For multi-subplot charts (performance, power, valve status), ECharts uses a grid-based system:

```python
def update_performance_graph(n, time_range):
    """Performance graph med 2 subplots"""
    # ... data fetching ...

    option = {
        # Define grid layout (2 rows)
        'grid': [
            {'left': 40, 'right': 40, 'top': 60, 'height': '35%'},   # Top subplot
            {'left': 40, 'right': 40, 'top': '55%', 'height': '35%'} # Bottom subplot
        ],

        # Define 2 x-axes (one per subplot)
        'xAxis': [
            {'gridIndex': 0, 'type': 'time'},
            {'gridIndex': 1, 'type': 'time', 'name': 'Tid'}
        ],

        # Define 2 y-axes
        'yAxis': [
            {'gridIndex': 0, 'name': 'ΔT (°C)'},
            {'gridIndex': 1, 'name': 'Status'}
        ],

        # Series with xAxisIndex/yAxisIndex to link to grids
        'series': [
            {
                'type': 'line',
                'name': 'KB ΔT',
                'xAxisIndex': 0,
                'yAxisIndex': 0,
                'data': brine_delta_data,
                'lineStyle': {'color': THERMIA_COLORS['delta_brine']}
            },
            {
                'type': 'line',
                'name': 'Radiator ΔT',
                'xAxisIndex': 0,
                'yAxisIndex': 0,
                'data': rad_delta_data,
                'lineStyle': {'color': THERMIA_COLORS['delta_radiator']}
            },
            {
                'type': 'line',
                'name': 'Kompressor',
                'xAxisIndex': 1,
                'yAxisIndex': 1,
                'data': compressor_data,
                'areaStyle': {'color': 'rgba(76, 175, 80, 0.3)'},
                'lineStyle': {'color': THERMIA_COLORS['compressor']}
            }
        ],

        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'cross'}
        },
        'backgroundColor': 'transparent'
    }

    return option
```

---

## Migration Checklist

### Phase 1: Setup (1-2 hours)
- [ ] Install `dash-echarts`
- [ ] Update `requirements.txt`
- [ ] Test basic chart rendering

### Phase 2: Simple Charts (2-4 hours)
- [ ] Migrate COP graph (line chart)
- [ ] Migrate runtime pie chart
- [ ] Test callbacks and data flow

### Phase 3: Complex Charts (4-8 hours)
- [ ] Migrate temperature graph (multi-line)
- [ ] Migrate Sankey diagram
- [ ] Test hover interactions

### Phase 4: Subplots (6-10 hours)
- [ ] Migrate performance graph (2 subplots)
- [ ] Migrate power graph (2 subplots)
- [ ] Migrate valve status graph (3 subplots)
- [ ] Fine-tune grid layouts

### Phase 5: Polish (2-4 hours)
- [ ] Update CSS for ECharts styling
- [ ] Test responsive behavior
- [ ] Performance testing
- [ ] Cross-browser testing

**Total Estimated Time: 15-28 hours**

---

## Performance Comparison

| Metric | Plotly | ECharts | Winner |
|--------|--------|---------|--------|
| **Bundle Size** | ~3.5MB | ~900KB | 🏆 ECharts |
| **Render Speed** | Good | Excellent | 🏆 ECharts |
| **Large Datasets** | Struggles >10k points | Handles 100k+ points | 🏆 ECharts |
| **Interactivity** | Excellent | Excellent | Tie |
| **Mobile** | Good | Excellent | 🏆 ECharts |
| **Documentation** | Excellent | Good (in English) | 🏆 Plotly |
| **Dash Integration** | Native | Third-party | 🏆 Plotly |

---

## Risks & Mitigation

| Risk | Severity | Mitigation |
|------|----------|-----------|
| `dash-echarts` bugs | Medium | Test thoroughly, have Plotly fallback |
| Learning curve | Low | ECharts docs are good |
| Breaking changes | Low | Pin package versions |
| Community support | Medium | Plotly has larger Dash community |
| Feature parity | Low | ECharts has all needed features |

---

## Verdict

### ✅ Proceed with Migration IF:
- You need better performance (smaller bundle, faster rendering)
- You have 2-3 weeks for implementation + testing
- You're willing to use a third-party Dash extension
- Your data sets are large (>5k points per chart)

### ❌ Stay with Plotly IF:
- Dashboard works fine currently
- No performance issues
- Limited development time
- Want to stay with official Dash ecosystem
- Need guaranteed long-term support

---

## Next Steps

If you decide to proceed:

1. **Prototype First:** Migrate just the COP graph to test `dash-echarts`
2. **Validate:** Ensure callbacks, styling, and data flow work
3. **Incremental Migration:** Move chart-by-chart (not all at once)
4. **Keep Plotly:** Don't remove Plotly until all charts migrated
5. **Testing:** Extensive testing on different browsers/devices

Would you like me to:
- Start with a proof-of-concept migration of one chart?
- Set up the dash-echarts package?
- Create a detailed migration plan with code examples?
