/**
 * ECharts Management for Heat Pump Dashboard
 * Handles initialization and updates for all 7 charts
 */

// Store chart instances globally
const charts = {};

// Store dashboard configuration
let dashboardConfig = null;

// ==================== Chart Initialization ====================

function initializeCharts(data) {
    console.log('📈 Initializing all charts...');

    // Store configuration
    if (data.config) {
        dashboardConfig = data.config;
    }

    // Initialize each chart instance
    charts.cop = echarts.init(document.getElementById('cop-chart'));
    charts.temperature = echarts.init(document.getElementById('temperature-chart'));
    charts.runtime = echarts.init(document.getElementById('runtime-chart'));
    charts.sankey = echarts.init(document.getElementById('sankey-chart'));
    charts.performance = echarts.init(document.getElementById('performance-chart'));
    charts.power = echarts.init(document.getElementById('power-chart'));
    charts.valve = echarts.init(document.getElementById('valve-chart'));

    // Update all charts with initial data
    updateAllCharts(data);

    // Make charts responsive
    window.addEventListener('resize', () => {
        Object.values(charts).forEach(chart => chart.resize());
    });

    console.log('✅ All charts initialized');
}

// ==================== Update All Charts ====================

function updateAllCharts(data) {
    if (data.cop) updateCopChart(data.cop);
    if (data.temperature) updateTemperatureChart(data.temperature);
    if (data.runtime) updateRuntimeChart(data.runtime);
    if (data.sankey) updateSankeyChart(data.sankey);
    if (data.performance) updatePerformanceChart(data.performance);
    if (data.power) updatePowerChart(data.power);
    if (data.valve) updateValveChart(data.valve);
}

// ==================== Chart 1: COP Line Chart ====================

function updateCopChart(data) {
    if (!data.values || data.values.length === 0) {
        console.warn('No COP data available');
        return;
    }

    const option = {
        grid: {
            left: 60,
            right: 40,
            top: 40,
            bottom: 60,
            backgroundColor: 'transparent'
        },
        xAxis: {
            type: 'time',
            name: 'Tid',
            nameLocation: 'middle',
            nameGap: 40,
            axisLine: { lineStyle: { color: '#999' } },
            axisLabel: { fontSize: 11 }
        },
        yAxis: {
            type: 'value',
            name: 'COP',
            min: 0,
            max: 6,
            axisLine: { lineStyle: { color: '#999' } },
            splitLine: { lineStyle: { color: '#eee' } }
        },
        series: [{
            type: 'line',
            name: 'COP',
            data: data.timestamps.map((t, i) => [t, data.values[i]]),
            smooth: true,
            lineStyle: {
                color: '#4CAF50',
                width: 3
            },
            areaStyle: {
                color: 'rgba(76, 175, 80, 0.2)'
            },
            markLine: {
                silent: false,
                symbol: 'none',
                lineStyle: {
                    type: 'dashed',
                    color: '#ff9800',
                    width: 2
                },
                label: {
                    position: 'end',
                    formatter: `Medel: ${data.avg.toFixed(2)}`
                },
                data: [{
                    yAxis: data.avg
                }]
            }
        }],
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross',
                label: { backgroundColor: '#6a7985' }
            },
            formatter: (params) => {
                const date = new Date(params[0].value[0]);
                const time = date.toLocaleTimeString('sv-SE');
                const value = params[0].value[1].toFixed(2);
                return `${time}<br/>COP: <b>${value}</b>`;
            }
        },
        backgroundColor: 'transparent'
    };

    charts.cop.setOption(option, true);
}

// ==================== Chart 2: Temperature Multi-line Chart ====================

