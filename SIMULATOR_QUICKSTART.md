# Simulator Quick Start Guide

Test the dashboard with different heat pump manufacturers **without needing a real heat pump or MQTT broker!**

## 🚀 Quick Start (2 steps)

### 1. Enable simulator in `config.yaml`

```yaml
simulator:
  enabled: true
  manufacturer: thermia  # Choose: 'thermia', 'ivt', or 'nibe'
  outdoor_temp: -5       # Set outdoor temperature (°C)
```

### 2. Start with embedded MQTT broker

```bash
docker-compose --profile simulator up -d
```

**Done!** Open http://localhost:8050 to see the dashboard with simulated data.

## 📊 What You Get

- ✅ Embedded MQTT broker (no configuration needed)
- ✅ Realistic heat pump behavior simulation
- ✅ Compressor cycling every 20-45 minutes
- ✅ Hot water mode switches every 2-4 hours
- ✅ Weather compensation
- ✅ Realistic COP values (1.5 - 6.0)
- ✅ Power consumption tracking

## 🔄 Switch Manufacturers

Want to see how the dashboard looks with different brands?

**Test IVT:**
```yaml
simulator:
  manufacturer: ivt
```

**Test NIBE:**
```yaml
simulator:
  manufacturer: nibe
```

Restart: `docker-compose --profile simulator restart simulator`

## 📝 View Logs

```bash
# Simulator logs
docker-compose logs -f simulator

# MQTT broker logs
docker-compose logs -f mosquitto-sim

# All services
docker-compose logs -f
```

## 🛑 Stop Simulator

```bash
docker-compose --profile simulator down
```

## 💡 Tips

- Data starts flowing after 10-20 seconds
- Compressor cycles: Look for "Compressor turned ON/OFF" in logs
- COP values are realistic: better when outdoor temp is higher
- Change outdoor temp in config.yaml to see how system responds

## 🏗️ Architecture

```
┌─────────────────────────┐
│  Embedded MQTT Broker   │ (mosquitto-sim)
│  Port: 1883             │
└───────▲─────────────────┘
        │
        │ publishes metrics
        │
┌───────┴─────────────────┐
│  Heat Pump Simulator    │ (thermia/ivt/nibe)
│  Generates realistic    │
│  metrics every 10s      │
└─────────────────────────┘

┌─────────────────────────┐
│  Collector              │ subscribes to MQTT
│  Stores in InfluxDB     │
└─────────────────────────┘

┌─────────────────────────┐
│  Dashboard              │ reads from InfluxDB
│  http://localhost:8050  │
└─────────────────────────┘
```

## ❓ Troubleshooting

**Dashboard shows no data?**
- Check simulator is enabled: `docker-compose ps`
- View logs: `docker-compose logs simulator`
- Wait 30 seconds for first data

**Wrong metrics?**
- Verify manufacturer setting matches your expectation
- Check logs for MQTT publish confirmations

**Port 1883 already in use?**
- Stop your external MQTT broker first
- Or modify port in docker-compose.yml

## 📚 More Info

See `simulator/README.md` for detailed documentation.
