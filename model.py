from dataclasses import dataclass

import pandas
import matplotlib.pyplot as plt
import numpy as np


@dataclass
class FeedStock:
    source: str
    feedstock_name: str
    dm: float
    vs_of_dm: float
    biogas_yield_vs: float
    percent_ch4: float
    crop_residue_waste_other: str
    density: float
    l_s: str
    digestion_reduction_factor: float
    cod: float
    bod: float
    total_n: float
    am_n: float
    total_p: float
    sol_p: float
    solid_p: float
    total_k: float
    annual_volume: float = 0.0  # Tonnes per year

class Shit:
    def __init__(self):
        self.content = {}

    def add_feedstock(self, feed: FeedStock):
        self.content[feed.feedstock_name] = feed

    def stats(self):
        # Table 1: Basic feedstock properties
        table1_data = []
        for feed in self.content.values():
            table1_data.append([
                feed.source,
                feed.feedstock_name, 
                feed.dm,
                feed.vs_of_dm,
                feed.biogas_yield_vs,
                feed.percent_ch4,
                feed.crop_residue_waste_other,
                feed.density,
                feed.l_s,
                feed.digestion_reduction_factor
            ])
        
        table1_df = pandas.DataFrame(table1_data, columns=[
            'Source', 'Feedstock Name', 'DM', 'VS of DM', 'Biogas Yield VS', 
            '% CH4', 'Crop/Residue/Waste/Other', 'Density', 'L/S', 'Digestion Reduction Factor'
        ])
        
        # Table 2: Nutrient composition
        table2_data = []
        for feed in self.content.values():
            table2_data.append([
                feed.source,
                feed.feedstock_name,
                feed.cod,
                feed.bod,
                feed.total_n,
                feed.am_n,
                feed.total_p,
                feed.sol_p,
                feed.solid_p,
                feed.total_k
            ])
        
        table2_df = pandas.DataFrame(table2_data, columns=[
            'Source', 'Feedstock Name', 'COD', 'BOD', 'Total N', 'Am N', 'Total P', 'Sol P', 'Solid P', 'Total K'
        ])
        
        # Display only the two tables as shown in green circles
        print("Table 1:")
        print(table1_df.to_string(index=False))
        print()
        
        print("Table 2:")
        print(table2_df.to_string(index=False))
        print()
        
        return table1_df, table2_df
    
    def volume_stats(self):
        """Display feedstock volumes"""
        volume_data = []
        for feed in self.content.values():
            volume_data.append([
                feed.feedstock_name,
                feed.annual_volume
            ])
        
        volume_df = pandas.DataFrame(volume_data, columns=[
            'Feedstock Name', 'Annual Volume (TPA)'
        ])
        
        print("Feedstock Annual Volumes:")
        print(volume_df.to_string(index=False, float_format='%.2f'))
        print()
        
        return volume_df
    
    def biogas_production_stats(self):
        """Calculate biogas, methane volumes and kWt for each feedstock"""
        production_data = []
        
        for feed in self.content.values():
            if feed.annual_volume > 0:
                # Calculate dry matter input (tonnes/year)
                dm_input = feed.annual_volume * feed.dm
                
                # Calculate volatile solids input (tonnes/year)
                vs_input = dm_input * feed.vs_of_dm
                
                # Calculate biogas volume (m3/year) - biogas_yield_vs is m3 per tonne VS
                biogas_volume = vs_input * feed.biogas_yield_vs
                
                # Calculate methane volume (m3/year)
                methane_volume = biogas_volume * feed.percent_ch4
                
                # Calculate kWt (assuming 10 kWh per m3 of methane - standard conversion)
                kwh_per_m3_methane = 10
                kwt = methane_volume * kwh_per_m3_methane / 1000  # Convert to MWh
                
                # Calculate hourly outputs
                biogas_per_hour = biogas_volume / (365 * 24)  # m3/hour
                methane_per_hour = methane_volume / (365 * 24)  # m3/hour
                
                production_data.append([
                    feed.feedstock_name,
                    feed.annual_volume,
                    biogas_volume,
                    biogas_per_hour,
                    methane_volume,
                    methane_per_hour,
                    kwt
                ])
        
        production_df = pandas.DataFrame(production_data, columns=[
            'Feedstock Name', 'Annual Volume (TPA)', 'Biogas Volume (m3/yr)', 
            'Biogas Output (m3/hr)', 'Methane Volume (m3/yr)', 'Methane Output (m3/hr)', 'Energy Output (MWh/yr)'
        ])
        
        print("Biogas Production Statistics:")
        print(production_df.to_string(index=False, float_format='%.2f'))
        print()
        
        return production_df
    
    def bulk_properties(self):
        """Calculate bulk properties of the fluid mixture"""
        total_tpa = 0.0
        total_dm = 0.0
        total_vs = 0.0
        total_biogas = 0.0
        total_methane = 0.0
        total_biogas_weighted_methane = 0.0
        crop_methane = 0.0
        residue_waste_methane = 0.0
        feedstock_tpa = 0.0  # TPA excluding water and recirc
        feedstock_dm = 0.0   # DM from feedstocks only
        
        # Calculate totals
        for feed in self.content.values():
            if feed.annual_volume > 0:
                total_tpa += feed.annual_volume
                dm_input = feed.annual_volume * feed.dm
                total_dm += dm_input
                vs_input = dm_input * feed.vs_of_dm
                total_vs += vs_input
                
                # Calculate biogas and methane for this feedstock
                biogas_volume = vs_input * feed.biogas_yield_vs
                methane_volume = biogas_volume * feed.percent_ch4
                
                total_biogas += biogas_volume
                total_methane += methane_volume
                total_biogas_weighted_methane += biogas_volume * feed.percent_ch4
                
                # Categorize methane by crop vs residue/waste
                if feed.crop_residue_waste_other == 'C':
                    crop_methane += methane_volume
                else:  # R, W, or Other
                    residue_waste_methane += methane_volume
                
                # Track feedstock DM (excluding Water and Recirc)
                if feed.feedstock_name not in ['Water', 'Recirc']:
                    feedstock_tpa += feed.annual_volume
                    feedstock_dm += dm_input
        
        # Calculate bulk percentages and properties
        bulk_dm_percentage = (total_dm / total_tpa * 100) if total_tpa > 0 else 0
        bulk_vs_percentage = (total_vs / total_dm * 100) if total_dm > 0 else 0
        mean_methane_percentage = (total_methane / total_biogas * 100) if total_biogas > 0 else 0
        
        # Calculate power output (10 kWh per m3 of methane)
        power_output_mwh = total_methane * 10 / 1000  # Convert to MWh
        
        # Calculate crop vs residue/waste percentages
        crop_methane_percentage = (crop_methane / total_methane * 100) if total_methane > 0 else 0
        residue_waste_methane_percentage = (residue_waste_methane / total_methane * 100) if total_methane > 0 else 0
        
        # Calculate feedstock bulk DM% (excluding water and recirc)
        feedstock_bulk_dm_percentage = (feedstock_dm / feedstock_tpa * 100) if feedstock_tpa > 0 else 0
        
        # First table: Bulk Properties
        bulk_properties_data = [
            ['Total TPA', total_tpa, 'tonnes/year'],
            ['Total DM Input', total_dm, 'tonnes/year'],
            ['Total VS Input', total_vs, 'tonnes/year'],
            ['Bulk DM %', bulk_dm_percentage, '%'],
            ['Feedstock Bulk DM %', feedstock_bulk_dm_percentage, '%'],
            ['Bulk VS of DM %', bulk_vs_percentage, '%']
        ]
        
        bulk_properties_df = pandas.DataFrame(bulk_properties_data, columns=[
            'Property', 'Value', 'Units'
        ])
        
        # Calculate hourly outputs for totals
        total_biogas_per_hour = total_biogas / (365 * 24)  # m3/hour
        total_methane_per_hour = total_methane / (365 * 24)  # m3/hour
        
        # Second table: Maximum Yields
        maximum_yields_data = [
            ['Total Biogas', total_biogas, 'm3/year'],
            ['Total Biogas per Hour', total_biogas_per_hour, 'm3/hour'],
            ['Total Methane', total_methane, 'm3/year'],
            ['Total Methane per Hour', total_methane_per_hour, 'm3/hour'],
            ['Mean Methane %', mean_methane_percentage, '%'],
            ['Power Output', power_output_mwh, 'MWh/year'],
            ['Methane from Crops %', crop_methane_percentage, '%'],
            ['Methane from Residue/Waste %', residue_waste_methane_percentage, '%']
        ]
        
        maximum_yields_df = pandas.DataFrame(maximum_yields_data, columns=[
            'Property', 'Value', 'Units'
        ])
        
        print("Bulk Fluid Properties:")
        print(bulk_properties_df.to_string(index=False, float_format='%.2f'))
        print()
        
        print("Maximum Yields:")
        print(maximum_yields_df.to_string(index=False, float_format='%.2f'))
        print()
        
        return bulk_properties_df, maximum_yields_df
    
    def plot_feedstock_chart(self):
        """Plot bar chart showing feedstock volumes, biogas and methane volumes produced"""
        # Get production data from biogas_production_stats
        production_df = self.biogas_production_stats()
        
        if production_df.empty:
            print("No feedstock data to plot")
            return None
        
        # Filter out feedstocks with zero volume
        production_df = production_df[production_df['Annual Volume (TPA)'] > 0]
        
        # Extract data from the production statistics
        feedstock_names = production_df['Feedstock Name'].tolist()
        volumes = production_df['Annual Volume (TPA)'].tolist()
        biogas_outputs = (production_df['Biogas Volume (m3/yr)'] / 1000).tolist()  # Convert to thousands
        methane_outputs = (production_df['Methane Volume (m3/yr)'] / 1000).tolist()  # Convert to thousands
        
        # Create the plot with dual y-axes
        x = np.arange(len(feedstock_names))
        width = 0.25
        
        fig, ax1 = plt.subplots(figsize=(14, 8))
        
        # First y-axis for input volumes
        bars1 = ax1.bar(x - width, volumes, width, label='Feedstock Volume (TPA)', color='steelblue', alpha=0.8)
        ax1.set_xlabel('Feedstock Type', fontsize=12)
        ax1.set_ylabel('Feedstock Volume (TPA)', color='steelblue', fontsize=12)
        ax1.tick_params(axis='y', labelcolor='steelblue')
        
        # Second y-axis for gas outputs (separate bars)
        ax2 = ax1.twinx()
        bars2 = ax2.bar(x, biogas_outputs, width, label='Biogas Volume (1000 m³/yr)', color='darkorange', alpha=0.8)
        bars3 = ax2.bar(x + width, methane_outputs, width, label='Methane Volume (1000 m³/yr)', color='forestgreen', alpha=0.8)
        ax2.set_ylabel('Gas Volume (1000 m³/yr)', color='darkred', fontsize=12)
        ax2.tick_params(axis='y', labelcolor='darkred')
        
        # Customize the plot
        ax1.set_title('Feedstock Volumes vs Biogas & Methane Production', fontsize=14, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(feedstock_names, rotation=45, ha='right', fontsize=10)
        
        # Create combined legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            ax1.annotate(f'{height:.0f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=8)
        
        for bar in bars2:
            height = bar.get_height()
            ax2.annotate(f'{height:.0f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=8, color='darkorange')
        
        for bar in bars3:
            height = bar.get_height()
            ax2.annotate(f'{height:.0f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=8, color='forestgreen')
        
        # Add grid for better readability
        ax1.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        return fig


def assign_feedstock_volumes(shit: Shit, volumes_path: str):
    """Assign annual volumes to feedstocks from CSV file"""
    df_volumes = pandas.read_csv(volumes_path)
    
    # Clean up the TPA column - remove spaces and commas, handle dashes
    volume_dict = {}
    for _, row in df_volumes.iterrows():
        feedstock_name = row['Feedstock Name'].strip()
        tpa_value = str(row['TPA']).strip()
        
        if tpa_value == '-' or tpa_value == 'nan':
            volume_dict[feedstock_name] = 0.0
        else:
            # Remove spaces and commas, convert to float
            clean_volume = tpa_value.replace(',', '').replace(' ', '')
            try:
                volume_dict[feedstock_name] = float(clean_volume)
            except ValueError:
                volume_dict[feedstock_name] = 0.0
    
    # Assign volumes to feedstocks in the Shit object
    for feed_name, feed in shit.content.items():
        # Try exact match first
        if feed_name in volume_dict:
            feed.annual_volume = volume_dict[feed_name]
        else:
            # Try matching by trimming spaces from volume dict keys
            matched = False
            for vol_name, vol_value in volume_dict.items():
                if feed_name.strip() == vol_name.strip():
                    feed.annual_volume = vol_value
                    matched = True
                    break
            if not matched:
                feed.annual_volume = 0.0
    
    return shit

def feed(input_path: str):
    shit = Shit()
    df_feed = pandas.read_csv(input_path, skiprows=[1])  # Skip units row
    df_feed.apply(lambda row: shit.add_feedstock(FeedStock(
        source=row['Source'],
        feedstock_name=row['Feedstock Name'],
        dm=row['DM'],
        vs_of_dm=row['VS of DM'],
        biogas_yield_vs=row['Biogas Yield VS'],
        percent_ch4=row['% CH4'],
        crop_residue_waste_other=row['Crop/Residue/Waste/Other'],
        density=row['Density '],
        l_s=row['L/S'],
        digestion_reduction_factor=row['Digestion Reduction Factor'],
        cod=row['COD '],
        bod=row['BOD'],
        total_n=row['Total N'],
        am_n=row['Am N '],
        total_p=row['Total P'],
        sol_p=row['Sol P '],
        solid_p=row['Solid P'],
        total_k=row['Total K ']
    )), axis=1)
    return shit


def mix(shit: Shit, clean_water: FeedStock, recirc_fluid: FeedStock):
    shit.add_feedstock(clean_water)
    shit.add_feedstock(recirc_fluid)
    return shit


def digestion(feed_input: dict):
    pass
    # INPUTS:
    # feed - which has clean water and recirc fluid added

    # PERFORMS
    # does reduction in VS for each feedstock
    # calculates the yeild - applies the proportions (meth_perc & gas yeild) to vs

    # LOGS
    # yeild
    # same params as input_feed_stats
    # retention time (tank volume / input rate)

    # OUTPUTS
    # overall rate 
    # percentage DM
    # tbh this is probably going to be the feedstock dict again


def pasturise(feed_input: dict):
    pass
    # TODO:
    # INPUT:
    # feedstock

    # OUTPUT:
    # feedstock

def seperate(feed_input: dict):
    pass
    # INPUT:
    # feedstock

    # PERFORMS:
    # seperates solids from liquid
    # takes x percent DM from the input to create y percent DM in sludge / solid
    # the rest is te liquid / recirc

    # LOGS
    # same stuff
    # proportions liquid / sludge
    

if __name__ == "__main__":
    foo = 10
    bar = 10
    shit = Shit()
    # Updated to use new FeedStock structure - these values are placeholders
    # Load data from CSV and assign volumes
    shit_from_csv = feed("Feedstocks_Training.csv")
    shit_from_csv = assign_feedstock_volumes(shit_from_csv, "feedstock volumes.csv")
    
    # Print all tables
    shit_from_csv.stats()
    shit_from_csv.volume_stats()
    shit_from_csv.bulk_properties()
    
    # Plot the chart (this will also display biogas production stats)
    shit_from_csv.plot_feedstock_chart()
    # INPUT = {
    #     "slurry": FeedStock("slurry", 18500, 8, 80, foo, bar, 60),
    #     "fym": FeedStock("fym", 6000, 30, 80, foo, bar, 60),
    #     "poultry_litter": FeedStock("poultry_litter", 9000, 40, 75, foo, bar, 60),
    #     "rape_straw": FeedStock("rape_straw", 6000, 89, 85, foo, bar, 60),
    #     "daf_sludges": FeedStock("daf_sludges", 2500, 20, 90, foo, bar, 60),
    #     "wc_silage": FeedStock("wc_silage", 6000, 27, 91, foo, bar, 60)}



    #     "recirc_fluid": FeedStcok("recirc_fluid", 1, 5, 0, 0, 0, 60),
    #     "clean_water": FeedStcok("clean_water", 1, 0, 0, 0, 0, 60),
    # 
