# Heat Pump Simulator

Realistic metric generator for testing the dashboard UI with different heat pump manufacturers.

## Supported Manufacturers

1. **Thermia** - Uses current metric names (radiator_forward, brine_in_evaporator, etc.)
2. **IVT** - Uses GT/EB naming (GT1, GT2, EB1, etc.) - common in Swedish IVT heat pumps
3. **NIBE** - Uses ModBus register numbers (40004, 40008, 43086, etc.) - NIBE F/S series

## Features

- ✅ Realistic temperature simulation based on physics
- ✅ Compressor cycling (20-45 min ON, 10-30 min OFF)
- ✅ Hot water vs heating mode switching
- ✅ Weather compensation (forward temp adjusts with outdoor temp)
- ✅ Auxiliary heater activation in cold weather
- ✅ Realistic COP calculation (1.5 - 6.0 range)
- ✅ Power consumption simulation
- ✅ Runtime counters
- ✅ MQTT publishing with manufacturer-specific topic structure

## Configuration

Edit `config.yaml`:

```yaml
simulator:
  enabled: true
  manufacturer: thermia  # or 'ivt' or 'nibe'
  update_interval: 10    # seconds
  outdoor_temp: -5       # °C
  mode: mqtt             # 'mqtt', 'influxdb', or 'both'
```

## Running the Simulator

### Option 1: Docker Compose (Recommended)

```bash
# Start with simulator profile
docker-compose --profile simulator up -d

# View logs
docker-compose logs -f simulator

# Stop simulator
docker-compose --profile simulator down
```

### Option 2: Standalone Python

```bash
cd simulator
pip install -r requirements.txt
python simulator.py
```

## Testing Different Manufacturers

### Test Thermia

```yaml
simulator:
  enabled: true
  manufacturer: thermia
```

Metrics published to:
- `thermia/outdoor_temp`
- `thermia/radiator_forward`
- `thermia/compressor`
- etc.

### Test IVT

```yaml
simulator:
  enabled: true
  manufacturer: ivt
```

Metrics published to:
- `ivt/sensors/gt1` (outdoor temp)
- `ivt/sensors/gt2` (supply temp)
- `ivt/relays/eb1` (compressor)
- etc.

### Test NIBE

```yaml
simulator:
  enabled: true
  manufacturer: nibe
```

Metrics published to:
- `nibe/40004/value` (BT1 - outdoor)
- `nibe/40008/value` (BT2 - supply)
- `nibe/43086/value` (compressor status)
- etc.

## Metric Mapping

Each simulator includes a `get_metric_mapping()` method that maps manufacturer-specific names to standard dashboard names:

```python
# IVT example
{
    'gt1_outdoor': 'outdoor_temp',
    'gt2_supply': 'radiator_forward',
    'eb1_compressor': 'compressor_status',
    ...
}
```

This allows the dashboard to work with any manufacturer by translating the metrics.

## Simulation Details

### Operating Cycles

- **Compressor**: Runs 20-45 minutes, then off for 10-30 minutes
- **Hot Water Mode**: Every 2-4 hours, runs for 30-60 minutes
- **Auxiliary Heater**: Only activates when outdoor temp < -10°C

### Temperature Simulation

- **Outdoor**: Set in config, used as base for all calculations
- **Indoor**: Slowly moves toward setpoint (21°C)
- **Brine Circuit**: Outdoor temp + 0.5-2°C (in), then -3 to -5°C delta
- **Radiator**: Weather compensated (higher outdoor = lower forward temp)
- **Hot Water**: Heats to 50-55°C in hot water mode

### COP Calculation

```
COP = 3.5 + (10 - temperature_difference) / 10
```

- Better COP with warmer brine and cooler forward temp
- Clamped to realistic range: 1.5 - 6.0
- Only calculated when compressor is running

### Power Consumption

- **Standby**: 20-50 W
- **Compressor ON**: 1200-1600 W (varies with outdoor temp)
- **Hot Water Mode**: +200-400 W
- **Aux Heater**: +2000-3000 W

## Development

### Adding a New Manufacturer

1. Create `simulator/{manufacturer}_simulator.py`:

```python
from .base_simulator import BaseHeatPumpSimulator

class MyBrandSimulator(BaseHeatPumpSimulator):
    def __init__(self):
        super().__init__(manufacturer="MyBrand")

    def get_metrics(self) -> dict:
        # Return manufacturer-specific metric names
        return {
            'my_temp_1': self.outdoor_temp,
            # ...
        }

    def get_mqtt_topic_mapping(self) -> dict:
        return {
            'my_temp_1': 'mybrand/temp1',
            # ...
        }

    def get_metric_mapping(self) -> dict:
        # Map to standard dashboard names
        return {
            'my_temp_1': 'outdoor_temp',
            # ...
        }
```

2. Register in `simulator/__init__.py`
3. Add to `simulator.py` in `_create_simulator()`

## Logs

The simulator provides detailed logging:

```
INFO - Initialized THERMIA heat pump simulator
DEBUG - Compressor turned ON
DEBUG - Switched to HOT WATER mode
INFO - 📊 Compressor: ON | Mode: Hot Water | Outdoor: -5.0°C | Forward: 52.3°C | COP: 3.45
```

## Troubleshooting

### Simulator not publishing metrics

1. Check `enabled: true` in config.yaml
2. Verify MQTT broker is running and accessible
3. Check logs: `docker-compose logs simulator`

### Wrong metric names in dashboard

1. Ensure manufacturer setting matches your expectation
2. Check metric mapping in simulator code
3. Verify collector is using correct topic subscription

### Unrealistic values

1. Adjust `outdoor_temp` in config
2. Check compressor is cycling (should see ON/OFF in logs)
3. Values stabilize after 5-10 minutes of runtime

## License

Part of the Heat Pump Dashboard project.
