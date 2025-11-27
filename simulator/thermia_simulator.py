"""
Thermia Heat Pump Simulator
Generates metrics matching Thermia heat pump format
"""

from typing import Dict, Any
from .base_simulator import BaseHeatPumpSimulator


class ThermiaSimulator(BaseHeatPumpSimulator):
    """Simulator for Thermia heat pumps"""

    def __init__(self):
        super().__init__(manufacturer="Thermia")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Generate Thermia-formatted metrics
        Matches the metrics currently used in the dashboard
        """

        cop = self._calculate_cop()
        power = self._calculate_power_consumption()

        # Thermia uses these exact metric names
        metrics = {
            # Temperatures
            'outdoor_temp': round(self.outdoor_temp, 1),
            'indoor_temp': round(self.indoor_temp, 1),
            'brine_in_evaporator': round(self.brine_in_temp, 1),
            'brine_out_condenser': round(self.brine_out_temp, 1),
            'radiator_forward': round(self.radiator_forward_temp, 1),
            'radiator_return': round(self.radiator_return_temp, 1),
            'hot_water_top': round(self.hot_water_temp, 1),

            # Status values (0 or 1)
            'compressor_status': 1 if self.compressor_on else 0,
            'brine_pump_status': 1 if self.compressor_on else 0,
            'radiator_pump_status': 1 if self.compressor_on else 0,
            'switch_valve_status': 1 if self.hot_water_mode else 0,  # 1=Hot water, 0=Heating

            # Power and auxiliary
            'power_consumption': round(power, 0),
            'additional_heat_percent': round(50.0 if self.aux_heater_on else 0.0, 1),

            # Calculated values
            'estimated_cop': round(cop, 2) if cop > 0 else None,

            # Operating hours (cumulative)
            'compressor_hours': round(self.compressor_on_time / 3600, 1),
            'aux_heater_hours': round(self.aux_heater_on_time / 3600, 1),
        }

        return metrics

    def get_mqtt_topic_mapping(self) -> Dict[str, str]:
        """
        Return MQTT topic mapping for Thermia
        Format: metric_name -> MQTT topic
        """
        return {
            'outdoor_temp': 'thermia/outdoor_temp',
            'indoor_temp': 'thermia/indoor_temp',
            'brine_in_evaporator': 'thermia/brine_in',
            'brine_out_condenser': 'thermia/brine_out',
            'radiator_forward': 'thermia/radiator_forward',
            'radiator_return': 'thermia/radiator_return',
            'hot_water_top': 'thermia/hot_water_top',
            'compressor_status': 'thermia/compressor',
            'brine_pump_status': 'thermia/brine_pump',
            'radiator_pump_status': 'thermia/radiator_pump',
            'switch_valve_status': 'thermia/switch_valve',
            'power_consumption': 'thermia/power',
            'additional_heat_percent': 'thermia/aux_heat_percent',
        }
