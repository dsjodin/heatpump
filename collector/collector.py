#!/usr/bin/env python3
"""
Thermia Heat Pump Data Collector
Subscribes to MQTT topics from H66 Gateway and stores data in InfluxDB
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

from metrics import MetricsProcessor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ThermiaCollector:
    """Main collector class for Thermia heat pump data"""
    
    def __init__(self, config_path: str = '/app/config.yaml'):
        """Initialize the collector with configuration"""
        self.config = self._load_config(config_path)
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
            'registers': self._get_default_registers(),
            'dashboard': {
                'title': 'Thermia Heat Pump Monitor',
                'refresh_interval': 30,
                'time_ranges': ['1h', '6h', '24h', '7d', '30d', '90d']
            }
        }
        
        return config
    
    def _get_default_registers(self) -> Dict[str, Any]:
        """Return default register configuration - CORRECTED based on official Husdata docs"""
        return {
            "0001": {"name": "radiator_return", "unit": "°C", "type": "temperature", "description": "Radiator return temperature"},
            "0002": {"name": "radiator_forward", "unit": "°C", "type": "temperature", "description": "Radiator forward temperature"},
            "0005": {"name": "brine_in_evaporator", "unit": "°C", "type": "temperature", "description": "Brine in/Evaporator temp"},
            "0006": {"name": "brine_out_condenser", "unit": "°C", "type": "temperature", "description": "Brine out/Condenser temp"},
            "0007": {"name": "outdoor_temp", "unit": "°C", "type": "temperature", "description": "Outdoor temperature"},
            "0008": {"name": "indoor_temp", "unit": "°C", "type": "temperature", "description": "Indoor temperature"},
            "0009": {"name": "hot_water_top", "unit": "°C", "type": "temperature", "description": "Hot water top temperature"},
            "0012": {"name": "pressure_tube_temp", "unit": "°C", "type": "temperature", "description": "Temp after compressor"},
            "0013": {"name": "cooling_temp", "unit": "°C", "type": "temperature", "description": "Cooling circuit temp"},
            "0107": {"name": "heating_setpoint", "unit": "°C", "type": "temperature", "description": "Heating target temp"},
            "3109": {"name": "circulation_pump_speed", "unit": "%", "type": "percentage", "description": "Circulation pump speed"},
            "3110": {"name": "brine_pump_speed", "unit": "%", "type": "percentage", "description": "Brine pump speed"},
            "1A01": {"name": "compressor_status", "unit": "", "type": "status", "description": "Compressor on/off"},
            "1A04": {"name": "brine_pump_status", "unit": "", "type": "status", "description": "Brine pump status"},
            "1A06": {"name": "radiator_pump_status", "unit": "", "type": "status", "description": "Radiator pump status"},
            "1A07": {"name": "switch_valve_status", "unit": "", "type": "status", "description": "Switch valve position"},
            "3104": {"name": "additional_heat_percent", "unit": "%", "type": "percentage", "description": "Additional heater percentage"},
            "1A20": {"name": "alarm_status", "unit": "", "type": "alarm", "description": "Alarm status"},
            "2A91": {"name": "alarm_code", "unit": "", "type": "alarm", "description": "Alarm code"},
            "2201": {"name": "operating_mode", "unit": "", "type": "setting", "description": "Operational mode"},
            "0203": {"name": "room_temp_setpoint", "unit": "°C", "type": "temperature", "description": "Room temp setpoint"},
            "2204": {"name": "room_sensor_influence", "unit": "°C", "type": "setting", "description": "Room sensor influence"},
            "0205": {"name": "heat_curve_L", "unit": "°C", "type": "setting", "description": "Heat curve L"},
            "0206": {"name": "heat_curve_R", "unit": "°C", "type": "setting", "description": "Heat curve R"},
            "0208": {"name": "hot_water_stop_temp", "unit": "°C", "type": "temperature", "description": "Hot water stop temp"},
            "0211": {"name": "heating_stop_temp", "unit": "°C", "type": "temperature", "description": "Heating stop temp"},
            "0212": {"name": "hot_water_start_temp", "unit": "°C", "type": "temperature", "description": "Hot water start temp"},
            "0214": {"name": "cooling_setpoint", "unit": "°C", "type": "temperature", "description": "Cooling setpoint"},
            "0217": {"name": "outdoor_temp_offset", "unit": "°C", "type": "temperature", "description": "Outdoor temp offset"},
            "0233": {"name": "external_control", "unit": "°C", "type": "setting", "description": "External control reduction"},
            "8105": {"name": "degree_minutes", "unit": "", "type": "setting", "description": "Degree minutes integral"},
            "6C60": {"name": "compressor_runtime", "unit": "hours", "type": "runtime", "description": "Compressor runtime"},
            "6C63": {"name": "aux_heater_3kw_runtime", "unit": "hours", "type": "runtime", "description": "3kW heater runtime"},
            "6C64": {"name": "hot_water_runtime", "unit": "hours", "type": "runtime", "description": "Hot water runtime"},
            "6C66": {"name": "aux_heater_6kw_runtime", "unit": "hours", "type": "runtime", "description": "6kW heater runtime"},
            "CFAA": {"name": "power_consumption", "unit": "W", "type": "power", "description": "Current power consumption"},
            "5FAB": {"name": "energy_accumulated", "unit": "kWh", "type": "energy", "description": "Accumulated energy"}
        }
    
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
        
        self.mqtt_client = mqtt.Client(client_id=mqtt_config['client_id'])
        self.mqtt_client.username_pw_set(
            mqtt_config['username'],
            mqtt_config['password']
        )
        
        # Set callbacks
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_disconnect = self._on_disconnect
        self.mqtt_client.on_message = self._on_message
        
        # Connect to broker
        try:
            self.mqtt_client.connect(
                mqtt_config['broker'],
                mqtt_config['port'],
                keepalive=60
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
            logger.warning(f"Unexpected disconnect from MQTT broker. Return code: {rc}")
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
        logger.info("Starting Thermia Data Collector...")
        
        # Setup connections
        self._setup_influxdb()
        self._setup_mqtt()
        
        # Start MQTT loop
        self.mqtt_client.loop_start()
        
        # Keep running
        try:
            while True:
                if not self.connected:
                    logger.warning("Not connected to MQTT broker, waiting...")
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
    
    collector = ThermiaCollector()
    collector.run()