function updateTemperatureChart(data) {
    if (!data.timestamps || data.timestamps.length === 0) {
        console.warn('No temperature data available');
        return;
    }

    const metrics = [
        { key: 'hot_water_top', name: 'Varmvatten', color: '#ff9800' },
        { key: 'radiator_forward', name: 'Radiator Fram ↑', color: '#dc143c' },
        { key: 'radiator_return', name: 'Radiator Retur ↓', color: '#ffd700' },
        { key: 'indoor_temp', name: 'Inne', color: '#4caf50' },
        { key: 'outdoor_temp', name: 'Ute', color: '#64b5f6' },
        { key: 'brine_in_evaporator', name: 'KB In →', color: '#00d4ff' },
        { key: 'brine_out_condenser', name: 'KB Ut ←', color: '#1565c0' }
    ];

    const series = [];
    const legendData = [];

    metrics.forEach(metric => {
        if (data[metric.key] && data[metric.key].length > 0) {
            legendData.push(metric.name);
            series.push({
                type: 'line',
                name: metric.name,
                data: data[metric.key].map((v, i) => [data.timestamps[i], v]),
                smooth: true,
                lineStyle: { color: metric.color, width: 2.5 },
                showSymbol: false
            });
        }
    });

    const option = {
        grid: {
            left: 60,
            right: 40,
            top: 80,
            bottom: 60,
            backgroundColor: 'transparent'
        },
        legend: {
            data: legendData,
            top: 10,
            right: 10,
            orient: 'horizontal',
            textStyle: { fontSize: 11 }
        },
        xAxis: {
            type: 'time',
            name: 'Tid',
            nameLocation: 'middle',
            nameGap: 40,
            axisLine: { lineStyle: { color: '#999' } }
        },
        yAxis: {
            type: 'value',
            name: 'Temperatur (°C)',
            axisLine: { lineStyle: { color: '#999' } },
            splitLine: { lineStyle: { color: '#eee' } }
        },
        series: series,
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross' }
        },
        backgroundColor: 'transparent'
    };

    charts.temperature.setOption(option, true);
}

// ==================== Chart 3: Runtime Pie Chart ====================

