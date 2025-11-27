#!/usr/bin/env python3
"""
Heat Pump Simulator
Generates realistic heat pump metrics and publishes to MQTT
Can simulate Thermia, IVT, or NIBE heat pumps
"""

import os
import sys
import time
import yaml
import json
import logging
import signal
from datetime import datetime
from typing import Optional

import paho.mqtt.client as mqtt

# Add parent directory to path to import simulator modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator import ThermiaSimulator, IVTSimulator, NIBESimulator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class HeatPumpSimulatorRunner:
    """Main simulator runner that publishes to MQTT"""

    def __init__(self, config_path: str = 'config.yaml'):
        self.config = self._load_config(config_path)
        self.simulator = None
        self.mqtt_client = None
        self.running = False

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def _create_simulator(self, manufacturer: str):
        """Create appropriate simulator based on manufacturer"""
        manufacturer = manufacturer.lower()

        if manufacturer == 'thermia':
            return ThermiaSimulator()
        elif manufacturer == 'ivt':
            return IVTSimulator()
        elif manufacturer == 'nibe':
            return NIBESimulator()
        else:
            logger.error(f"Unknown manufacturer: {manufacturer}")
            sys.exit(1)

    def _setup_mqtt(self):
        """Setup MQTT client"""
        mqtt_config = self.config['mqtt']

        self.mqtt_client = mqtt.Client(
            client_id=mqtt_config.get('client_id', 'heatpump_simulator'),
            clean_session=True
        )

        # Set callbacks
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect

        # Connect to broker
        try:
            logger.info(f"Connecting to MQTT broker at {mqtt_config['broker']}:{mqtt_config['port']}")
            self.mqtt_client.connect(
                mqtt_config['broker'],
                mqtt_config['port'],
                keepalive=60
            )
            self.mqtt_client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            sys.exit(1)

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            logger.info("✅ Connected to MQTT broker")
        else:
            logger.error(f"❌ MQTT connection failed with code {rc}")

    def _on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnect (rc={rc})")

    def _publish_metrics(self, metrics: dict, topic_mapping: dict):
        """Publish metrics to MQTT"""
        for metric_name, value in metrics.items():
            # Skip None values
            if value is None:
                continue

            # Get MQTT topic for this metric
            topic = topic_mapping.get(metric_name)
            if not topic:
                # Use default topic structure if not mapped
                topic = f"simulator/{self.config['simulator']['manufacturer']}/{metric_name}"

            # Publish as JSON payload
            payload = json.dumps({
                'value': value,
                'timestamp': datetime.now().isoformat(),
                'metric': metric_name
            })

            try:
                self.mqtt_client.publish(topic, payload, qos=1)
            except Exception as e:
                logger.error(f"Failed to publish {metric_name}: {e}")

    def run(self):
        """Main simulation loop"""
        sim_config = self.config.get('simulator', {})

        if not sim_config.get('enabled', False):
            logger.info("Simulator is disabled in config")
            return

        # Create simulator
        manufacturer = sim_config.get('manufacturer', 'thermia')
        logger.info(f"Initializing {manufacturer.upper()} heat pump simulator")
        self.simulator = self._create_simulator(manufacturer)

        # Set initial outdoor temperature
        outdoor_temp = sim_config.get('outdoor_temp', -5)
        self.simulator.set_outdoor_temp(outdoor_temp)
        logger.info(f"Set outdoor temperature to {outdoor_temp}°C")

        # Setup MQTT
        self._setup_mqtt()

        # Get update interval
        update_interval = sim_config.get('update_interval', 10)
        logger.info(f"Update interval: {update_interval} seconds")

        # Get topic mapping
        topic_mapping = {}
        if hasattr(self.simulator, 'get_mqtt_topic_mapping'):
            topic_mapping = self.simulator.get_mqtt_topic_mapping()

        # Main loop
        self.running = True
        iteration = 0

        logger.info("🚀 Starting simulation loop...")

        try:
            while self.running:
                iteration += 1

                # Update simulation state
                self.simulator.update()

                # Get current metrics
                metrics = self.simulator.get_metrics()

                # Publish to MQTT
                self._publish_metrics(metrics, topic_mapping)

                # Log summary
                if iteration % 6 == 0:  # Every minute with 10s interval
                    logger.info(
                        f"📊 Compressor: {'ON' if metrics.get('compressor_status', 0) else 'OFF'} | "
                        f"Mode: {'Hot Water' if metrics.get('switch_valve_status', 0) else 'Heating'} | "
                        f"Outdoor: {metrics.get('outdoor_temp', 0):.1f}°C | "
                        f"Forward: {metrics.get('radiator_forward', 0):.1f}°C | "
                        f"COP: {metrics.get('estimated_cop', 0) or '--'}"
                    )

                # Sleep
                time.sleep(update_interval)

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self._cleanup()

    def _cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up...")
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        logger.info("Simulator stopped")


def main():
    """Entry point"""
    config_path = os.getenv('CONFIG_PATH', '/app/config.yaml')

    logger.info("=" * 60)
    logger.info("Heat Pump Simulator")
    logger.info("Supports: Thermia, IVT, NIBE")
    logger.info("=" * 60)

    runner = HeatPumpSimulatorRunner(config_path)
    runner.run()


if __name__ == '__main__':
    main()
