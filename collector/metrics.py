"""
Metrics Processor for Thermia Heat Pump Data
Handles data conversion and validation for different metric types
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MetricsProcessor:
    """Process and convert heat pump metrics"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration"""
        self.config = config
    
    def process_value(self, register_id: str, raw_value: str, register_info: Dict[str, Any]) -> Optional[float]:
        """
        Process a raw value based on its type
        
        Args:
            register_id: Register identifier
            raw_value: Raw value from MQTT
            register_info: Register configuration
            
        Returns:
            Processed numeric value or None if invalid
        """
        try:
            metric_type = register_info.get('type', 'unknown')
            
            # Convert to number
            try:
                value = float(raw_value)
            except (ValueError, TypeError):
                logger.warning(f"Invalid numeric value for {register_id}: {raw_value}")
                return None
            
            # Process based on type
            if metric_type == 'temperature':
                return self._process_temperature(value)
            elif metric_type == 'status':
                return self._process_status(value)
            elif metric_type == 'power':
                return self._process_power(value)
            elif metric_type == 'energy':
                return self._process_energy(value)
            elif metric_type == 'percentage':
                return self._process_percentage(value)
            elif metric_type == 'setting':
                return self._process_setting(value)
            elif metric_type == 'alarm':
                return self._process_alarm(value)
            elif metric_type == 'runtime':
                return self._process_runtime(value)
            else:
                # Unknown type, return as-is
                return value
                
        except Exception as e:
            logger.error(f"Error processing value for {register_id}: {e}")
            return None
    
    def _process_temperature(self, value: float) -> Optional[float]:
        """
        Process temperature values
        
        NOTE: Some H66 firmwares send temperatures already in correct format (54.0 for 54°C)
        while older firmwares send multiplied by 10 (540 for 54°C).
        
        This version handles H66s that send actual values (no multiplication).
        If your temps are 10x too large, you may have an older H66 that needs division by 10.
        
        Also handles negative temperatures sent via two's complement encoding.
        """
        # Check if this is a negative temperature (two's complement encoding)
        # This happens for negative values in 16-bit unsigned representation
        if value > 32768:
            # This is a negative temperature in two's complement
            value = value - 65536
        
        # H66 sends actual temperature value - NO division needed
        temp = value
        
        # Sanity check: temperatures should be reasonable
        if temp < -50 or temp > 150:
            logger.warning(f"Temperature out of range: {temp}°C, raw MQTT value was: {value}")
            return None
        
        return round(temp, 1)
    
    def _process_status(self, value: float) -> float:
        """
        Process status values (typically 0 or 1)
        """
        # Status values are typically 0 (off) or 1 (on)
        # Sometimes they can be other values, so we keep the raw value
        return value
    
    def _process_power(self, value: float) -> float:
        """
        Process power consumption values (Watts)
        """
        # Power values should be positive
        if value < 0:
            logger.warning(f"Negative power value: {value}")
            return 0.0
        
        return round(value, 1)
    
    def _process_energy(self, value: float) -> float:
        """
        Process accumulated energy values (kWh)
        """
        # Energy values should be positive
        if value < 0:
            logger.warning(f"Negative energy value: {value}")
            return 0.0
        
        return round(value, 2)
    
    def _process_percentage(self, value: float) -> float:
        """
        Process percentage values (0-100)
        """
        # Clamp to valid percentage range
        if value < 0:
            return 0.0
        if value > 100:
            return 100.0
        
        return round(value, 1)
    
    def _process_setting(self, value: float) -> float:
        """
        Process setting values (heat curve, operating mode, etc.)
        
        H66 sends settings in their actual format - no conversion needed
        """
        return value
    
    def _process_alarm(self, value: float) -> float:
        """
        Process alarm codes
        0 = no alarm, other values indicate alarm codes
        Return as float to match InfluxDB field type
        """
        return float(value)
    
    def _process_runtime(self, value: float) -> float:
        """
        Process runtime values (hours)
        Runtime counters should always be positive
        """
        if value < 0:
            logger.warning(f"Negative runtime value: {value}")
            return 0.0
        
        return round(value, 1)
    
    def validate_metric(self, register_id: str, value: float) -> bool:
        """
        Validate if a metric value is reasonable
        
        Args:
            register_id: Register identifier
            value: Processed value
            
        Returns:
            True if valid, False otherwise
        """
        register_info = self.config['registers'].get(register_id)
        
        if not register_info:
            return True  # Unknown registers pass through
        
        metric_type = register_info.get('type', 'unknown')
        
        # Type-specific validation
        if metric_type == 'temperature':
            return -50 <= value <= 150
        elif metric_type == 'status':
            return True  # All status values are valid
        elif metric_type == 'power':
            return 0 <= value <= 50000  # Max 50kW seems reasonable
        elif metric_type == 'energy':
            return value >= 0
        elif metric_type == 'percentage':
            return 0 <= value <= 100
        elif metric_type == 'alarm':
            return value >= 0
        
        return True
