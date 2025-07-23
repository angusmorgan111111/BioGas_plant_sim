#!/usr/bin/env python3
"""
Biogas Plant Simulation Configuration GUI

This GUI allows users to configure simulation parameters including:
- Intake volumes for feedstock
- Stage-specific parameters
- Mix stage additives
- Separation parameters

The configuration can be saved to/loaded from JSON files.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import pandas as pd
import os
from model import Shit, FeedStock, initial_feed, mix, digest, pasteurize, separate
from equipment_manager import EquipmentManager


class BiogasConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Biogas Plant Simulation Configuration")
        self.root.geometry("800x700")
        
        # Configuration data
        self.config = {
            'feedstock': {},
            'mix_additives': {
                'clean_water_rate': 1000,
                'recirc_fluid_rate': 1000,
                'recirc_fluid_dm_perc': 5
            },
            'digest_params': {},
            'separation_params': {
                'sludge_dm_percent': 20,
                'dm_removal_percent': 70
            }
        }
        
        # Load default feedstock data
        self.load_default_feedstock()
        
        # Initialize equipment manager
        self.equipment_manager = EquipmentManager()
        
        self.create_widgets()
    
    def load_default_feedstock(self):
        """Load feedstock data from feed.csv if it exists"""
        try:
            if os.path.exists('feed.csv'):
                df = pd.read_csv('feed.csv', index_col='feed_name')
                for index, row in df.iterrows():
                    feedstock_data = {
                        'rate': row['rate'],
                        'dm_perc': row['dm_perc'],
                        'vs_perc': row['vs_perc'],
                        'gas_yield': row['gas_yield'],
                        'meth_perc': row['meth_perc'],
                        'digest_reduction_factor': row['digest_reduction_factor']
                    }
                    
                    # Add density field if it exists in the CSV
                    if 'Density' in row:
                        feedstock_data['Density'] = row['Density']
                    elif 'density' in row:
                        feedstock_data['Density'] = row['density']
                    else:
                        feedstock_data['Density'] = 1.0  # Default density T/M³
                    
                    # Add Crop_Residue_Waste and Solid_Liquid fields if they exist in the CSV
                    if 'Crop_Residue_Waste' in row:
                        feedstock_data['Crop_Residue_Waste'] = row['Crop_Residue_Waste']
                    else:
                        feedstock_data['Crop_Residue_Waste'] = 'W'  # Default
                        
                    if 'Solid_Liquid' in row:
                        feedstock_data['Solid_Liquid'] = row['Solid_Liquid']
                    else:
                        feedstock_data['Solid_Liquid'] = 'S'  # Default
                    
                    self.config['feedstock'][index] = feedstock_data
            
            # Add clean water as a feedstock entry with default values
            self.config['feedstock']['clean_water'] = {
                'rate': self.config['mix_additives']['clean_water_rate'],
                'dm_perc': 0.0,
                'vs_perc': 0.0,
                'gas_yield': 0.0,
                'meth_perc': 0.0,
                'digest_reduction_factor': 0.0,
                'Density': 1.0,
                'Crop_Residue_Waste': 'W',
                'Solid_Liquid': 'L'
            }
            
            # Add recirculation fluid as a feedstock entry with default values
            self.config['feedstock']['recirc_fluid'] = {
                'rate': self.config['mix_additives']['recirc_fluid_rate'],
                'dm_perc': self.config['mix_additives']['recirc_fluid_dm_perc'],
                'vs_perc': 0.0,
                'gas_yield': 0.0,
                'meth_perc': 0.0,
                'digest_reduction_factor': 0.0,
                'Density': 1.0,
                'Crop_Residue_Waste': 'W',
                'Solid_Liquid': 'L'
            }
        except Exception as e:
            messagebox.showwarning("Warning", f"Could not load feed.csv: {e}")
    
    def create_widgets(self):
        # Main container with scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Combined Feedstock and Water tab
        self.create_combined_input_tab(notebook)
        
        # Equipment Configuration tab
        self.create_equipment_tab(notebook)
        
        # Separation tab
        self.create_separation_tab(notebook)
        
        # Control buttons
        self.create_control_buttons(main_frame)
    
    def create_combined_input_tab(self, notebook):
        input_frame = ttk.Frame(notebook)
        notebook.add(input_frame, text="Feedstock & Water Inputs")
        
        # Main scrollable container
        main_canvas = tk.Canvas(input_frame)
        main_scrollbar = ttk.Scrollbar(input_frame, orient="vertical", command=main_canvas.yview)
        main_scrollable_frame = ttk.Frame(main_canvas)
        
        main_scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=main_scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        
        # --- FEEDSTOCK SECTION ---
        feedstock_section = ttk.LabelFrame(main_scrollable_frame, text="Feedstock Configuration", padding=10)
        feedstock_section.pack(fill=tk.X, padx=10, pady=10)
        
        # Header
        ttk.Label(feedstock_section, text="Organic Feedstock Parameters", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=10, pady=5)
        
        # Column headers
        headers = ["Feed Name", "Rate (T/A)", "DM %", "VS %", "Gas Yield (m3/T)", "Methane %", "Digest Reduction %", "Density (T/M³)", "Crop/Residue/Waste", "Solid/Liquid"]
        for i, header in enumerate(headers):
            ttk.Label(feedstock_section, text=header, font=('Arial', 9, 'bold')).grid(row=1, column=i, padx=3, pady=3)
        
        # Feedstock entries
        self.feedstock_vars = {}
        row = 2
        for feed_name, params in self.config['feedstock'].items():
            # Feed name (read-only)
            ttk.Label(feedstock_section, text=feed_name, font=('Arial', 9)).grid(row=row, column=0, padx=3, pady=2)
            
            # Parameter entries
            feed_vars = {}
            param_list = ['rate', 'dm_perc', 'vs_perc', 'gas_yield', 'meth_perc', 'digest_reduction_factor', 'Density', 'Crop_Residue_Waste', 'Solid_Liquid']
            for i, param in enumerate(param_list):
                # Set default values for new fields if they don't exist
                if param not in params:
                    if param == 'Crop_Residue_Waste':
                        params[param] = 'W'  # Default to Waste
                    elif param == 'Solid_Liquid':
                        params[param] = 'S'  # Default to Solid
                    elif param == 'Density':
                        params[param] = 1.0  # Default density T/M³
                
                var = tk.StringVar(value=str(params[param]))
                
                # Create dropdown for Crop_Residue_Waste field
                if param == 'Crop_Residue_Waste':
                    combo = ttk.Combobox(feedstock_section, textvariable=var, values=['C', 'R', 'W'], width=8, font=('Arial', 9), state='readonly')
                    combo.grid(row=row, column=i+1, padx=3, pady=2)
                    combo.bind('<<ComboboxSelected>>', self.update_dm_readouts)
                # Create dropdown for Solid_Liquid field
                elif param == 'Solid_Liquid':
                    combo = ttk.Combobox(feedstock_section, textvariable=var, values=['S', 'L'], width=8, font=('Arial', 9), state='readonly')
                    combo.grid(row=row, column=i+1, padx=3, pady=2)
                    combo.bind('<<ComboboxSelected>>', self.update_dm_readouts)
                else:
                    # Regular entry for numeric fields
                    entry = ttk.Entry(feedstock_section, textvariable=var, width=10, font=('Arial', 9))
                    entry.grid(row=row, column=i+1, padx=3, pady=2)
                    entry.bind('<KeyRelease>', self.update_dm_readouts)
                
                feed_vars[param] = var
            
            self.feedstock_vars[feed_name] = feed_vars
            row += 1
        
        
        # --- BULK FEEDSTOCK SECTION ---
        feedstock_section = ttk.LabelFrame(main_scrollable_frame, text="Bulk Feedstock Properties", padding=15)
        feedstock_section.pack(fill=tk.X, padx=10, pady=10)
        
        # Section header
        ttk.Label(feedstock_section, text="Bulk Feedstock Analysis:", font=('Arial', 10, 'bold'), foreground='blue').grid(row=0, column=0, columnspan=6, pady=5, sticky=tk.W)
        
        # Feedstock DM (organic only)
        ttk.Label(feedstock_section, text="Feedstock DM:", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, padx=5)
        self.dm_before_label = ttk.Label(feedstock_section, text="--.--%", font=('Arial', 9), foreground='darkgreen', background='lightgray', relief='sunken')
        self.dm_before_label.grid(row=1, column=1, padx=10, pady=2, sticky=tk.W)
        
        # Total Mix DM
        ttk.Label(feedstock_section, text="Total Mix DM:", font=('Arial', 9, 'bold')).grid(row=2, column=0, sticky=tk.W, padx=5)
        self.dm_after_label = ttk.Label(feedstock_section, text="--.--%", font=('Arial', 9), foreground='darkblue', background='lightgray', relief='sunken')
        self.dm_after_label.grid(row=2, column=1, padx=10, pady=2, sticky=tk.W)
        
        # Total Feedstock Mix
        ttk.Label(feedstock_section, text="Total Feedstock Mix:", font=('Arial', 9, 'bold')).grid(row=3, column=0, sticky=tk.W, padx=5)
        self.total_all_mass_label = ttk.Label(feedstock_section, text="--- T/A", font=('Arial', 9), foreground='darkblue', background='lightgray', relief='sunken')
        self.total_all_mass_label.grid(row=3, column=1, padx=10, pady=2, sticky=tk.W)
        
        # Total Feedstock Feed only
        ttk.Label(feedstock_section, text="Total Feedstock Feed only:", font=('Arial', 9, 'bold')).grid(row=4, column=0, sticky=tk.W, padx=5)
        self.total_organic_mass_label = ttk.Label(feedstock_section, text="--- T/A", font=('Arial', 9), foreground='darkgreen', background='lightgray', relief='sunken')
        self.total_organic_mass_label.grid(row=4, column=1, padx=10, pady=2, sticky=tk.W)
        
        # Total Feedstock VS
        ttk.Label(feedstock_section, text="Total Feedstock VS:", font=('Arial', 9, 'bold')).grid(row=5, column=0, sticky=tk.W, padx=5)
        self.total_vs_label = ttk.Label(feedstock_section, text="--- T/A", font=('Arial', 9), foreground='darkorange', background='lightgray', relief='sunken')
        self.total_vs_label.grid(row=5, column=1, padx=10, pady=2, sticky=tk.W)
        
        # Calculate button
        ttk.Button(feedstock_section, text="Update Feedstock Properties", command=self.update_dm_readouts).grid(row=6, column=0, columnspan=6, pady=15)
        
        # --- DIGESTION SECTION ---
        yields_section = ttk.LabelFrame(main_scrollable_frame, text="Digestion", padding=15)
        yields_section.pack(fill=tk.X, padx=10, pady=10)
        
        # --- HYDRAULIC PARAMETERS SUBSECTION ---
        hydraulic_frame = ttk.LabelFrame(yields_section, text="Hydraulic Parameters", padding=10)
        hydraulic_frame.grid(row=0, column=0, columnspan=6, sticky='w', padx=10, pady=10)
        
        # Total digestion volume
        ttk.Label(hydraulic_frame, text="Total Digestion Volume:", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=5)
        self.total_digestion_volume_label = ttk.Label(hydraulic_frame, text="--- m³", font=('Arial', 9), foreground='purple', background='lightgray', relief='sunken')
        self.total_digestion_volume_label.grid(row=0, column=1, padx=10, pady=2, sticky=tk.W)
        
        # Primary digestion volume
        ttk.Label(hydraulic_frame, text="Primary Digestion Volume:", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, padx=5)
        self.primary_volume_label = ttk.Label(hydraulic_frame, text="--- m³", font=('Arial', 9), foreground='darkgreen', background='lightgray', relief='sunken')
        self.primary_volume_label.grid(row=1, column=1, padx=10, pady=2, sticky=tk.W)
        
        # Secondary digestion volume  
        ttk.Label(hydraulic_frame, text="Secondary Digestion Volume:", font=('Arial', 9, 'bold')).grid(row=2, column=0, sticky=tk.W, padx=5)
        self.secondary_volume_label = ttk.Label(hydraulic_frame, text="--- m³", font=('Arial', 9), foreground='darkgreen', background='lightgray', relief='sunken')
        self.secondary_volume_label.grid(row=2, column=1, padx=10, pady=2, sticky=tk.W)
        
        # Retention time (input volume) - over total digestion volume
        ttk.Label(hydraulic_frame, text="Retention Time (input):", font=('Arial', 9, 'bold')).grid(row=3, column=0, sticky=tk.W, padx=5)
        self.retention_time_input_label = ttk.Label(hydraulic_frame, text="--- days", font=('Arial', 9), foreground='darkblue', background='lightgray', relief='sunken')
        self.retention_time_input_label.grid(row=3, column=1, padx=10, pady=2, sticky=tk.W)
        
        # Retention time (average volume) - over total digestion volume
        ttk.Label(hydraulic_frame, text="Retention Time (average):", font=('Arial', 9, 'bold')).grid(row=4, column=0, sticky=tk.W, padx=5)
        self.retention_time_avg_label = ttk.Label(hydraulic_frame, text="--- days", font=('Arial', 9), foreground='darkblue', background='lightgray', relief='sunken')
        self.retention_time_avg_label.grid(row=4, column=1, padx=10, pady=2, sticky=tk.W)
        
        # Bulk digestion outcomes section - after hydraulic parameters, justified left
        bulk_frame = ttk.Frame(yields_section)
        bulk_frame.grid(row=1, column=0, columnspan=6, pady=15, sticky='w')
        
        ttk.Label(bulk_frame, text="Bulk Digestion Outcomes:", font=('Arial', 10, 'bold'), foreground='darkblue').grid(row=0, column=0, columnspan=6, pady=5, sticky=tk.W)
        
        # Total Biogas Volume
        ttk.Label(bulk_frame, text="Total Biogas Volume:", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, padx=5)
        self.biogas_volume_label = ttk.Label(bulk_frame, text="--- m³/A", font=('Arial', 9), foreground='darkgreen', background='lightgray', relief='sunken')
        self.biogas_volume_label.grid(row=1, column=1, padx=10, pady=2, sticky=tk.W)
        
        # Gas yield (methane)
        ttk.Label(bulk_frame, text="Methane Yield:", font=('Arial', 9, 'bold')).grid(row=2, column=0, sticky=tk.W, padx=5)
        self.gas_yield_label = ttk.Label(bulk_frame, text="--- m³/A", font=('Arial', 9), foreground='darkgreen', background='lightgray', relief='sunken')
        self.gas_yield_label.grid(row=2, column=1, padx=10, pady=2, sticky=tk.W)
        
        # % Methane
        ttk.Label(bulk_frame, text="% Methane:", font=('Arial', 9, 'bold')).grid(row=3, column=0, sticky=tk.W, padx=5)
        self.methane_percent_label = ttk.Label(bulk_frame, text="--.--%", font=('Arial', 9), foreground='purple', background='lightgray', relief='sunken')
        self.methane_percent_label.grid(row=3, column=1, padx=10, pady=2, sticky=tk.W)
        
        # Output volume
        ttk.Label(bulk_frame, text="Output Volume:", font=('Arial', 9, 'bold')).grid(row=4, column=0, sticky=tk.W, padx=5)
        self.output_volume_label = ttk.Label(bulk_frame, text="--- T/A", font=('Arial', 9), foreground='darkblue', background='lightgray', relief='sunken')
        self.output_volume_label.grid(row=4, column=1, padx=10, pady=2, sticky=tk.W)
        
        # Output DM
        ttk.Label(bulk_frame, text="Output DM%:", font=('Arial', 9, 'bold')).grid(row=5, column=0, sticky=tk.W, padx=5)
        self.output_dm_label = ttk.Label(bulk_frame, text="--.--%", font=('Arial', 9), foreground='darkorange', background='lightgray', relief='sunken')
        self.output_dm_label.grid(row=5, column=1, padx=10, pady=2, sticky=tk.W)
        
        # Section header for Post-Digestion Analysis
        ttk.Label(yields_section, text="Post-Digestion Analysis:", font=('Arial', 11, 'bold'), foreground='darkred').grid(row=2, column=0, columnspan=6, pady=10, sticky=tk.W)
        
        # Create Treeview for feedstock details
        self.feedstock_tree = ttk.Treeview(yields_section, columns=('input_mass', 'dm_rate', 'vs_rate', 'vs_loss', 'final_mass', 'biogas', 'methane'), show='tree headings', height=8)
        
        # Configure column headings
        self.feedstock_tree.heading('#0', text='Feedstock')
        self.feedstock_tree.heading('input_mass', text='Input Mass (T/A)')
        self.feedstock_tree.heading('dm_rate', text='DM Rate (T/A)')
        self.feedstock_tree.heading('vs_rate', text='VS Rate (T/A)')
        self.feedstock_tree.heading('vs_loss', text='VS Loss (T/A)')
        self.feedstock_tree.heading('final_mass', text='Final Mass (T/A)')
        self.feedstock_tree.heading('biogas', text='Biogas (m³/A)')
        self.feedstock_tree.heading('methane', text='Methane (m³/A)')
        
        # Configure column widths - made wider for better readability
        self.feedstock_tree.column('#0', width=150, minwidth=120)
        self.feedstock_tree.column('input_mass', width=120, minwidth=100)
        self.feedstock_tree.column('dm_rate', width=120, minwidth=100)
        self.feedstock_tree.column('vs_rate', width=120, minwidth=100)
        self.feedstock_tree.column('vs_loss', width=120, minwidth=100)
        self.feedstock_tree.column('final_mass', width=120, minwidth=100)
        self.feedstock_tree.column('biogas', width=120, minwidth=100)
        self.feedstock_tree.column('methane', width=120, minwidth=100)
        
        self.feedstock_tree.grid(row=3, column=0, columnspan=6, padx=10, pady=10, sticky='ew')
        
        # Scrollbar for treeview
        tree_scrollbar = ttk.Scrollbar(yields_section, orient='vertical', command=self.feedstock_tree.yview)
        tree_scrollbar.grid(row=3, column=6, sticky='ns', pady=10)
        self.feedstock_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        # Update button
        ttk.Button(yields_section, text="Calculate Digestion Results", command=self.update_yields_and_reduction).grid(row=4, column=0, columnspan=6, pady=15)
        
        # --- SEPARATION RESULTS SECTION ---
        separation_section = ttk.LabelFrame(main_scrollable_frame, text="Separation Stage Results", padding=15)
        separation_section.pack(fill=tk.X, padx=10, pady=10)
        
        # Section header
        ttk.Label(separation_section, text="Sequential Separation Analysis:", font=('Arial', 11, 'bold'), foreground='darkred').grid(row=0, column=0, columnspan=6, pady=10)
        
        # Create Treeview for separation stage results
        self.separation_tree = ttk.Treeview(separation_section, columns=('present', 'input_mass', 'input_dm', 'sludge_mass', 'sludge_dm', 'liquid_mass', 'liquid_dm'), show='tree headings', height=6)
        
        # Configure column headings
        self.separation_tree.heading('#0', text='Stage')
        self.separation_tree.heading('present', text='Present')
        self.separation_tree.heading('input_mass', text='Input Mass (T/A)')
        self.separation_tree.heading('input_dm', text='Input DM (%)')
        self.separation_tree.heading('sludge_mass', text='Sludge Mass (T/A)')
        self.separation_tree.heading('sludge_dm', text='Sludge DM (%)')
        self.separation_tree.heading('liquid_mass', text='Liquid Mass (T/A)')
        self.separation_tree.heading('liquid_dm', text='Liquid DM (%)')
        
        # Configure column widths
        self.separation_tree.column('#0', width=100, minwidth=80)
        self.separation_tree.column('present', width=80, minwidth=60)
        self.separation_tree.column('input_mass', width=120, minwidth=100)
        self.separation_tree.column('input_dm', width=100, minwidth=80)
        self.separation_tree.column('sludge_mass', width=120, minwidth=100)
        self.separation_tree.column('sludge_dm', width=100, minwidth=80)
        self.separation_tree.column('liquid_mass', width=120, minwidth=100)
        self.separation_tree.column('liquid_dm', width=100, minwidth=80)
        
        self.separation_tree.grid(row=1, column=0, columnspan=6, padx=10, pady=10, sticky='ew')
        
        # Scrollbar for separation treeview
        sep_tree_scrollbar = ttk.Scrollbar(separation_section, orient='vertical', command=self.separation_tree.yview)
        sep_tree_scrollbar.grid(row=1, column=6, sticky='ns', pady=10)
        self.separation_tree.configure(yscrollcommand=sep_tree_scrollbar.set)
        
        # Separation bulk parameters summary
        final_frame = ttk.Frame(separation_section)
        final_frame.grid(row=2, column=0, columnspan=6, pady=15, sticky='w')
        
        ttk.Label(final_frame, text="Separation Bulk Parameters:", font=('Arial', 10, 'bold'), foreground='darkblue').grid(row=0, column=0, columnspan=6, pady=5, sticky=tk.W)
        
        # Final liquid mass
        ttk.Label(final_frame, text="Final Liquid Mass:", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, padx=5)
        self.final_liquid_mass_label = ttk.Label(final_frame, text="--- T/A", font=('Arial', 9), foreground='darkblue', background='lightgray', relief='sunken')
        self.final_liquid_mass_label.grid(row=1, column=1, padx=10, pady=2, sticky=tk.W)
        
        # Final liquid DM%
        ttk.Label(final_frame, text="Final Liquid DM%:", font=('Arial', 9, 'bold')).grid(row=2, column=0, sticky=tk.W, padx=5)
        self.final_liquid_dm_label = ttk.Label(final_frame, text="--.--%", font=('Arial', 9), foreground='darkblue', background='lightgray', relief='sunken')
        self.final_liquid_dm_label.grid(row=2, column=1, padx=10, pady=2, sticky=tk.W)
        
        # Total sludge mass
        ttk.Label(final_frame, text="Total Sludge Mass:", font=('Arial', 9, 'bold')).grid(row=3, column=0, sticky=tk.W, padx=5)
        self.total_sludge_mass_label = ttk.Label(final_frame, text="--- T/A", font=('Arial', 9), foreground='brown', background='lightgray', relief='sunken')
        self.total_sludge_mass_label.grid(row=3, column=1, padx=10, pady=2, sticky=tk.W)
        
        # Total sludge DM%
        ttk.Label(final_frame, text="Total Sludge DM%:", font=('Arial', 9, 'bold')).grid(row=4, column=0, sticky=tk.W, padx=5)
        self.total_sludge_dm_label = ttk.Label(final_frame, text="--.--%", font=('Arial', 9), foreground='brown', background='lightgray', relief='sunken')
        self.total_sludge_dm_label.grid(row=4, column=1, padx=10, pady=2, sticky=tk.W)
        
        # Update button
        ttk.Button(separation_section, text="Calculate Separation Results", command=self.update_separation_results).grid(row=3, column=0, columnspan=6, pady=15)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")
        
        # Initialize DM readouts
        self.update_dm_readouts()
    
    def create_equipment_tab(self, notebook):
        equipment_frame = ttk.Frame(notebook)
        notebook.add(equipment_frame, text="Equipment Configuration")
        
        # Main container with scrollbar
        equipment_canvas = tk.Canvas(equipment_frame)
        equipment_scrollbar = ttk.Scrollbar(equipment_frame, orient="vertical", command=equipment_canvas.yview)
        equipment_scrollable_frame = ttk.Frame(equipment_canvas)
        
        equipment_scrollable_frame.bind(
            "<Configure>",
            lambda e: equipment_canvas.configure(scrollregion=equipment_canvas.bbox("all"))
        )
        
        equipment_canvas.create_window((0, 0), window=equipment_scrollable_frame, anchor="nw")
        equipment_canvas.configure(yscrollcommand=equipment_scrollbar.set)
        
        # Header and scenario management
        header_frame = ttk.Frame(equipment_scrollable_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header_frame, text="Equipment Configuration", font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
        
        # Scenario management buttons
        scenario_frame = ttk.Frame(header_frame)
        scenario_frame.pack(side=tk.RIGHT)
        
        ttk.Button(scenario_frame, text="Save Scenario", command=self.save_equipment_scenario).pack(side=tk.LEFT, padx=2)
        ttk.Button(scenario_frame, text="Load Scenario", command=self.load_equipment_scenario).pack(side=tk.LEFT, padx=2)
        
        # Equipment stage tabs
        equipment_notebook = ttk.Notebook(equipment_scrollable_frame)
        equipment_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.equipment_vars = {}
        
        # Create tabs for each equipment stage
        for stage in self.equipment_manager.equipment_files.keys():
            self.create_equipment_stage_tab(equipment_notebook, stage)
        
        equipment_canvas.pack(side="left", fill="both", expand=True)
        equipment_scrollbar.pack(side="right", fill="y")
    
    def create_equipment_stage_tab(self, notebook, stage):
        stage_frame = ttk.Frame(notebook)
        notebook.add(stage_frame, text=stage)
        
        # Stage data
        stage_data = self.equipment_manager.get_equipment_data(stage)
        self.equipment_vars[stage] = {}
        
        row = 0
        for equipment_type, parameters in stage_data.items():
            # Equipment type header
            equipment_frame = ttk.LabelFrame(stage_frame, text=equipment_type.replace('_', ' '), padding=10)
            equipment_frame.grid(row=row, column=0, columnspan=3, sticky='ew', padx=10, pady=5)
            stage_frame.grid_columnconfigure(0, weight=1)
            
            self.equipment_vars[stage][equipment_type] = {}
            
            param_row = 0
            for parameter, param_data in parameters.items():
                # Parameter label
                param_label = parameter.replace('_', ' ').title()
                ttk.Label(equipment_frame, text=f"{param_label}:", font=('Arial', 9)).grid(
                    row=param_row, column=0, sticky='w', padx=5, pady=2)
                
                # Special handling for different parameter types
                if parameter == 'Present' or param_data.get('unit') == 'boolean':
                    # Boolean checkbox
                    var = tk.BooleanVar(value=str(param_data['value']).lower() == 'true')
                    entry = ttk.Checkbutton(equipment_frame, variable=var)
                elif parameter == 'Fuel_Type':
                    # Dropdown for fuel type
                    var = tk.StringVar(value=str(param_data['value']))
                    entry = ttk.Combobox(equipment_frame, textvariable=var, 
                                       values=['Biogas', 'Natural_Gas'], width=15, state='readonly')
                else:
                    # Regular text entry
                    var = tk.StringVar(value=str(param_data['value']))
                    entry = ttk.Entry(equipment_frame, textvariable=var, width=15)
                
                entry.grid(row=param_row, column=1, padx=5, pady=2)
                
                # Unit label
                ttk.Label(equipment_frame, text=param_data['unit'], font=('Arial', 9)).grid(
                    row=param_row, column=2, sticky='w', padx=5, pady=2)
                
                self.equipment_vars[stage][equipment_type][parameter] = var
                param_row += 1
            
            row += 1
    
    def save_equipment_scenario(self):
        """Save current equipment configuration as a scenario"""
        scenario_name = tk.simpledialog.askstring("Save Scenario", "Enter scenario name:")
        if scenario_name:
            try:
                # Update equipment manager with current GUI values
                self.apply_equipment_config()
                
                # Save scenario
                self.equipment_manager.save_scenario(scenario_name)
                messagebox.showinfo("Success", f"Scenario '{scenario_name}' saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save scenario: {e}")
    
    def load_equipment_scenario(self):
        """Load an equipment scenario"""
        scenarios = self.equipment_manager.list_scenarios()
        if not scenarios:
            messagebox.showinfo("Info", "No saved scenarios found.")
            return
        
        # Create selection dialog
        selection_window = tk.Toplevel(self.root)
        selection_window.title("Load Scenario")
        selection_window.geometry("300x200")
        
        ttk.Label(selection_window, text="Select scenario to load:").pack(pady=10)
        
        scenario_var = tk.StringVar()
        scenario_listbox = tk.Listbox(selection_window, height=8)
        scenario_listbox.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        for scenario in scenarios:
            scenario_listbox.insert(tk.END, scenario)
        
        def load_selected():
            selection = scenario_listbox.curselection()
            if selection:
                scenario_name = scenarios[selection[0]]
                if self.equipment_manager.load_scenario(scenario_name):
                    self.update_equipment_gui()
                    messagebox.showinfo("Success", f"Scenario '{scenario_name}' loaded successfully!")
                    selection_window.destroy()
                else:
                    messagebox.showerror("Error", f"Failed to load scenario '{scenario_name}'")
        
        ttk.Button(selection_window, text="Load", command=load_selected).pack(pady=10)
        ttk.Button(selection_window, text="Cancel", command=selection_window.destroy).pack()
    
    def apply_equipment_config(self):
        """Apply current GUI values to equipment manager"""
        for stage, equipment_types in self.equipment_vars.items():
            for equipment_type, parameters in equipment_types.items():
                for parameter, var in parameters.items():
                    try:
                        value = var.get()
                        
                        # Handle different variable types
                        if isinstance(var, tk.BooleanVar):
                            # Boolean values - convert to string for CSV storage
                            value = 'True' if value else 'False'
                        else:
                            # Try to convert to float if it's a number
                            try:
                                value = float(value)
                            except ValueError:
                                pass  # Keep as string
                        
                        self.equipment_manager.update_equipment_parameter(stage, equipment_type, parameter, value)
                    except Exception as e:
                        print(f"Error updating {stage}.{equipment_type}.{parameter}: {e}")
        
        # Save all equipment changes back to CSV files
        self.equipment_manager.save_all_equipment()
    
    def update_equipment_gui(self):
        """Update GUI with current equipment manager values"""
        for stage, equipment_types in self.equipment_vars.items():
            stage_data = self.equipment_manager.get_equipment_data(stage)
            for equipment_type, parameters in equipment_types.items():
                if equipment_type in stage_data:
                    for parameter, var in parameters.items():
                        if parameter in stage_data[equipment_type]:
                            param_value = stage_data[equipment_type][parameter]['value']
                            if isinstance(var, tk.BooleanVar):
                                # Boolean variable - convert string to boolean
                                var.set(str(param_value).lower() == 'true')
                            else:
                                # String variable
                                var.set(str(param_value))
        
        
    
    def create_separation_tab(self, notebook):
        sep_frame = ttk.Frame(notebook)
        notebook.add(sep_frame, text="Separation Configuration")
        
        # Separation parameters
        ttk.Label(sep_frame, text="Separation Stage Parameters", font=('Arial', 14, 'bold')).pack(pady=10)
        
        sep_params_frame = ttk.LabelFrame(sep_frame, text="Separation Parameters", padding=10)
        sep_params_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Sludge DM percentage
        ttk.Label(sep_params_frame, text="Sludge DM Percentage (%):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.sludge_dm_var = tk.StringVar(value=str(self.config['separation_params']['sludge_dm_percent']))
        ttk.Entry(sep_params_frame, textvariable=self.sludge_dm_var, width=15).grid(row=0, column=1, padx=10, pady=5)
        
        # DM removal percentage
        ttk.Label(sep_params_frame, text="DM Removal Percentage (%):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.dm_removal_var = tk.StringVar(value=str(self.config['separation_params']['dm_removal_percent']))
        ttk.Entry(sep_params_frame, textvariable=self.dm_removal_var, width=15).grid(row=1, column=1, padx=10, pady=5)
    
    def create_control_buttons(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Load configuration
        ttk.Button(button_frame, text="Load Config", command=self.load_config).pack(side=tk.LEFT, padx=5)
        
        # Save configuration
        ttk.Button(button_frame, text="Save Config", command=self.save_config).pack(side=tk.LEFT, padx=5)
        
        # Apply and run simulation
        ttk.Button(button_frame, text="Apply & Run Simulation", command=self.apply_and_run).pack(side=tk.RIGHT, padx=5)
        
        # Apply configuration
        ttk.Button(button_frame, text="Apply Config", command=self.apply_config).pack(side=tk.RIGHT, padx=5)
    
    def validate_inputs(self):
        """Validate all input fields"""
        try:
            # Validate feedstock parameters
            for feed_name, vars_dict in self.feedstock_vars.items():
                for param, var in vars_dict.items():
                    # Skip validation for categorical fields
                    if param in ['Crop_Residue_Waste', 'Solid_Liquid']:
                        value = var.get()
                        # Validate categorical values
                        if param == 'Crop_Residue_Waste' and value not in ['C', 'R', 'W']:
                            raise ValueError(f"{feed_name} Crop/Residue/Waste must be C, R, or W")
                        elif param == 'Solid_Liquid' and value not in ['S', 'L']:
                            raise ValueError(f"{feed_name} Solid/Liquid must be S or L")
                    else:
                        # Validate numeric fields
                        value = float(var.get())
                        if value < 0:
                            raise ValueError(f"{feed_name} {param} cannot be negative")
            
            # Mix parameters are now validated as part of feedstock validation
            
            # Validate separation parameters
            sludge_dm = float(self.sludge_dm_var.get())
            dm_removal = float(self.dm_removal_var.get())
            
            if not (0 < sludge_dm <= 100):
                raise ValueError("Sludge DM percentage must be between 0 and 100")
            if not (0 < dm_removal <= 100):
                raise ValueError("DM removal percentage must be between 0 and 100")
                
            return True
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            return False
    
    def apply_config(self):
        """Apply current GUI values to configuration"""
        if not self.validate_inputs():
            return False
        
        # Apply equipment configuration
        self.apply_equipment_config()
        
        try:
            # Update feedstock config
            for feed_name, vars_dict in self.feedstock_vars.items():
                for param, var in vars_dict.items():
                    # Handle categorical fields differently
                    if param in ['Crop_Residue_Waste', 'Solid_Liquid']:
                        self.config['feedstock'][feed_name][param] = var.get()
                    else:
                        # Convert numeric fields to float
                        self.config['feedstock'][feed_name][param] = float(var.get())
            
            # Update mix config from feedstock table
            self.config['mix_additives']['clean_water_rate'] = float(self.feedstock_vars['clean_water']['rate'].get())
            self.config['mix_additives']['recirc_fluid_rate'] = float(self.feedstock_vars['recirc_fluid']['rate'].get())
            self.config['mix_additives']['recirc_fluid_dm_perc'] = float(self.feedstock_vars['recirc_fluid']['dm_perc'].get())
            
            # Update separation config
            self.config['separation_params']['sludge_dm_percent'] = float(self.sludge_dm_var.get())
            self.config['separation_params']['dm_removal_percent'] = float(self.dm_removal_var.get())
            
            # Write updated feed.csv
            self.write_feedstock_csv()
            
            # Update model constants
            self.update_model_constants()
            
            messagebox.showinfo("Success", "Configuration applied successfully!")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply configuration: {e}")
            return False
    
    def write_feedstock_csv(self):
        """Write current feedstock configuration to feed.csv"""
        data = []
        for feed_name, params in self.config['feedstock'].items():
            row = {'feed_name': feed_name}
            row.update(params)
            data.append(row)
        
        df = pd.DataFrame(data)
        # Reorder columns to match expected order
        column_order = ['feed_name', 'rate', 'dm_perc', 'vs_perc', 'gas_yield', 'meth_perc', 'digest_reduction_factor', 'Crop_Residue_Waste', 'Solid_Liquid', 'Density']
        df = df.reindex(columns=column_order)
        df.to_csv('feed.csv', index=False)
    
    def update_model_constants(self):
        """Update model.py constants with current configuration"""
        # Read current model.py
        with open('model.py', 'r') as f:
            content = f.read()
        
        # Update constants
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('SLUDGE_DM_PERCENT ='):
                lines[i] = f"SLUDGE_DM_PERCENT = {self.config['separation_params']['sludge_dm_percent']}"
            elif line.startswith('DM_REMOVAL_PERCENT ='):
                lines[i] = f"DM_REMOVAL_PERCENT = {self.config['separation_params']['dm_removal_percent']}"
            elif line.startswith('CLEAN_WATER_RATE ='):
                lines[i] = f"CLEAN_WATER_RATE = {self.config['mix_additives']['clean_water_rate']}"
        
        # Write updated model.py
        with open('model.py', 'w') as f:
            f.write('\n'.join(lines))
    
    def apply_and_run(self):
        """Apply configuration and run simulation"""
        if self.apply_config():
            try:
                messagebox.showinfo("Running", "Simulation started. Check console for output.")
                self.run_simulation()
                messagebox.showinfo("Complete", "Simulation completed! Check console output.")
            except Exception as e:
                messagebox.showerror("Simulation Error", f"Failed to run simulation: {e}")
    
    def run_simulation(self):
        """Run the biogas simulation with current configuration"""
        shit = Shit()

        # 1. INITIAL FEED - must be first
        initial_feed(shit, "feed.csv")
        stats = shit.stats()
        print("FEED")
        print("------------------------------------")
        print(stats[0])
        print(f"DM PERCENTAGE: {stats[1]} %\n")

        # 2. MIX - both clean water and recirculation fluid are now loaded with feedstock, no additional mix needed
        stats = shit.stats()
        print("MIX")
        print("------------------------------------")
        print(stats[0])
        print(f"DM PERCENTAGE: {stats[1]} %\n")

        # 3. DIGEST
        methane_yield = digest(shit)
        stats = shit.stats()
        print("DIGEST")
        print("------------------------------------")
        print(stats[0])
        print(f"DM PERCENTAGE: {stats[1]} %")
        print(f"METHANE YIELD: {methane_yield} TpA\n")

        # 4. PASTEURIZE
        pasteurize(shit)
        stats = shit.stats()
        print("PASTEURIZE")
        print("------------------------------------")
        print(stats[0])
        print(f"DM PERCENTAGE: {stats[1]} %\n")

        # 5. SEPARATE - Sequential separation
        # Get separation stage configuration
        separation_data = self.equipment_manager.get_equipment_data('Separation')
        stages = []
        stage_names = sorted([stage for stage in separation_data.keys() if stage.startswith('Stage_')])
        
        for stage_name in stage_names:
            stage_params = separation_data[stage_name]
            stage_config = {
                'present': stage_params.get('Present', {}).get('value', 'False').lower() == 'true',
                'dm_removal_percent': float(stage_params.get('DM_Removal_Percent', {}).get('value', 0)),
                'sludge_dm': float(stage_params.get('Sludge_DM', {}).get('value', 20))
            }
            stages.append(stage_config)
        
        from model import separate_sequential
        separation_results = separate_sequential(shit, stages)
        
        print("SEQUENTIAL SEPARATION")
        print("------------------------------------")
        for stage_result in separation_results['stage_results']:
            present_text = "ACTIVE" if stage_result['present'] else "INACTIVE"
            print(f"{stage_result['stage']} ({present_text}):")
            print(f"  Input: {stage_result['input_mass']:.1f} T/A at {stage_result['input_dm_percent']:.2f}% DM")
            if stage_result['present']:
                print(f"  Sludge: {stage_result['sludge_mass']:.1f} T/A at {stage_result['sludge_dm_percent']:.1f}% DM")
                print(f"  Liquid: {stage_result['liquid_mass']:.1f} T/A at {stage_result['liquid_dm_percent']:.2f}% DM")
            else:
                print(f"  No separation (stage inactive)")
            print()
        
        print("FINAL SEPARATION RESULTS:")
        print(f"Final Liquid: {separation_results['final_liquid']['mass']:.1f} T/A at {separation_results['final_liquid']['dm_percent']:.2f}% DM")
        print(f"Total Sludge: {separation_results['total_sludge']['mass']:.1f} T/A at {separation_results['total_sludge']['dm_percent']:.2f}% DM")
    
    def save_config(self):
        """Save current configuration to JSON file"""
        if not self.apply_config():
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Configuration"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.config, f, indent=2)
                messagebox.showinfo("Success", f"Configuration saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def load_config(self):
        """Load configuration from JSON file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Configuration"
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    loaded_config = json.load(f)
                
                # Update GUI with loaded values
                self.config.update(loaded_config)
                self.update_gui_from_config()
                messagebox.showinfo("Success", f"Configuration loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {e}")
    
    def update_gui_from_config(self):
        """Update GUI fields with current configuration values"""
        # Update feedstock fields
        for feed_name, vars_dict in self.feedstock_vars.items():
            if feed_name in self.config['feedstock']:
                for param, var in vars_dict.items():
                    var.set(str(self.config['feedstock'][feed_name][param]))
        
        # Mix fields are now updated as part of feedstock updates above
        
        # Update separation fields
        self.sludge_dm_var.set(str(self.config['separation_params']['sludge_dm_percent']))
        self.dm_removal_var.set(str(self.config['separation_params']['dm_removal_percent']))
        
        # Update DM readouts
        self.update_dm_readouts()
    
    def update_dm_readouts(self, event=None):
        """Update the DM readout labels using current GUI values"""
        try:
            # Create temporary Shit objects to calculate DM percentages
            shit_before = Shit()
            shit_after = Shit()
            
            # Add feedstock to both objects
            for feed_name, vars_dict in self.feedstock_vars.items():
                try:
                    rate = float(vars_dict['rate'].get())
                    dm_perc = float(vars_dict['dm_perc'].get())
                    vs_perc = float(vars_dict['vs_perc'].get())
                    gas_yield = float(vars_dict['gas_yield'].get())
                    meth_perc = float(vars_dict['meth_perc'].get())
                    digest_reduction = float(vars_dict['digest_reduction_factor'].get())
                    
                    feed = FeedStock(feed_name, rate, dm_perc, vs_perc, gas_yield, meth_perc, digest_reduction)
                    
                    # Only add organic feedstock to shit_before (exclude clean_water and recirc_fluid)
                    if feed_name not in ['clean_water', 'recirc_fluid']:
                        shit_before.add_feed(feed)
                    
                    # Add all feedstock to shit_after
                    shit_after.add_feed(feed)
                except (ValueError, AttributeError):
                    # Skip invalid entries
                    continue
            
            # Calculate DM before water addition
            if len(shit_before.content) > 0:
                stats_before = shit_before.stats()
                dm_before = stats_before[1]
                self.dm_before_label.config(text=f"{dm_before:.2f}%")
            else:
                self.dm_before_label.config(text="--.--%")
            
            # Both clean water and recirculation fluid are now in feedstock table - already added above
            # Calculate DM after adding all feedstock (including clean water and recirc)
            if len(shit_after.content) > 0:
                stats_after = shit_after.stats()
                dm_after = stats_after[1]
                self.dm_after_label.config(text=f"{dm_after:.2f}%")
            else:
                self.dm_after_label.config(text="--.--%")
                
            # Calculate total organic mass (excluding water & recirc)
            if len(shit_before.content) > 0:
                stats_before = shit_before.stats()
                total_organic_mass = stats_before[0]['tot_rate'].loc['*total']
                self.total_organic_mass_label.config(text=f"{total_organic_mass:.1f} T/A")
            else:
                self.total_organic_mass_label.config(text="--- T/A")
            
            # Calculate total all mass (including water & recirc)
            if len(shit_after.content) > 0:
                stats_after = shit_after.stats()
                total_all_mass = stats_after[0]['tot_rate'].loc['*total']
                self.total_all_mass_label.config(text=f"{total_all_mass:.1f} T/A")
            else:
                self.total_all_mass_label.config(text="--- T/A")
            
            # Calculate total volatile solids (from all feedstock)
            if len(shit_after.content) > 0:
                stats_after = shit_after.stats()
                total_vs = stats_after[0]['vs_rate'].loc['*total']
                self.total_vs_label.config(text=f"{total_vs:.1f} T/A")
            else:
                self.total_vs_label.config(text="--- T/A")
                
        except Exception as e:
            # Handle any calculation errors gracefully
            self.dm_before_label.config(text="Error")
            self.dm_after_label.config(text="Error")
            self.total_organic_mass_label.config(text="Error")
            self.total_all_mass_label.config(text="Error")
            self.total_vs_label.config(text="Error")
    
    def update_yields_and_reduction(self):
        """Calculate and display digestion yields and mass reduction for each feedstock"""
        try:
            # Clear existing tree items
            for item in self.feedstock_tree.get_children():
                self.feedstock_tree.delete(item)
            
            # Create Shit object for simulation
            shit = Shit()
            
            # Add feedstock from GUI
            for feed_name, vars_dict in self.feedstock_vars.items():
                try:
                    rate = float(vars_dict['rate'].get())
                    dm_perc = float(vars_dict['dm_perc'].get())
                    vs_perc = float(vars_dict['vs_perc'].get())
                    gas_yield = float(vars_dict['gas_yield'].get())
                    meth_perc = float(vars_dict['meth_perc'].get())
                    digest_reduction = float(vars_dict['digest_reduction_factor'].get())
                    
                    feed = FeedStock(feed_name, rate, dm_perc, vs_perc, gas_yield, meth_perc, digest_reduction)
                    shit.add_feed(feed)
                except (ValueError, AttributeError):
                    continue
            
            # Both clean water and recirculation fluid are now in feedstock table - already added above
            
            if len(shit.content) == 0:
                self.biogas_volume_label.config(text="--- m³/A")
                self.gas_yield_label.config(text="--- m³/A")
                self.methane_percent_label.config(text="--.--%")
                self.output_volume_label.config(text="--- T/A")
                self.output_dm_label.config(text="--.--%")
                return
            
            # Get initial stats for display
            initial_stats = shit.stats()
            
            # Calculate initial values for each feedstock
            initial_data = {}
            for feed_name, feed in shit.content.items():
                initial_mass = feed.quant
                initial_dm_rate = initial_mass * (feed.dm_perc / 100)
                initial_vs_rate = initial_dm_rate * (feed.vs_perc / 100)
                
                initial_data[feed_name] = {
                    'initial_mass': initial_mass,
                    'initial_dm_rate': initial_dm_rate,
                    'initial_vs_rate': initial_vs_rate
                }
            
            # Run digestion
            methane_yield, mass_reduction_table = digest(shit)
            
            # Get post-digestion stats
            final_stats = shit.stats()
            
            # Populate the tree with feedstock data
            for _, row in mass_reduction_table.iterrows():
                feed_name = row['feed_name']
                if feed_name == '*TOTAL':
                    # Add total row with different formatting
                    self.feedstock_tree.insert('', 'end', text=feed_name, 
                                             values=(f"{row['initial_mass']:.1f}",
                                                   f"{row['initial_dm_rate']:.1f}",
                                                   f"{row['initial_vs_rate']:.1f}",
                                                   f"{row['vs_reduction']:.1f}",
                                                   f"{row['final_mass']:.1f}",
                                                   f"{row['biogas_yield']:.1f}",
                                                   f"{row['methane_yield']:.1f}"),
                                             tags=('total',))
                else:
                    self.feedstock_tree.insert('', 'end', text=feed_name,
                                             values=(f"{row['initial_mass']:.1f}",
                                                   f"{row['initial_dm_rate']:.1f}",
                                                   f"{row['initial_vs_rate']:.1f}",
                                                   f"{row['vs_reduction']:.1f}",
                                                   f"{row['final_mass']:.1f}",
                                                   f"{row['biogas_yield']:.1f}",
                                                   f"{row['methane_yield']:.1f}"))
            
            # Configure total row formatting
            self.feedstock_tree.tag_configure('total', background='lightblue', font=('Arial', 9, 'bold'))
            
            # Update bulk outcomes
            total_biogas = mass_reduction_table[mass_reduction_table['feed_name'] == '*TOTAL']['biogas_yield'].iloc[0]
            total_methane = mass_reduction_table[mass_reduction_table['feed_name'] == '*TOTAL']['methane_yield'].iloc[0]
            total_output_mass = mass_reduction_table[mass_reduction_table['feed_name'] == '*TOTAL']['final_mass'].iloc[0]
            output_dm_percent = final_stats[1]
            
            # Calculate % methane in biogas
            methane_percent = (total_methane / total_biogas * 100) if total_biogas > 0 else 0
            
            self.biogas_volume_label.config(text=f"{total_biogas:.1f} m³/A")
            self.gas_yield_label.config(text=f"{total_methane:.1f} m³/A")
            self.methane_percent_label.config(text=f"{methane_percent:.1f}%")
            self.output_volume_label.config(text=f"{total_output_mass:.1f} T/A")
            self.output_dm_label.config(text=f"{output_dm_percent:.2f}%")
            
            # Calculate and display hydraulic parameters
            try:
                from model import calculate_hydraulic_parameters
                
                # Create a fresh Shit object with initial feedstock for hydraulic calculations
                hydraulic_shit = Shit()
                for feed_name, vars_dict in self.feedstock_vars.items():
                    try:
                        rate = float(vars_dict['rate'].get())
                        dm_perc = float(vars_dict['dm_perc'].get())
                        vs_perc = float(vars_dict['vs_perc'].get())
                        gas_yield = float(vars_dict['gas_yield'].get())
                        meth_perc = float(vars_dict['meth_perc'].get())
                        digest_reduction = float(vars_dict['digest_reduction_factor'].get())
                        
                        feed = FeedStock(feed_name, rate, dm_perc, vs_perc, gas_yield, meth_perc, digest_reduction)
                        hydraulic_shit.add_feed(feed)
                    except (ValueError, AttributeError):
                        continue
                
                hydraulic_params = calculate_hydraulic_parameters(hydraulic_shit)
                
                # Update hydraulic parameter labels
                total_volume = hydraulic_params['primary_volume'] + hydraulic_params['secondary_volume']
                self.total_digestion_volume_label.config(text=f"{total_volume:.0f} m³")
                self.primary_volume_label.config(text=f"{hydraulic_params['primary_volume']:.0f} m³")
                self.secondary_volume_label.config(text=f"{hydraulic_params['secondary_volume']:.0f} m³")
                self.retention_time_input_label.config(text=f"{hydraulic_params['retention_time_input']:.1f} days")
                self.retention_time_avg_label.config(text=f"{hydraulic_params['retention_time_average']:.1f} days")
                
            except Exception as hydraulic_error:
                print(f"Error calculating hydraulic parameters: {hydraulic_error}")
                self.total_digestion_volume_label.config(text="Error")
                self.primary_volume_label.config(text="Error")
                self.secondary_volume_label.config(text="Error")
                self.retention_time_input_label.config(text="Error")
                self.retention_time_avg_label.config(text="Error")
            
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error calculating digestion results: {str(e)}")
            self.biogas_volume_label.config(text="Error")
            self.gas_yield_label.config(text="Error")
            self.methane_percent_label.config(text="Error")
            self.output_volume_label.config(text="Error")
            self.output_dm_label.config(text="Error")
    
    def update_separation_results(self):
        """Calculate and display sequential separation results"""
        try:
            # Clear existing tree items
            for item in self.separation_tree.get_children():
                self.separation_tree.delete(item)
            
            # Create Shit object for simulation
            shit = Shit()
            
            # Add feedstock from GUI (same as yields calculation)
            for feed_name, vars_dict in self.feedstock_vars.items():
                try:
                    rate = float(vars_dict['rate'].get())
                    dm_perc = float(vars_dict['dm_perc'].get())
                    vs_perc = float(vars_dict['vs_perc'].get())
                    gas_yield = float(vars_dict['gas_yield'].get())
                    meth_perc = float(vars_dict['meth_perc'].get())
                    digest_reduction = float(vars_dict['digest_reduction_factor'].get())
                    
                    feed = FeedStock(feed_name, rate, dm_perc, vs_perc, gas_yield, meth_perc, digest_reduction)
                    shit.add_feed(feed)
                except (ValueError, AttributeError):
                    continue
            
            if len(shit.content) == 0:
                self.final_liquid_mass_label.config(text="--- T/A")
                self.final_liquid_dm_label.config(text="--.--%")
                self.total_sludge_mass_label.config(text="--- T/A")
                self.total_sludge_dm_label.config(text="--.--%")
                return
            
            # Run digestion first (to get post-digestion material for separation)
            methane_yield, mass_reduction_table = digest(shit)
            
            # Get separation stage configuration from equipment manager
            separation_data = self.equipment_manager.get_equipment_data('Separation')
            
            # Convert equipment data to stages list
            stages = []
            stage_names = sorted([stage for stage in separation_data.keys() if stage.startswith('Stage_')])
            
            for stage_name in stage_names:
                stage_params = separation_data[stage_name]
                stage_config = {
                    'present': stage_params.get('Present', {}).get('value', 'False').lower() == 'true',
                    'dm_removal_percent': float(stage_params.get('DM_Removal_Percent', {}).get('value', 0)),
                    'sludge_dm': float(stage_params.get('Sludge_DM', {}).get('value', 20))
                }
                stages.append(stage_config)
            
            # Run sequential separation
            from model import separate_sequential
            separation_results = separate_sequential(shit, stages)
            
            # Populate the tree with stage results
            for stage_result in separation_results['stage_results']:
                present_text = "Yes" if stage_result['present'] else "No"
                
                self.separation_tree.insert('', 'end', 
                                           text=stage_result['stage'],
                                           values=(present_text,
                                                 f"{stage_result['input_mass']:.1f}",
                                                 f"{stage_result['input_dm_percent']:.2f}",
                                                 f"{stage_result['sludge_mass']:.1f}",
                                                 f"{stage_result['sludge_dm_percent']:.1f}",
                                                 f"{stage_result['liquid_mass']:.1f}",
                                                 f"{stage_result['liquid_dm_percent']:.2f}"),
                                           tags=('present' if stage_result['present'] else 'absent',))
            
            # Configure row formatting
            self.separation_tree.tag_configure('present', background='lightgreen')
            self.separation_tree.tag_configure('absent', background='lightgray', foreground='gray')
            
            # Update final results
            final_liquid = separation_results['final_liquid']
            total_sludge = separation_results['total_sludge']
            
            self.final_liquid_mass_label.config(text=f"{final_liquid['mass']:.1f} T/A")
            self.final_liquid_dm_label.config(text=f"{final_liquid['dm_percent']:.2f}%")
            self.total_sludge_mass_label.config(text=f"{total_sludge['mass']:.1f} T/A")
            self.total_sludge_dm_label.config(text=f"{total_sludge['dm_percent']:.2f}%")
            
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error calculating separation results: {str(e)}")
            self.final_liquid_mass_label.config(text="Error")
            self.final_liquid_dm_label.config(text="Error")
            self.total_sludge_mass_label.config(text="Error")
            self.total_sludge_dm_label.config(text="Error")


def main():
    root = tk.Tk()
    app = BiogasConfigGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()