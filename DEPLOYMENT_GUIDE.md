# Heat Pump Dashboard - Deployment Guide

Complete guide for deploying the new Flask + WebSocket + ECharts dashboard.

## 🎯 Quick Start

### Option 1: Docker (Recommended)

```bash
# 1. Set environment variables
export INFLUXDB_TOKEN=your-influxdb-token
export HEATPUMP_BRAND=thermia  # or ivt, nibe

# 2. Start dashboard
docker-compose -f docker-compose.websocket.yml up -d

# 3. Access dashboard
open http://localhost:8050
```

### Option 2: Local Python

```bash
# 1. Navigate to dashboard directory
cd /home/user/heatpump/dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
export INFLUXDB_URL=http://localhost:8086
export INFLUXDB_TOKEN=your-token
export INFLUXDB_ORG=thermia
export INFLUXDB_BUCKET=heatpump
export HEATPUMP_BRAND=thermia

# 4. Run server
python app.py

# 5. Access dashboard
open http://localhost:8050
```

## 📋 Prerequisites

### Required

- **InfluxDB 2.x**: Running and accessible
- **InfluxDB Token**: With read access to heatpump bucket
- **Python 3.11+** (if running locally)
- **Docker & Docker Compose** (if using containers)

### Optional

- Reverse proxy (nginx, Traefik) for HTTPS
- Domain name for production deployment

## 🔧 Configuration

### Environment Variables

Create a `.env` file in repository root:

```bash
# InfluxDB Configuration
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your-token-here
INFLUXDB_ORG=thermia
INFLUXDB_BUCKET=heatpump

# Dashboard Configuration
HEATPUMP_BRAND=thermia  # thermia, ivt, or nibe
SECRET_KEY=generate-secure-random-key-for-production

# InfluxDB Initial Setup (first run only)
INFLUX_USERNAME=admin
INFLUX_PASSWORD=changeme123
```

### Generate Secure Secret Key

```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

### Brand Configuration (Optional)

Create `config.yaml` in repository root:

```yaml
brand: thermia  # thermia, ivt, or nibe
```

## 🐳 Docker Deployment

### Full Stack with InfluxDB

```bash
# Start both dashboard and InfluxDB
docker-compose -f docker-compose.websocket.yml up -d

# Check status
docker ps

# View logs
docker logs -f heatpump-dashboard-websocket

# Stop
docker-compose -f docker-compose.websocket.yml down
```

### Dashboard Only (Existing InfluxDB)

```bash
# Edit docker-compose.websocket.yml
# Comment out the influxdb service
# Update INFLUXDB_URL to point to your InfluxDB

# Start dashboard only
docker-compose -f docker-compose.websocket.yml up -d dashboard-websocket
```

### Build Custom Image

```bash
cd /home/user/heatpump/dashboard

# Build
docker build -t heatpump-dashboard:websocket .

# Run
docker run -d \
  --name heatpump-dashboard \
  -p 8050:8050 \
  -e INFLUXDB_URL=http://influxdb:8086 \
  -e INFLUXDB_TOKEN=your-token \
  -e HEATPUMP_BRAND=thermia \
  -v $(pwd)/../dashboard_dash/data_query.py:/app/data_query.py:ro \
  -v $(pwd)/../dashboard_dash/config_colors.py:/app/config_colors.py:ro \
  -v $(pwd)/../providers:/app/providers:ro \
  heatpump-dashboard:websocket
```

## 🌐 Production Deployment

### 1. Reverse Proxy with nginx

```nginx
# /etc/nginx/sites-available/heatpump

upstream heatpump_backend {
    server localhost:8050;
}