function updateRuntimeChart(data) {
    const option = {
        series: [{
            type: 'pie',
            radius: ['40%', '70%'],
            data: [
                {
                    value: data.compressor_percent,
                    name: 'Kompressor',
                    itemStyle: { color: '#4caf50' }
                },
                {
                    value: data.aux_heater_percent,
                    name: 'Tillsats',
                    itemStyle: { color: '#ffc107' }
                },
                {
                    value: data.inactive_percent,
                    name: 'Inaktiv',
                    itemStyle: { color: '#e9ecef' }
                }
            ],
            label: {
                formatter: '{b}: {d}%',
                fontSize: 12
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        }],
        tooltip: {
            trigger: 'item',
            formatter: '{b}: {c}% ({d}%)'
        },
        backgroundColor: 'transparent'
    };

    charts.runtime.setOption(option, true);
}

// ==================== Chart 4: Sankey Energy Flow ====================

function updateSankeyChart(data) {
    if (!data.nodes || data.nodes.length === 0) {
        console.warn('No Sankey data available');
        return;
    }

    const option = {
        title: {
            text: `Energiflöde (COP: ${data.cop.toFixed(2)}, ${data.free_energy_percent.toFixed(0)}% gratis från mark)`,
            textStyle: { fontSize: 14, color: '#666' },
            left: 'center',
            top: 10
        },
        series: [{
            type: 'sankey',
            layout: 'none',
            emphasis: { focus: 'adjacency' },
            data: data.nodes,
            links: data.links.map(link => ({
                source: link.source,
                target: link.target,
                value: link.value
            })),
            lineStyle: {
                color: 'gradient',
                curveness: 0.5
            },
            itemStyle: {
                borderWidth: 2,
                borderColor: '#fff'
            },
            label: {
                color: '#333',
                fontSize: 12
            }
        }],
        tooltip: {
            trigger: 'item',
            formatter: (params) => {
                if (params.dataType === 'edge') {
                    return `${params.data.source} → ${params.data.target}<br/>Energi: ${params.value.toFixed(0)}`;
                } else {
                    return `${params.name}`;
                }
            }
        },
        backgroundColor: 'transparent'
    };

    charts.sankey.setOption(option, true);
}

// ==================== Chart 5: Performance (2 subplots) ====================

function updatePerformanceChart(data) {
    const option = {
        grid: [
            { left: 70, right: 50, top: 80, height: '35%' },
            { left: 70, right: 50, top: '58%', height: '30%' }
        ],
        title: [
            { text: 'Temperaturdifferenser', left: 'center', top: 50, textStyle: { fontSize: 14 } },
            { text: 'Kompressor Drifttid', left: 'center', top: '50%', textStyle: { fontSize: 14 } }
        ],
        xAxis: [
            { gridIndex: 0, type: 'time', show: false },
            { gridIndex: 1, type: 'time', name: 'Tid', nameLocation: 'middle', nameGap: 30 }
        ],
        yAxis: [
            { gridIndex: 0, name: 'ΔT (°C)', splitLine: { lineStyle: { color: '#eee' } } },
            { gridIndex: 1, name: 'Status', min: -0.1, max: 1.1, splitLine: { lineStyle: { color: '#eee' } } }
        ],
        series: [
            {
                name: 'KB ΔT',
                type: 'line',
                xAxisIndex: 0,
                yAxisIndex: 0,
                data: data.brine_delta || [],
                lineStyle: { color: '#26c6da', width: 2.5 },
                showSymbol: false
            },
            {
                name: 'Radiator ΔT',
                type: 'line',
                xAxisIndex: 0,
                yAxisIndex: 0,
                data: data.radiator_delta || [],
                lineStyle: { color: '#ff5722', width: 2.5 },
                showSymbol: false
            },
            {
                name: 'Kompressor',
                type: 'line',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: data.compressor_status || [],
                areaStyle: { color: 'rgba(76, 175, 80, 0.3)' },
                lineStyle: { color: '#4caf50', width: 2.5 },
                showSymbol: false,
                step: 'end'
            }
        ],
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross' }
        },
        backgroundColor: 'transparent'
    };

    charts.performance.setOption(option, true);
}

// ==================== Chart 6: Power (2 subplots) ====================

function updatePowerChart(data) {
    const option = {
        grid: [
            { left: 70, right: 50, top: 80, height: '35%' },
            { left: 70, right: 50, top: '58%', height: '30%' }
        ],
        title: [
            { text: 'Effektförbrukning', left: 'center', top: 50, textStyle: { fontSize: 14 } },
            { text: 'Systemstatus', left: 'center', top: '50%', textStyle: { fontSize: 14 } }
        ],
        xAxis: [
            { gridIndex: 0, type: 'time', show: false },
            { gridIndex: 1, type: 'time', name: 'Tid', nameLocation: 'middle', nameGap: 30 }
        ],
        yAxis: [
            { gridIndex: 0, name: 'Effekt (W)', splitLine: { lineStyle: { color: '#eee' } } },
            { gridIndex: 1, name: 'Status / %', splitLine: { lineStyle: { color: '#eee' } } }
        ],
        series: [
            {
                name: 'Effekt',
                type: 'line',
                xAxisIndex: 0,
                yAxisIndex: 0,
                data: data.power_consumption || [],
                lineStyle: { color: '#9b59b6', width: 2.5 },
                areaStyle: { color: 'rgba(155, 89, 182, 0.2)' },
                showSymbol: false
            },
            {
                name: 'Kompressor',
                type: 'line',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: data.compressor_status || [],
                lineStyle: { color: '#4caf50', width: 2.5 },
                showSymbol: false,
                step: 'end'
            },
            {
                name: 'Tillsats %',
                type: 'line',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: data.additional_heat_percent || [],
                lineStyle: { color: '#ffc107', width: 2.5 },
                showSymbol: false
            }
        ],
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross' }
        },
        backgroundColor: 'transparent'
    };

    charts.power.setOption(option, true);
}

