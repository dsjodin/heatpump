#!/usr/bin/env python3
"""
Heat Pump Data Collector
Subscribes to MQTT topics from H66 Gateway and stores data in InfluxDB
Supports multiple brands: Thermia, IVT
"""

import os
import sys
import time
import json
import yaml
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Add parent directory to path for provider imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from providers import get_provider
from metrics import MetricsProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HeatPumpCollector:
    """Main collector class for heat pump data (supports multiple brands)"""

    def __init__(self, config_path: str = '/app/config.yaml'):
        """Initialize the collector with configuration"""
        self.config = self._load_config(config_path)

        # Get brand-specific provider
        brand = self.config.get('brand', 'thermia')
        try:
            self.provider = get_provider(brand)
            logger.info(f"Loaded provider for brand: {self.provider.get_display_name()}")
        except ValueError as e:
            logger.error(f"Failed to load provider: {e}")
            raise

        # Update config with registers from provider
        self.config['registers'] = self.provider.get_registers()

        self.mqtt_client = None
        self.influx_client = None
        self.write_api = None
        self.metrics_processor = MetricsProcessor(self.config)
        self.connected = False
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file or environment variables"""
        
        # Try to load from file first
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                logger.info("Configuration loaded from file")
                return config
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}, trying environment variables")
        
        # Fall back to environment variables
        logger.info("Loading configuration from environment variables")

        config = {
            'brand': os.getenv('HEATPUMP_BRAND', 'thermia'),
            'mqtt': {
                'broker': os.getenv('MQTT_BROKER', 'mosquitto'),
                'port': int(os.getenv('MQTT_PORT', '1883')),
                'username': os.getenv('MQTT_USERNAME', 'thermia'),
                'password': os.getenv('MQTT_PASSWORD', 'thermia123'),
                'client_id': os.getenv('MQTT_CLIENT_ID', 'thermia_monitor'),
                'h66_mac': os.getenv('H66_MAC', 'cd4dee258efa'),
                'keepalive': int(os.getenv('MQTT_KEEPALIVE', '60')),
                'qos': int(os.getenv('MQTT_QOS', '0'))
            },
            'collection': {
                'interval_seconds': int(os.getenv('COLLECTION_INTERVAL', '300')),
                'retry_attempts': int(os.getenv('RETRY_ATTEMPTS', '5')),
                'retry_delay': int(os.getenv('RETRY_DELAY', '10'))
            },
            'influxdb': {},
            'registers': {},  # Will be loaded from provider
            'dashboard': {
                'title': 'Heat Pump Monitor',
                'refresh_interval': 30,
                'time_ranges': ['1h', '6h', '24h', '7d', '30d', '90d']
            }
        }

        return config

    def _setup_influxdb(self):
        """Setup InfluxDB client and write API"""
        try:
            url = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
            token = os.getenv('INFLUXDB_TOKEN')
            org = os.getenv('INFLUXDB_ORG', 'thermia')
            bucket = os.getenv('INFLUXDB_BUCKET', 'heatpump')
            
            self.influx_client = InfluxDBClient(url=url, token=token, org=org)
            self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
            
            # Test connection
            health = self.influx_client.health()
            logger.info(f"InfluxDB connection established: {health.status}")
            
        except Exception as e:
            logger.error(f"Failed to setup InfluxDB: {e}")
            raise
    
    def _setup_mqtt(self):
        """Setup MQTT client and callbacks"""
        mqtt_config = self.config['mqtt']

        # Create client with clean session and automatic reconnect
        self.mqtt_client = mqtt.Client(
            client_id=mqtt_config['client_id'],
            clean_session=True,
            protocol=mqtt.MQTTv311
        )
        self.mqtt_client.username_pw_set(
            mqtt_config['username'],
            mqtt_config['password']
        )

        # Enable automatic reconnect
        self.mqtt_client.reconnect_delay_set(min_delay=1, max_delay=120)

        # Set callbacks
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_disconnect = self._on_disconnect
        self.mqtt_client.on_message = self._on_message

        # Connect to broker with keepalive
        try:
            self.mqtt_client.connect(
                mqtt_config['broker'],
                mqtt_config['port'],
                keepalive=mqtt_config.get('keepalive', 60)
            )
            logger.info(f"Connecting to MQTT broker: {mqtt_config['broker']}:{mqtt_config['port']}")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            self.connected = True
            logger.info("Successfully connected to MQTT broker")
            
            # Subscribe to all topics from H66
            h66_mac = self.config['mqtt']['h66_mac']
            
            # Subscribe to individual register updates
            topic = f"{h66_mac}/HP/#"
            client.subscribe(topic)
            logger.info(f"Subscribed to topic: {topic}")
            
            # Subscribe to status updates
            status_topic = f"{h66_mac}/HP/STATUS/#"
            client.subscribe(status_topic)
            logger.info(f"Subscribed to topic: {status_topic}")
            
        else:
            self.connected = False
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        self.connected = False
        if rc != 0:
            # MQTT error codes: https://github.com/eclipse/paho.mqtt.python/blob/master/src/paho/mqtt/client.py
            error_messages = {
                1: "Incorrect protocol version",
                2: "Invalid client identifier",
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized",
                7: "Connection lost"
            }
            error_msg = error_messages.get(rc, f"Unknown error (code {rc})")
            logger.warning(f"Unexpected disconnect from MQTT broker: {error_msg}")
            logger.info("Will attempt to reconnect automatically...")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg):
        """Callback when message received from MQTT"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.debug(f"Received message on topic {topic}: {payload}")
            
            # Extract register ID from topic
            # Topic format: <mac>/HP/<register_id> or <mac>/HP/STATUS/<register_id>
            parts = topic.split('/')
            
            if len(parts) >= 3:
                # Get register ID
                if parts[2] == 'STATUS' and len(parts) >= 4:
                    register_id = parts[3]
                else:
                    register_id = parts[2]
                
                # Process and store the metric
                self._process_metric(register_id, payload)
            
        except Exception as e:
            logger.error(f"Error processing message from {msg.topic}: {e}")
    
    def _process_metric(self, register_id: str, value: str):
        """Process and store a metric in InfluxDB"""
        try:
            # Get metric info from configuration
            register_id_upper = register_id.upper()
            
            if register_id_upper not in self.config['registers']:
                logger.debug(f"Unknown register: {register_id_upper}")
                return
            
            register_info = self.config['registers'][register_id_upper]
            
            # Convert value based on type
            processed_value = self.metrics_processor.process_value(
                register_id_upper,
                value,
                register_info
            )
            
            if processed_value is None:
                return
            
            # Create InfluxDB point
            point = Point("heatpump") \
                .tag("register_id", register_id_upper) \
                .tag("name", register_info['name']) \
                .tag("type", register_info['type']) \
                .field("value", processed_value) \
                .time(datetime.utcnow())
            
            # Add unit as tag if present
            if register_info.get('unit'):
                point = point.tag("unit", register_info['unit'])
            
            # Write to InfluxDB
            bucket = os.getenv('INFLUXDB_BUCKET', 'heatpump')
            self.write_api.write(bucket=bucket, record=point)
            
            logger.info(f"Stored metric: {register_info['name']} = {processed_value} {register_info.get('unit', '')}")
            
        except Exception as e:
            logger.error(f"Error storing metric {register_id}: {e}")
    
    def run(self):
        """Main run loop"""
        logger.info(f"Starting Heat Pump Data Collector for {self.provider.get_display_name()}...")
        logger.info(f"Monitoring {len(self.config['registers'])} registers")

        # Setup connections
        self._setup_influxdb()
        self._setup_mqtt()

        # Start MQTT loop
        self.mqtt_client.loop_start()

        # Keep running with reconnect logic
        reconnect_attempts = 0
        max_reconnect_attempts = 5

        try:
            while True:
                if not self.connected:
                    logger.warning("Not connected to MQTT broker, attempting to reconnect...")
                    try:
                        self.mqtt_client.reconnect()
                        reconnect_attempts += 1
                        if reconnect_attempts >= max_reconnect_attempts:
                            logger.error("Max reconnect attempts reached, waiting longer...")
                            time.sleep(60)
                            reconnect_attempts = 0
                    except Exception as e:
                        logger.error(f"Reconnect failed: {e}")
                else:
                    # Reset reconnect counter when connected
                    if reconnect_attempts > 0:
                        logger.info("Successfully reconnected to MQTT broker")
                        reconnect_attempts = 0

                time.sleep(10)

        except KeyboardInterrupt:
            logger.info("Shutting down collector...")
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            self.influx_client.close()


if __name__ == "__main__":
    # Wait a bit for other services to start
    logger.info("Waiting for services to be ready...")
    time.sleep(10)

    collector = HeatPumpCollector()
    collector.run()