server {
    listen 80;
    server_name heatpump.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name heatpump.example.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/heatpump.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/heatpump.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # WebSocket Support
    location / {
        proxy_pass http://heatpump_backend;
        proxy_http_version 1.1;

        # WebSocket headers
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Standard proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_read_timeout 86400;  # 24 hours for WebSocket
        proxy_send_timeout 86400;
    }

    # Static files (optional caching)
    location /static/ {
        proxy_pass http://heatpump_backend;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable and test:

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/heatpump /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### 2. SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d heatpump.example.com

# Auto-renewal (certbot sets this up automatically)
sudo certbot renew --dry-run
```

### 3. Systemd Service (Alternative to Docker)

Create `/etc/systemd/system/heatpump-dashboard.service`:

```ini
[Unit]
Description=Heat Pump Dashboard (WebSocket)
After=network.target influxdb.service

[Service]
Type=simple
User=heatpump
Group=heatpump
WorkingDirectory=/opt/heatpump/dashboard
Environment="INFLUXDB_URL=http://localhost:8086"
Environment="INFLUXDB_TOKEN=your-token"
Environment="INFLUXDB_ORG=thermia"
Environment="INFLUXDB_BUCKET=heatpump"
Environment="HEATPUMP_BRAND=thermia"
Environment="SECRET_KEY=your-secret-key"
ExecStart=/usr/bin/python3 /opt/heatpump/dashboard/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable heatpump-dashboard
sudo systemctl start heatpump-dashboard
sudo systemctl status heatpump-dashboard
```

## 🔍 Health Checks

### Manual Health Check

```bash
# Config endpoint
curl http://localhost:8050/api/config

# Should return:
# {"brand":"thermia","display_name":"Thermia Diplomat","colors":{...}}

# Initial data endpoint
curl http://localhost:8050/api/initial-data?range=1h

# Should return JSON with all 7 chart datasets
```

### Automated Health Check

Docker includes built-in health check:

```bash
# Check container health
docker ps

# Should show "healthy" status after 40 seconds
```

### Monitoring WebSocket

```bash
# View WebSocket connections in logs
docker logs -f heatpump-dashboard-websocket | grep "Client connected"

# Or for systemd
journalctl -u heatpump-dashboard -f | grep "Client connected"
```

## 🚨 Troubleshooting

### Issue: Dashboard shows "Disconnected"

**Symptoms**: Connection badge shows red "Frånkopplad"

**Solutions**:
1. Check server is running:
   ```bash
   docker ps | grep dashboard
   # or
   sudo systemctl status heatpump-dashboard
   ```

2. Check WebSocket connection in browser console (F12):
   ```javascript
   // Should see: ✅ WebSocket connected
   ```

3. Check firewall:
   ```bash
   sudo ufw status
   sudo ufw allow 8050/tcp
   ```

4. Check logs:
   ```bash
   docker logs heatpump-dashboard-websocket
   ```

### Issue: Charts show no data

**Symptoms**: Charts are empty or show "No data available"

**Solutions**:
1. Verify InfluxDB has data:
   ```bash
   # Check InfluxDB is running
   curl http://localhost:8086/health

   # Check bucket has data (use InfluxDB UI)
   open http://localhost:8086
   ```

2. Check environment variables:
   ```bash
   docker exec heatpump-dashboard-websocket env | grep INFLUX
   ```

3. Test data query:
   ```bash
   curl "http://localhost:8050/api/initial-data?range=1h"
   ```

4. Check server logs for errors:
   ```bash
   docker logs heatpump-dashboard-websocket | grep ERROR
   ```

### Issue: WebSocket keeps reconnecting

**Symptoms**: Connection status flickers, logs show rapid connect/disconnect

**Solutions**:
1. Check reverse proxy WebSocket support:
   - Ensure `Upgrade` and `Connection` headers are set
   - Increase proxy timeouts

2. Check network stability:
   ```bash
   ping -c 10 localhost
   ```

3. Review browser console for errors

4. Check server CPU/memory:
   ```bash
   docker stats heatpump-dashboard-websocket
   ```

### Issue: Slow performance

**Symptoms**: Charts take long to load or update

**Solutions**:
1. Use shorter time range:
   - 1h or 6h instead of 30d

2. Check InfluxDB query performance:
   ```bash
   # View InfluxDB logs
   docker logs influxdb | grep query
   ```

3. Optimize InfluxDB:
   - Check disk space
   - Review retention policies
   - Consider downsampling old data

4. Monitor resource usage:
   ```bash
   docker stats
   ```

## 📊 Monitoring

### Key Metrics to Monitor

1. **WebSocket Connections**: Number of active clients
2. **Update Frequency**: Auto-updates every 30 seconds
3. **Response Time**: API endpoint latency
4. **Memory Usage**: Container/process memory
5. **Error Rate**: Failed queries or WebSocket errors

### Prometheus Monitoring (Optional)

Add metrics endpoint to app.py:

```python
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
websocket_connections = Counter('websocket_connections_total', 'Total WebSocket connections')
api_requests = Counter('api_requests_total', 'Total API requests')
api_duration = Histogram('api_request_duration_seconds', 'API request duration')

# Add metrics endpoint
@app.route('/metrics')
def metrics():
    return generate_latest()
```

## 🔄 Updates and Maintenance

### Updating Dashboard

```bash
# Pull latest code
git pull origin main

# Rebuild Docker image
docker-compose -f docker-compose.websocket.yml build dashboard-websocket

# Restart with new image
docker-compose -f docker-compose.websocket.yml up -d dashboard-websocket
```

### Backup Configuration

```bash
# Backup environment variables
cp .env .env.backup

# Backup config file
cp config.yaml config.yaml.backup

# Backup InfluxDB data (if running in Docker)
docker run --rm -v heatpump_influxdb-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/influxdb-backup-$(date +%Y%m%d).tar.gz /data
```

### Rollback to Dash Version

If you need to rollback to the old Dash version:

```bash
# Stop WebSocket dashboard
docker-compose -f docker-compose.websocket.yml down

# Start Dash dashboard
cd dashboard_dash
python app.py
# or use original docker-compose if available
```

## 🎯 Performance Tuning

### For High Traffic

1. **Use multiple workers** (if using gunicorn):
   ```bash
   gunicorn --worker-class eventlet -w 4 --bind 0.0.0.0:8050 app:app
   ```

2. **Enable compression** in nginx:
   ```nginx
   gzip on;
   gzip_types application/json text/css application/javascript;
   ```

3. **Cache static assets**:
   ```nginx
   location /static/ {
       expires 7d;
       add_header Cache-Control "public, immutable";
   }
   ```

4. **Use Redis for session storage** (if needed):
   ```python
   from flask_session import Session
   app.config['SESSION_TYPE'] = 'redis'
   Session(app)
   ```

### For Resource-Constrained Environments

1. **Increase update interval** (reduce from 30s to 60s):
   ```python
   # In app.py background_updates()
   eventlet.sleep(60)  # Changed from 30
   ```

2. **Limit concurrent connections**:
   ```python
   MAX_CONNECTIONS = 100
   if len(connected_clients) >= MAX_CONNECTIONS:
       emit('error', {'message': 'Server at capacity'})
       return disconnect()
   ```

3. **Reduce chart data points**:
   - Use larger aggregation windows in InfluxDB queries
   - Already implemented in `data_query.py`

## 📝 Checklist for Production

Before deploying to production, verify:

- [ ] INFLUXDB_TOKEN is set securely
- [ ] SECRET_KEY is generated and set
- [ ] HTTPS is configured (SSL certificate)
- [ ] Firewall rules are configured
- [ ] Health checks are passing
- [ ] Monitoring is set up
- [ ] Backups are configured
- [ ] Reverse proxy is configured (if needed)
- [ ] Domain name is pointed to server
- [ ] Error logging is enabled
- [ ] Resource limits are set (Docker)
- [ ] Auto-restart is enabled
- [ ] Documentation is updated

## 🔗 Related Documentation

- Main README: `dashboard/README.md`
- Migration Plan: `WEBSOCKET_MIGRATION_PLAN.md`
- Phase Completion Docs: `PHASE[1-3]_COMPLETE.md`
- Original Dash Version: `dashboard_dash/README_SV.md`

## 💡 Best Practices

1. **Security**:
   - Always use HTTPS in production
   - Set strong SECRET_KEY
   - Use read-only InfluxDB token
   - Keep dependencies updated

2. **Performance**:
   - Monitor resource usage
   - Use appropriate time ranges
   - Enable caching where appropriate
   - Optimize InfluxDB queries

3. **Reliability**:
   - Set up health checks
   - Enable auto-restart
   - Monitor logs regularly
   - Have rollback plan ready

4. **Maintenance**:
   - Regular backups
   - Keep documentation updated
   - Test updates in staging first
   - Monitor error rates

---

**Need help?** Check the troubleshooting section or review server logs for errors.
