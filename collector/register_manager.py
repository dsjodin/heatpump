"""
Register Manager for Multi-Brand Heat Pump Support
Handles pump-specific register mappings and profiles
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class RegisterManager:
    """
    Manages pump-specific register profiles and provides unified access
    to register configurations across different heat pump brands.
    """
    
    def __init__(self, pump_type: str, profile_dir: str = '/app/pump_profiles'):
        """
        Initialize RegisterManager with specific pump type
        
        Args:
            pump_type: Type of pump (e.g., 'thermia_diplomat', 'ivt_greenline')
            profile_dir: Directory containing pump profile YAML files
        """
        self.pump_type = pump_type
        self.profile_dir = profile_dir
        self.registers = {}
        self.logical_map = {}  # Maps logical_name -> register_id
        self.capabilities = {}
        
        self._load_profile()
        self._build_logical_map()
        self._detect_capabilities()
    
    def _load_profile(self):
        """Load pump profile from YAML file"""
        profile_path = os.path.join(self.profile_dir, f"{self.pump_type}.yaml")
        
        if not os.path.exists(profile_path):
            raise FileNotFoundError(
                f"Pump profile not found: {profile_path}\n"
                f"Available types: thermia_diplomat, ivt_greenline"
            )
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = yaml.safe_load(f)
            
            self.registers = profile_data.get('registers', {})
            self.metadata = profile_data.get('metadata', {})
            
            logger.info(f"Loaded pump profile: {self.pump_type}")
            logger.info(f"  Brand: {self.metadata.get('brand', 'Unknown')}")
            logger.info(f"  Model: {self.metadata.get('model', 'Unknown')}")
            logger.info(f"  Registers: {len(self.registers)}")
            
        except Exception as e:
            logger.error(f"Error loading pump profile: {e}")
            raise
    
    def _build_logical_map(self):
        """Build mapping from logical names to register IDs"""
        for register_id, config in self.registers.items():
            logical_name = config.get('logical_name')
            if logical_name:
                self.logical_map[logical_name] = register_id
    
    def _detect_capabilities(self):
        """Detect what capabilities this pump has"""
        self.capabilities = {
            'has_power_measurement': 'power_consumption' in self.logical_map,
            'has_energy_measurement': 'energy_accumulated' in self.logical_map,
            'has_heat_carrier_sensors': 'heat_carrier_return' in self.logical_map,
            'has_separate_heater_steps': 'add_heat_step_1' in self.logical_map,
            'has_detailed_runtime': 'compressor_runtime_heating' in self.logical_map,
            'has_external_tank_sensor': 'warm_water_2' in self.logical_map
        }
        
        logger.info(f"Pump capabilities detected:")
        for capability, available in self.capabilities.items():
            status = "✓" if available else "✗"
            logger.info(f"  {status} {capability}")
    
    def get_register_config(self, register_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific register ID"""
        return self.registers.get(register_id.upper())
    
    def get_register_by_logical_name(self, logical_name: str) -> Optional[str]:
        """Get register ID by logical name"""
        return self.logical_map.get(logical_name)
    
    def has_capability(self, capability: str) -> bool:
        """Check if pump has a specific capability"""
        return self.capabilities.get(capability, False)
    
    def get_all_registers(self) -> Dict[str, Any]:
        """Get all register configurations"""
        return self.registers
    
    def get_register_ids(self) -> list:
        """Get list of all register IDs"""
        return list(self.registers.keys())
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get pump metadata"""
        return self.metadata
    
    def get_brand_name(self) -> str:
        """Get human-readable brand name"""
        return self.metadata.get('brand', 'Unknown')
    
    def get_model_name(self) -> str:
        """Get human-readable model name"""
        return self.metadata.get('model', 'Unknown')
    
    def get_alarm_codes(self) -> Dict[int, str]:
        """Get alarm code descriptions for this pump"""
        return self.metadata.get('alarm_codes', {})
    
    def validate_register_availability(self, required_registers: list) -> Dict[str, bool]:
        """
        Validate that required registers are available
        
        Args:
            required_registers: List of logical names or register IDs
            
        Returns:
            Dict mapping register to availability status
        """
        availability = {}
        
        for register in required_registers:
            # Check if it's a logical name first
            if register in self.logical_map:
                availability[register] = True
            # Then check if it's a register ID
            elif register.upper() in self.registers:
                availability[register] = True
            else:
                availability[register] = False
        
        return availability