// ==================== Chart 7: Valve Status (3 subplots) ====================

function updateValveChart(data) {
    const option = {
        grid: [
            { left: 70, right: 50, top: 80, height: '22%' },
            { left: 70, right: 50, top: '40%', height: '22%' },
            { left: 70, right: 50, top: '70%', height: '22%' }
        ],
        title: [
            { text: 'Växelventilsläge (1=Varmvatten, 0=Uppvärmning)', left: 'center', top: 50, textStyle: { fontSize: 13 } },
            { text: 'Kompressorstatus (1=PÅ, 0=AV)', left: 'center', top: '32%', textStyle: { fontSize: 13 } },
            { text: 'Varmvattentemperatur (°C)', left: 'center', top: '62%', textStyle: { fontSize: 13 } }
        ],
        xAxis: [
            { gridIndex: 0, type: 'time', show: false },
            { gridIndex: 1, type: 'time', show: false },
            { gridIndex: 2, type: 'time', name: 'Tid', nameLocation: 'middle', nameGap: 30 }
        ],
        yAxis: [
            { gridIndex: 0, name: 'Status', min: -0.1, max: 1.1, splitLine: { lineStyle: { color: '#eee' } } },
            { gridIndex: 1, name: 'Status', min: -0.1, max: 1.1, splitLine: { lineStyle: { color: '#eee' } } },
            { gridIndex: 2, name: 'Temp (°C)', splitLine: { lineStyle: { color: '#eee' } } }
        ],
        series: [
            {
                name: 'Växelventil',
                type: 'line',
                xAxisIndex: 0,
                yAxisIndex: 0,
                data: data.valve_status || [],
                lineStyle: { color: '#ff9800', width: 3 },
                areaStyle: { color: 'rgba(255, 152, 0, 0.3)' },
                showSymbol: false,
                step: 'end'
            },
            {
                name: 'Kompressor',
                type: 'line',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: data.compressor_status || [],
                lineStyle: { color: '#4caf50', width: 2.5 },
                areaStyle: { color: 'rgba(76, 175, 80, 0.2)' },
                showSymbol: false,
                step: 'end'
            },
            {
                name: 'VV Temp',
                type: 'line',
                xAxisIndex: 2,
                yAxisIndex: 2,
                data: data.hot_water_temp || [],
                lineStyle: { color: '#ff9800', width: 2.5 },
                showSymbol: false
            }
        ],
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross' }
        },
        backgroundColor: 'transparent'
    };

    charts.valve.setOption(option, true);
}

// ==================== KPI Updates ====================

function updateKPIs(data) {
    // COP
    if (data.cop && data.cop.avg) {
        document.getElementById('kpi-cop').textContent = data.cop.avg.toFixed(2);
    }

    // Compressor runtime
    if (data.runtime && data.runtime.compressor_percent !== undefined) {
        document.getElementById('kpi-compressor').textContent = `${data.runtime.compressor_percent.toFixed(0)}%`;
    }

    // Indoor temperature (latest value from temperature data)
    if (data.temperature && data.temperature.indoor_temp) {
        const temps = data.temperature.indoor_temp;
        if (temps.length > 0) {
            const latest = temps[temps.length - 1];
            document.getElementById('kpi-indoor').textContent = `${latest.toFixed(1)}°C`;
        }
    }

    // Hot water temperature (latest value)
    if (data.temperature && data.temperature.hot_water_top) {
        const temps = data.temperature.hot_water_top;
        if (temps.length > 0) {
            const latest = temps[temps.length - 1];
            document.getElementById('kpi-hot-water').textContent = `${latest.toFixed(0)}°C`;
        }
    }
}

// ==================== Export Functions ====================

// Make functions available globally
window.initializeCharts = initializeCharts;
window.updateAllCharts = updateAllCharts;
window.updateKPIs = updateKPIs;

console.log('🎨 Charts module loaded');
