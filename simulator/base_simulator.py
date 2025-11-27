"""
Base Heat Pump Simulator
Provides realistic heat pump metric generation with time-based variations
"""

import random
import math
import time
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseHeatPumpSimulator:
    """Base class for heat pump simulators with realistic physics"""

    def __init__(self, manufacturer: str = "Generic"):
        self.manufacturer = manufacturer
        self.start_time = time.time()

        # Operating state
        self.compressor_on = False
        self.hot_water_mode = False
        self.aux_heater_on = False

        # Cycle timers
        self.last_compressor_change = time.time()
        self.last_mode_change = time.time()
        self.compressor_on_time = 0
        self.aux_heater_on_time = 0

        # Environmental conditions
        self.outdoor_temp = -5.0  # Default winter temperature
        self.indoor_temp_setpoint = 21.0

        # Current values (will vary over time)
        self.indoor_temp = 20.5
        self.brine_in_temp = 0.5
        self.brine_out_temp = -3.0
        self.radiator_forward_temp = 35.0
        self.radiator_return_temp = 30.0
        self.hot_water_temp = 50.0

        logger.info(f"Initialized {manufacturer} heat pump simulator")

    def set_outdoor_temp(self, temp: float):
        """Set outdoor temperature (affects all other temps)"""
        self.outdoor_temp = temp

    def _update_operating_state(self):
        """Update compressor and mode states based on realistic cycles"""
        current_time = time.time()
        elapsed = current_time - self.start_time

        # Compressor cycles: ON for 20-45 min, OFF for 10-30 min
        if self.compressor_on:
            if current_time - self.last_compressor_change > random.uniform(1200, 2700):
                self.compressor_on = False
                self.last_compressor_change = current_time
                logger.debug("Compressor turned OFF")
        else:
            if current_time - self.last_compressor_change > random.uniform(600, 1800):
                self.compressor_on = True
                self.last_compressor_change = current_time
                logger.debug("Compressor turned ON")

        # Hot water mode: Switch every 2-4 hours for 30-60 minutes
        if self.hot_water_mode:
            if current_time - self.last_mode_change > random.uniform(1800, 3600):
                self.hot_water_mode = False
                self.last_mode_change = current_time
                logger.debug("Switched to HEATING mode")
        else:
            if current_time - self.last_mode_change > random.uniform(7200, 14400):
                self.hot_water_mode = True
                self.last_mode_change = current_time
                logger.debug("Switched to HOT WATER mode")

        # Aux heater: Only when very cold and compressor can't keep up
        self.aux_heater_on = (
            self.outdoor_temp < -10 and
            self.compressor_on and
            random.random() < 0.3
        )

        # Track operating hours
        if self.compressor_on:
            self.compressor_on_time += 1
        if self.aux_heater_on:
            self.aux_heater_on_time += 1

    def _calculate_cop(self) -> float:
        """Calculate realistic COP based on temperatures"""
        if not self.compressor_on:
            return 0.0

        # COP depends on temperature difference
        # Better COP with higher brine temp and lower forward temp
        brine_avg = (self.brine_in_temp + self.brine_out_temp) / 2
        forward_temp = self.radiator_forward_temp

        # Base COP from Carnot efficiency (simplified)
        temp_diff = forward_temp - brine_avg
        if temp_diff <= 0:
            return 3.5

        base_cop = 3.5 + (10 - temp_diff) / 10

        # Add some realistic variation
        cop = base_cop + random.uniform(-0.2, 0.2)

        # Clamp to realistic range
        return max(1.5, min(6.0, cop))

    def _simulate_temperatures(self):
        """Simulate realistic temperature changes based on operating state"""

        # Indoor temperature slowly drifts toward setpoint
        if self.indoor_temp < self.indoor_temp_setpoint - 0.5:
            self.indoor_temp += random.uniform(0.01, 0.05)
        elif self.indoor_temp > self.indoor_temp_setpoint + 0.5:
            self.indoor_temp -= random.uniform(0.01, 0.05)
        else:
            self.indoor_temp += random.uniform(-0.02, 0.02)

        if self.compressor_on:
            # Compressor running - temperatures move toward operating values

            # Brine circuit (evaporator side)
            self.brine_in_temp = self.outdoor_temp + random.uniform(0.5, 2.0)
            self.brine_out_temp = self.brine_in_temp - random.uniform(3.0, 5.0)

            if self.hot_water_mode:
                # Hot water mode: Higher forward temp
                self.radiator_forward_temp = random.uniform(50, 60)
                self.radiator_return_temp = self.radiator_forward_temp - random.uniform(8, 12)

                # Hot water heating up
                if self.hot_water_temp < 55:
                    self.hot_water_temp += random.uniform(0.5, 1.5)
            else:
                # Heating mode: Normal radiator temps
                # Forward temp depends on outdoor temp (weather compensation)
                target_forward = 45 - (self.outdoor_temp * 1.2)
                target_forward = max(30, min(55, target_forward))

                self.radiator_forward_temp += (target_forward - self.radiator_forward_temp) * 0.1
                self.radiator_return_temp = self.radiator_forward_temp - random.uniform(5, 10)

                # Hot water cooling down slowly
                if self.hot_water_temp > 45:
                    self.hot_water_temp -= random.uniform(0.05, 0.15)

            # Aux heater adds extra heat
            if self.aux_heater_on:
                self.radiator_forward_temp += random.uniform(2, 5)
        else:
            # Compressor off - temperatures drift toward ambient
            self.brine_in_temp += (self.outdoor_temp - self.brine_in_temp) * 0.05
            self.brine_out_temp += (self.outdoor_temp - self.brine_out_temp) * 0.05

            self.radiator_forward_temp -= random.uniform(0.2, 0.5)
            self.radiator_return_temp -= random.uniform(0.1, 0.3)

            # Hot water cooling down
            if self.hot_water_temp > 40:
                self.hot_water_temp -= random.uniform(0.1, 0.2)

    def _calculate_power_consumption(self) -> float:
        """Calculate realistic power consumption"""
        if not self.compressor_on:
            return random.uniform(20, 50)  # Standby power

        # Base compressor power
        base_power = random.uniform(1200, 1600)

        # Higher power in hot water mode
        if self.hot_water_mode:
            base_power += random.uniform(200, 400)

        # Aux heater adds significant power
        if self.aux_heater_on:
            base_power += random.uniform(2000, 3000)

        # Power varies with outdoor temp (harder to compress when cold)
        temp_factor = 1.0 + ((-5 - self.outdoor_temp) * 0.02)

        return base_power * temp_factor

    def get_metrics(self) -> Dict[str, Any]:
        """
        Generate current metrics
        Must be overridden by manufacturer-specific simulators
        """
        raise NotImplementedError("Subclass must implement get_metrics()")

    def update(self):
        """Update simulation state (call this periodically)"""
        self._update_operating_state()
        self._simulate_temperatures()
