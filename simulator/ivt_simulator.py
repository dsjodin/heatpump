"""
IVT Heat Pump Simulator
Generates metrics matching IVT heat pump format
IVT uses slightly different naming conventions
"""

from typing import Dict, Any
from .base_simulator import BaseHeatPumpSimulator


class IVTSimulator(BaseHeatPumpSimulator):
    """Simulator for IVT heat pumps"""

    def __init__(self):
        super().__init__(manufacturer="IVT")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Generate IVT-formatted metrics
        IVT uses different naming: GT (from Swedish "givartemperatur" - sensor temp)
        """

        cop = self._calculate_cop()
        power = self._calculate_power_consumption()

        # IVT metric naming convention
        metrics = {
            # Temperatures - IVT uses GT prefix
            'gt1_outdoor': round(self.outdoor_temp, 1),           # GT1 = Outdoor
            'gt2_supply': round(self.radiator_forward_temp, 1),   # GT2 = Supply/Forward
            'gt3_return': round(self.radiator_return_temp, 1),    # GT3 = Return
            'gt5_brine_in': round(self.brine_in_temp, 1),         # GT5 = Brine in
            'gt6_brine_out': round(self.brine_out_temp, 1),       # GT6 = Brine out
            'gt8_hot_water': round(self.hot_water_temp, 1),       # GT8 = Hot water
            'gt10_indoor': round(self.indoor_temp, 1),            # GT10 = Indoor

            # Status values - IVT uses EB (relay outputs)
            'eb1_compressor': 1 if self.compressor_on else 0,     # EB1 = Compressor
            'eb2_aux_heater': 1 if self.aux_heater_on else 0,     # EB2 = Aux heater
            'eb3_brine_pump': 1 if self.compressor_on else 0,     # EB3 = Brine pump
            'eb4_radiator_pump': 1 if self.compressor_on else 0,  # EB4 = Radiator pump
            'eb7_3way_valve': 1 if self.hot_water_mode else 0,    # EB7 = 3-way valve

            # Power
            'power_meter': round(power, 0),

            # Calculated
            'cop_current': round(cop, 2) if cop > 0 else None,

            # Counters (IVT tracks these)
            'compressor_starts': int(self.compressor_on_time / 1800),  # Estimate starts
            'operating_hours_compressor': round(self.compressor_on_time / 3600, 1),
            'operating_hours_aux': round(self.aux_heater_on_time / 3600, 1),
        }

        return metrics

    def get_mqtt_topic_mapping(self) -> Dict[str, str]:
        """
        Return MQTT topic mapping for IVT
        IVT often uses ModBus registers or MQTT topics
        """
        return {
            'gt1_outdoor': 'ivt/sensors/gt1',
            'gt2_supply': 'ivt/sensors/gt2',
            'gt3_return': 'ivt/sensors/gt3',
            'gt5_brine_in': 'ivt/sensors/gt5',
            'gt6_brine_out': 'ivt/sensors/gt6',
            'gt8_hot_water': 'ivt/sensors/gt8',
            'gt10_indoor': 'ivt/sensors/gt10',
            'eb1_compressor': 'ivt/relays/eb1',
            'eb2_aux_heater': 'ivt/relays/eb2',
            'eb3_brine_pump': 'ivt/relays/eb3',
            'eb4_radiator_pump': 'ivt/relays/eb4',
            'eb7_3way_valve': 'ivt/relays/eb7',
            'power_meter': 'ivt/power',
        }

    def get_metric_mapping(self) -> Dict[str, str]:
        """
        Map IVT metric names to standard dashboard names
        This allows the dashboard to work with different manufacturers
        """
        return {
            'gt1_outdoor': 'outdoor_temp',
            'gt10_indoor': 'indoor_temp',
            'gt5_brine_in': 'brine_in_evaporator',
            'gt6_brine_out': 'brine_out_condenser',
            'gt2_supply': 'radiator_forward',
            'gt3_return': 'radiator_return',
            'gt8_hot_water': 'hot_water_top',
            'eb1_compressor': 'compressor_status',
            'eb3_brine_pump': 'brine_pump_status',
            'eb4_radiator_pump': 'radiator_pump_status',
            'eb7_3way_valve': 'switch_valve_status',
            'power_meter': 'power_consumption',
            'eb2_aux_heater': 'aux_heater_status',
            'cop_current': 'estimated_cop',
        }
