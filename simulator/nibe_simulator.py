"""
NIBE Heat Pump Simulator
Generates metrics matching NIBE heat pump format
NIBE uses ModBus register numbers as identifiers
"""

from typing import Dict, Any
from .base_simulator import BaseHeatPumpSimulator


class NIBESimulator(BaseHeatPumpSimulator):
    """Simulator for NIBE heat pumps (S/F-series)"""

    def __init__(self):
        super().__init__(manufacturer="NIBE")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Generate NIBE-formatted metrics
        NIBE uses register numbers (40xxx range for readings)
        """

        cop = self._calculate_cop()
        power = self._calculate_power_consumption()

        # NIBE register-based naming
        # Common registers from NIBE F/S series
        metrics = {
            # Temperatures (40xxx registers)
            '40004': round(self.outdoor_temp, 1),           # BT1 Outdoor temp
            '40008': round(self.radiator_forward_temp, 1),  # BT2 Supply temp S1
            '40012': round(self.radiator_return_temp, 1),   # BT3 Return temp
            '40013': round(self.hot_water_temp, 1),         # BT7 Hot water top
            '40014': round(self.hot_water_temp - 5, 1),     # BT6 Hot water charged
            '40015': round(self.brine_in_temp, 1),          # BT10 Brine in
            '40016': round(self.brine_out_temp, 1),         # BT11 Brine out
            '40033': round(self.indoor_temp, 1),            # BT50 Room temp S1

            # Current values
            '40072': round(cop * 10, 0),                    # COP (multiplied by 10)
            '40074': round(power, 0),                       # Compressor frequency/power

            # Status registers (43xxx for status)
            '43086': 20 if self.compressor_on else 0,       # Compressor status
            '43108': 1 if self.hot_water_mode else 0,       # Hot water mode
            '43091': 1 if self.aux_heater_on else 0,        # Additional heat status

            # Degree minutes (used for heating curves)
            '43005': int((18 - self.outdoor_temp) * 100),   # Degree minutes

            # Operating time (48xxx for counters)
            '48043': int(self.compressor_on_time / 3600),   # Compressor operating time
            '48044': int(self.aux_heater_on_time / 3600),   # Add. heat operating time

            # Priority (what system is doing)
            '43136': 30 if self.hot_water_mode else 10,     # Priority: 10=Heat, 30=Hot water, 40=Pool

            # Pump speeds (0-100%)
            '43166': 80 if self.compressor_on else 0,       # Brine pump speed
            '43171': 70 if self.compressor_on else 0,       # Heat carrier pump speed
        }

        return metrics

    def get_mqtt_topic_mapping(self) -> Dict[str, str]:
        """
        Return MQTT topic mapping for NIBE
        Often published via nibe2mqtt or similar integrations
        """
        return {
            '40004': 'nibe/40004/value',  # BT1
            '40008': 'nibe/40008/value',  # BT2
            '40012': 'nibe/40012/value',  # BT3
            '40013': 'nibe/40013/value',  # BT7
            '40015': 'nibe/40015/value',  # BT10
            '40016': 'nibe/40016/value',  # BT11
            '40033': 'nibe/40033/value',  # BT50
            '40072': 'nibe/40072/value',  # COP
            '40074': 'nibe/40074/value',  # Power
            '43086': 'nibe/43086/value',  # Compressor
            '43108': 'nibe/43108/value',  # Mode
            '43091': 'nibe/43091/value',  # Add heat
            '48043': 'nibe/48043/value',  # Hours compressor
            '48044': 'nibe/48044/value',  # Hours aux
        }

    def get_metric_mapping(self) -> Dict[str, str]:
        """
        Map NIBE register numbers to standard dashboard names
        """
        return {
            '40004': 'outdoor_temp',            # BT1
            '40033': 'indoor_temp',             # BT50
            '40015': 'brine_in_evaporator',     # BT10
            '40016': 'brine_out_condenser',     # BT11
            '40008': 'radiator_forward',        # BT2
            '40012': 'radiator_return',         # BT3
            '40013': 'hot_water_top',           # BT7
            '43086': 'compressor_status',       # Compressor (normalize to 0/1)
            '43166': 'brine_pump_status',       # Brine pump (normalize to 0/1)
            '43171': 'radiator_pump_status',    # Heat pump (normalize to 0/1)
            '43108': 'switch_valve_status',     # Mode
            '40074': 'power_consumption',       # Power
            '43091': 'aux_heater_status',       # Add heat
            '40072': 'estimated_cop',           # COP (divide by 10)
        }

    def normalize_value(self, register: str, value: Any) -> Any:
        """
        Normalize NIBE-specific values to standard format
        """
        # COP is multiplied by 10 in NIBE
        if register == '40072':
            return value / 10.0 if value else None

        # Compressor status: 20=running, map to 1
        if register == '43086':
            return 1 if value == 20 else 0

        # Pump speeds > 0 means running
        if register in ['43166', '43171']:
            return 1 if value > 0 else 0

        return value
