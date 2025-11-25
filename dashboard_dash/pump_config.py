"""
Pump Configuration Helper for Dashboard
Centralized config loading for pump-specific features
"""

import os
import yaml
import logging

logger = logging.getLogger(__name__)

_config_cache = None


def load_config():
    """Load configuration from config.yaml"""
    global _config_cache
    
    if _config_cache is not None:
        return _config_cache
    
    config_path = os.getenv('CONFIG_PATH', '/app/config.yaml')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            _config_cache = yaml.safe_load(f)
        return _config_cache
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        # Return default config
        return {
            'system': {
                'pump_type': 'thermia_diplomat',
                'pump_model': 'Thermia Heat Pump'
            }
        }


def get_pump_type():
    """Get configured pump type"""
    config = load_config()
    return config.get('system', {}).get('pump_type', 'thermia_diplomat')


def get_pump_model():
    """Get configured pump model name"""
    config = load_config()
    return config.get('system', {}).get('pump_model', 'Heat Pump')


def get_pump_brand():
    """Get pump brand name"""
    pump_type = get_pump_type()
    
    brands = {
        'thermia_diplomat': 'Thermia',
        'ivt_greenline': 'IVT'
    }
    
    return brands.get(pump_type, 'Unknown')


def is_thermia():
    """Check if current pump is Thermia"""
    return get_pump_type() == 'thermia_diplomat'


def is_ivt():
    """Check if current pump is IVT"""
    return get_pump_type() == 'ivt_greenline'


def has_power_measurement():
    """Check if pump supports direct power measurement"""
    # Thermia has CFAA power register
    return is_thermia()


def has_energy_measurement():
    """Check if pump supports direct energy measurement"""
    # Thermia has 5FAB energy register
    return is_thermia()


def has_heat_carrier_sensors():
    """Check if pump has internal heat carrier sensors"""
    # IVT has 0003/0004 heat carrier sensors
    return is_ivt()


def has_separate_heater_steps():
    """Check if pump has separate heater step indicators"""
    # IVT has 1A02/1A03 for 3kW/6kW steps
    return is_ivt()


def has_detailed_runtime():
    """Check if pump has detailed runtime breakdowns"""
    # IVT has 6C55/6C56/6C58/6C59 for heating/hotwater splits
    return is_ivt()


def has_external_tank_sensor():
    """Check if pump supports external tank sensor"""
    # IVT has 000A warm water 2 sensor
    return is_ivt()


def get_capabilities():
    """Get dict of all pump capabilities"""
    return {
        'has_power_measurement': has_power_measurement(),
        'has_energy_measurement': has_energy_measurement(),
        'has_heat_carrier_sensors': has_heat_carrier_sensors(),
        'has_separate_heater_steps': has_separate_heater_steps(),
        'has_detailed_runtime': has_detailed_runtime(),
        'has_external_tank_sensor': has_external_tank_sensor()
    }


def get_dashboard_title():
    """Get formatted dashboard title"""
    brand = get_pump_brand()
    model = get_pump_model()
    return f"{brand} Värmepump Monitor"


def get_dashboard_subtitle():
    """Get dashboard subtitle based on capabilities"""
    if is_thermia():
        return "Avancerad övervakning med COP, kostnader och prestandaanalys"
    elif is_ivt():
        return "Detaljerad övervakning med runtime-analys och systemstatus"
    else:
        return "Värmepump övervakning"
