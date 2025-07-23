#!/usr/bin/env python3
"""
Equipment Configuration Manager for Biogas Plant Simulation

Manages equipment configurations for different stages of the biogas plant,
including loading/saving equipment scenarios and CSV management.
"""

import pandas as pd
import json
import os
from typing import Dict, Any, List


class EquipmentManager:
    def __init__(self):
        self.equipment_files = {
            'Mixing': 'equipment_mixing.csv',
            'Digestion': 'equipment_digestion.csv', 
            'Pasteurization': 'equipment_pasteurization.csv',
            'Separation': 'equipment_separation.csv',
            'Storage': 'equipment_storage.csv',
            'Gas Upgrading': 'equipment_gas_upgrading.csv',
            'Boiler': 'equipment_boiler.csv',
            'CHP': 'equipment_chp.csv'
        }
        
        self.equipment_data = {}
        self.load_all_equipment()
    
    def load_all_equipment(self):
        """Load equipment data from all CSV files"""
        for stage, filename in self.equipment_files.items():
            self.equipment_data[stage] = self.load_equipment_csv(filename)
    
    def load_equipment_csv(self, filename: str) -> Dict[str, Dict[str, Any]]:
        """Load equipment data from a specific CSV file"""
        equipment_dict = {}
        
        try:
            if os.path.exists(filename):
                df = pd.read_csv(filename)
                
                for _, row in df.iterrows():
                    equipment_type = row['equipment_type']
                    parameter = row['parameter']
                    value = row['value']
                    unit = row['unit']
                    
                    if equipment_type not in equipment_dict:
                        equipment_dict[equipment_type] = {}
                    
                    equipment_dict[equipment_type][parameter] = {
                        'value': value,
                        'unit': unit
                    }
        except Exception as e:
            print(f"Error loading {filename}: {e}")
        
        return equipment_dict
    
    def save_equipment_csv(self, stage: str):
        """Save equipment data for a specific stage to CSV"""
        if stage not in self.equipment_data:
            return
        
        filename = self.equipment_files[stage]
        data = []
        
        for equipment_type, parameters in self.equipment_data[stage].items():
            for parameter, param_data in parameters.items():
                data.append({
                    'equipment_type': equipment_type,
                    'parameter': parameter,
                    'value': param_data['value'],
                    'unit': param_data['unit']
                })
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
    
    def save_all_equipment(self):
        """Save all equipment data to their respective CSV files"""
        for stage in self.equipment_files.keys():
            self.save_equipment_csv(stage)
    
    def save_scenario(self, scenario_name: str):
        """Save current equipment configuration as a named scenario"""
        scenario_data = {
            'name': scenario_name,
            'equipment': self.equipment_data.copy()
        }
        
        filename = f"equipment_scenario_{scenario_name}.json"
        with open(filename, 'w') as f:
            json.dump(scenario_data, f, indent=2)
    
    def load_scenario(self, scenario_name: str):
        """Load a named equipment scenario"""
        filename = f"equipment_scenario_{scenario_name}.json"
        
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    scenario_data = json.load(f)
                    self.equipment_data = scenario_data['equipment']
                    return True
        except Exception as e:
            print(f"Error loading scenario {scenario_name}: {e}")
        
        return False
    
    def list_scenarios(self) -> List[str]:
        """List all available equipment scenarios"""
        scenarios = []
        for filename in os.listdir('.'):
            if filename.startswith('equipment_scenario_') and filename.endswith('.json'):
                scenario_name = filename.replace('equipment_scenario_', '').replace('.json', '')
                scenarios.append(scenario_name)
        return scenarios
    
    def get_equipment_data(self, stage: str) -> Dict[str, Dict[str, Any]]:
        """Get equipment data for a specific stage"""
        return self.equipment_data.get(stage, {})
    
    def update_equipment_parameter(self, stage: str, equipment_type: str, parameter: str, value: Any):
        """Update a specific equipment parameter"""
        if stage not in self.equipment_data:
            self.equipment_data[stage] = {}
        
        if equipment_type not in self.equipment_data[stage]:
            self.equipment_data[stage][equipment_type] = {}
        
        if parameter not in self.equipment_data[stage][equipment_type]:
            self.equipment_data[stage][equipment_type][parameter] = {'unit': ''}
        
        self.equipment_data[stage][equipment_type][parameter]['value'] = value


if __name__ == "__main__":
    # Test the equipment manager
    manager = EquipmentManager()
    print("Loaded equipment stages:", list(manager.equipment_data.keys()))
    
    # Test scenario saving/loading
    manager.save_scenario("default")
    print("Saved default scenario")
    
    scenarios = manager.list_scenarios()
    print("Available scenarios:", scenarios)