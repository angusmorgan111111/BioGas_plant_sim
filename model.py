# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "matplotlib",
#     "pandas",
#     "reportlab",
# ]
# ///
from dataclasses import dataclass

import pandas as pd


# TODO put these params in a file
SLUDGE_DM_PERCENT = 20.0
DM_REMOVAL_PERCENT = 70.0
CLEAN_WATER_RATE = 1000.0


@dataclass
class FeedStock:
    name: str
    quant: float  # (rate) (T/A)
    dm_perc: float  # (%)
    vs_perc: float  # (%)
    gas_yield: float  # (m3/T)
    meth_perc: float  # (%)
    digest_reduction_factor: float  # (%)


class Shit:
    def __init__(self):
        self.content = {}

    def add_feed(self, feed: FeedStock):
        self.content[feed.name] = feed

    def stats(self):
        df_rates = pd.DataFrame()
        df_rates["feed_name"] = self.content.keys()
        df_rates["tot_rate"] = [x.quant for x in self.content.values()]
        df_rates["dm_rate"] = df_rates.apply(
            lambda row: self.content[row.feed_name].quant
            * self.content[row.feed_name].dm_perc
            / 100,
            axis=1,
        )
        df_rates["vs_rate"] = df_rates.apply(
            lambda row: row.dm_rate * self.content[row.feed_name].vs_perc / 100, axis=1
        )
        df_rates["gas_rate"] = df_rates.apply(
            lambda row: row.vs_rate * self.content[row.feed_name].gas_yield,
            axis=1,
        )
        df_rates["meth_rate"] = df_rates.apply(
            lambda row: row.gas_rate * self.content[row.feed_name].meth_perc / 100,
            axis=1,
        )
        df_rates = df_rates.set_index("feed_name").rename_axis(None, axis=1)
        df_rates.index.name = None
        df_rates.loc["*total"] = df_rates.apply(lambda column: sum(column), axis=0)
        total_dm_perc = (
            df_rates.dm_rate.loc["*total"] * 100 / df_rates.tot_rate.loc["*total"]
        )
        return df_rates, total_dm_perc


def initial_feed(shit: Shit, input_path: str):
    """
    Reads the input data containing the initial feedstock and adds to the shit.

    TODO: make the input data JSON so we can have different suppliers in one file

    args: the input to the process (an instantiated but unpopulated Shit object)
    input_path: path to the input data
    """
    df_feed = pd.read_csv(input_path, index_col="feed_name")
    df_feed.apply(
        lambda feed: shit.add_feed(
            FeedStock(
                feed.name,
                feed.rate,
                feed.dm_perc,
                feed.vs_perc,
                feed.gas_yield,
                feed.meth_perc,
                feed.digest_reduction_factor,
            )
        ),
        axis=1,
    )


def mix(shit: Shit, *args: FeedStock):
    """
    Adds new feed to the shit. Used for adding recirc fluid and clean water but
    can in theory be used at any stage to add new feed of any type

    args:
    shit: the input to the process that will be updated by mutation
    *args: any number of additional unnamed optional feedstocks
    """
    for additions in args:
        shit.add_feed(additions)


def digest(shit: Shit) -> tuple[float, pd.DataFrame]:
    """
    Converts shit to methane. Finds the total volatile solids for each feed and
    calculates the methane yield using the gas_yield and meth_perc for each
    feed type.

    Reduces the mass for each feedstock individually based on their 
    digest_reduction_factor applied to the volatile solids (VS) content 
    within the dry matter (DM).

    Updates the "shit" by mutating feedstock quantities and DM percentages.

    args:
    shit: the input to the process that will be updated by mutation

    returns:
    tuple containing:
    - meth_yield (m³/A): the rate of methane production
    - mass_reduction_df: DataFrame showing mass reduction details for each feedstock
    """
    meth_yield = 0
    mass_reduction_data = []
    
    for feed in shit.content.values():
        # Store initial values
        initial_mass = feed.quant
        initial_dm_perc = feed.dm_perc
        initial_vs_perc = feed.vs_perc
        
        # Calculate initial dry matter rate
        initial_dm_rate = feed.quant * (feed.dm_perc / 100)
        
        # Calculate initial volatile solids rate (VS within DM)
        initial_vs_rate = initial_dm_rate * (feed.vs_perc / 100)
        
        # Calculate total biogas yield per feed type (based on VS content)
        feed_biogas = initial_vs_rate * feed.gas_yield
        
        # Calculate methane yield per feed type (biogas × methane percentage)
        feed_methane = feed_biogas * (feed.meth_perc / 100)
        meth_yield += feed_methane
        
        # Calculate VS reduction based on digest_reduction_factor
        # This represents the amount of VS that is digested and converted to gas
        vs_reduction = initial_vs_rate * (feed.digest_reduction_factor / 100)
        
        # The mass reduction equals the VS reduction 
        # (digested VS is converted to gas and leaves the system)
        mass_reduction = vs_reduction
        
        # Calculate remaining components after digestion
        remaining_vs = initial_vs_rate - vs_reduction
        # Non-volatile solids (ash, lignin, etc.) remain unchanged
        non_vs_dm = initial_dm_rate - initial_vs_rate  # Non-volatile portion of DM
        remaining_dm = remaining_vs + non_vs_dm
        
        # Update feedstock properties after digestion
        new_quantity = feed.quant - mass_reduction
        new_dm_perc = (remaining_dm / new_quantity) * 100 if new_quantity > 0 else 0
        new_vs_perc = (remaining_vs / remaining_dm) * 100 if remaining_dm > 0 else 0
        
        # Store mass reduction data before updating feed properties
        mass_reduction_data.append({
            'feed_name': feed.name,
            'initial_mass': initial_mass,
            'initial_dm_rate': initial_dm_rate,
            'initial_vs_rate': initial_vs_rate,
            'vs_reduction': vs_reduction,
            'mass_reduction': mass_reduction,
            'final_mass': new_quantity,
            'mass_reduction_perc': (mass_reduction / initial_mass) * 100,
            'biogas_yield': feed_biogas,
            'methane_yield': feed_methane,
            'initial_dm_perc': initial_dm_perc,
            'final_dm_perc': new_dm_perc,
            'initial_vs_perc': initial_vs_perc,
            'final_vs_perc': new_vs_perc
        })
        
        # Update feed properties
        feed.quant = new_quantity
        feed.dm_perc = new_dm_perc
        feed.vs_perc = new_vs_perc
    
    # Create DataFrame for mass reduction summary
    mass_reduction_df = pd.DataFrame(mass_reduction_data)
    
    # Add total row
    if not mass_reduction_df.empty:
        total_row = {
            'feed_name': '*TOTAL',
            'initial_mass': mass_reduction_df['initial_mass'].sum(),
            'initial_dm_rate': mass_reduction_df['initial_dm_rate'].sum(),
            'initial_vs_rate': mass_reduction_df['initial_vs_rate'].sum(),
            'vs_reduction': mass_reduction_df['vs_reduction'].sum(),
            'mass_reduction': mass_reduction_df['mass_reduction'].sum(),
            'final_mass': mass_reduction_df['final_mass'].sum(),
            'mass_reduction_perc': (mass_reduction_df['mass_reduction'].sum() / mass_reduction_df['initial_mass'].sum()) * 100,
            'biogas_yield': mass_reduction_df['biogas_yield'].sum(),
            'methane_yield': mass_reduction_df['methane_yield'].sum(),
            'initial_dm_perc': (mass_reduction_df['initial_dm_rate'].sum() / mass_reduction_df['initial_mass'].sum()) * 100,
            'final_dm_perc': (mass_reduction_df['initial_dm_rate'].sum() - mass_reduction_df['vs_reduction'].sum()) / mass_reduction_df['final_mass'].sum() * 100,
            'initial_vs_perc': (mass_reduction_df['initial_vs_rate'].sum() / mass_reduction_df['initial_dm_rate'].sum()) * 100,
            'final_vs_perc': ((mass_reduction_df['initial_vs_rate'].sum() - mass_reduction_df['vs_reduction'].sum()) / (mass_reduction_df['initial_dm_rate'].sum() - mass_reduction_df['vs_reduction'].sum())) * 100 if (mass_reduction_df['initial_dm_rate'].sum() - mass_reduction_df['vs_reduction'].sum()) > 0 else 0
        }
        
        # Add total row to DataFrame
        mass_reduction_df = pd.concat([mass_reduction_df, pd.DataFrame([total_row])], ignore_index=True)
    
    return meth_yield, mass_reduction_df


# TODO
def pasteurize(shit: Shit):
    pass


def separate_sequential(shit: Shit, separation_stages: list) -> dict:
    """
    Performs sequential liquid-sludge separation through multiple stages.
    Only liquid passes through all stages, sludge is removed at each stage.

    args:
    shit: input to the separation process
    separation_stages: list of dicts containing stage parameters
                      [{'present': True, 'dm_removal_percent': 30, 'sludge_dm': 15}, ...]

    returns:
    dict containing results for each stage:
    {
        'stage_results': [
            {
                'stage': 'Stage_1',
                'present': True,
                'input_mass': 1000.0,
                'input_dm_percent': 10.0,
                'sludge_mass': 50.0,
                'sludge_dm_percent': 15.0,
                'liquid_mass': 950.0,
                'liquid_dm_percent': 8.5
            }, ...
        ],
        'final_liquid': {'mass': 900.0, 'dm_percent': 5.0},
        'total_sludge': {'mass': 100.0, 'dm_percent': 20.0}
    }
    """
    results = {
        'stage_results': [],
        'final_liquid': {},
        'total_sludge': {'mass': 0.0, 'total_dm': 0.0}
    }
    
    # Initial conditions
    current_liquid_mass = sum(feed.quant for feed in shit.content.values())
    current_liquid_dm = sum(feed.quant * feed.dm_perc / 100 for feed in shit.content.values())
    current_liquid_dm_perc = (current_liquid_dm / current_liquid_mass * 100) if current_liquid_mass > 0 else 0
    
    total_sludge_mass = 0.0
    total_sludge_dm = 0.0
    
    for i, stage in enumerate(separation_stages):
        stage_name = f"Stage_{i+1}"
        
        if not stage.get('present', False):
            # Stage not present - record but don't process
            stage_result = {
                'stage': stage_name,
                'present': False,
                'input_mass': current_liquid_mass,
                'input_dm_percent': current_liquid_dm_perc,
                'sludge_mass': 0.0,
                'sludge_dm_percent': 0.0,
                'liquid_mass': current_liquid_mass,
                'liquid_dm_percent': current_liquid_dm_perc
            }
            results['stage_results'].append(stage_result)
            continue
        
        # Stage is present - perform separation
        dm_removal_percent = stage.get('dm_removal_percent', 0)
        sludge_dm_percent = stage.get('sludge_dm', 20)
        
        # Calculate DM removed at this stage
        dm_removed = current_liquid_dm * (dm_removal_percent / 100)
        
        # Calculate sludge produced at this stage
        stage_sludge_mass = (dm_removed * 100) / sludge_dm_percent if sludge_dm_percent > 0 else 0
        
        # Update liquid after this stage
        remaining_liquid_mass = current_liquid_mass - stage_sludge_mass
        remaining_liquid_dm = current_liquid_dm - dm_removed
        remaining_liquid_dm_perc = (remaining_liquid_dm / remaining_liquid_mass * 100) if remaining_liquid_mass > 0 else 0
        
        # Record stage results
        stage_result = {
            'stage': stage_name,
            'present': True,
            'input_mass': current_liquid_mass,
            'input_dm_percent': current_liquid_dm_perc,
            'sludge_mass': stage_sludge_mass,
            'sludge_dm_percent': sludge_dm_percent,
            'liquid_mass': remaining_liquid_mass,
            'liquid_dm_percent': remaining_liquid_dm_perc
        }
        results['stage_results'].append(stage_result)
        
        # Accumulate total sludge
        total_sludge_mass += stage_sludge_mass
        total_sludge_dm += dm_removed
        
        # Update for next stage
        current_liquid_mass = remaining_liquid_mass
        current_liquid_dm = remaining_liquid_dm
        current_liquid_dm_perc = remaining_liquid_dm_perc
    
    # Final results
    results['final_liquid'] = {
        'mass': current_liquid_mass,
        'dm_percent': current_liquid_dm_perc
    }
    
    results['total_sludge'] = {
        'mass': total_sludge_mass,
        'dm_percent': (total_sludge_dm / total_sludge_mass * 100) if total_sludge_mass > 0 else 0
    }
    
    return results


def separate(
    shit: Shit,
    dm_remv_perc: int = DM_REMOVAL_PERCENT,
    sludge_dm_perc: int = SLUDGE_DM_PERCENT,
) -> tuple[float, float, float]:
    """
    Legacy single-stage separation function for backward compatibility.
    
    Performs liquid-sludge separation & calculates the rates for each matter.

    args:
    shit: input to the separate process
    dm_remv_perc (%): the percentage of dry matter removed from the input
    sludge_dm_perc (%): the percentage of dry matter in the sludge

    returns:
    a tuple containing:
    sludge_rate (TpA)
    liquid_rate (TpA)
    liquid_dm_perc (%): the percentage of dry matter in the recirc fluid
    """
    total_dm = sum(feed.quant * feed.dm_perc / 100 for feed in shit.content.values())
    removed_dm = total_dm * dm_remv_perc / 100
    sludge_rate = removed_dm * 100 / sludge_dm_perc
    liquid_rate = sum(feed.quant for feed in shit.content.values()) - removed_dm
    liquid_dm_perc = ((total_dm - removed_dm) / liquid_rate) * 100
    return sludge_rate, liquid_rate, liquid_dm_perc


# TODO
def recirculate():
    """
    """
    pass


def calculate_hydraulic_parameters(shit: Shit, equipment_digestion_path: str = "equipment_digestion.csv") -> dict:
    """
    Calculate hydraulic parameters for digestion including volumes and retention times.
    
    args:
    shit: input to calculate hydraulic parameters for
    equipment_digestion_path: path to equipment digestion CSV file
    
    returns:
    dict containing:
    - primary_volume: total primary digestion volume (m³)
    - secondary_volume: total secondary digestion volume (m³)
    - retention_time_input: retention time based on input volume (days)
    - retention_time_average: retention time based on average of input and output volumes (days)
    """
    results = {
        'primary_volume': 0.0,
        'secondary_volume': 0.0,
        'retention_time_input': 0.0,
        'retention_time_average': 0.0
    }
    
    try:
        # Read equipment digestion parameters
        df_equipment = pd.read_csv(equipment_digestion_path)
        
        # Extract primary digestion parameters
        primary_data = df_equipment[df_equipment['equipment_type'] == 'Primary_Digestion']
        primary_tanks = 1.0
        primary_volume_per_tank = 2000.0
        
        for _, row in primary_data.iterrows():
            if row['parameter'] == 'No_Tanks':
                primary_tanks = float(row['value'])
            elif row['parameter'] == 'Usable_Volume':
                primary_volume_per_tank = float(row['value'])
        
        results['primary_volume'] = primary_tanks * primary_volume_per_tank
        
        # Extract secondary digestion parameters
        secondary_data = df_equipment[df_equipment['equipment_type'] == 'Secondary_Digestion']
        secondary_tanks = 1.0
        secondary_volume_per_tank = 1500.0
        
        for _, row in secondary_data.iterrows():
            if row['parameter'] == 'No_Tanks':
                secondary_tanks = float(row['value'])
            elif row['parameter'] == 'Usable_Volume':
                secondary_volume_per_tank = float(row['value'])
        
        results['secondary_volume'] = secondary_tanks * secondary_volume_per_tank
        
        # Calculate total annual feedstock (including water & recirc)
        total_input_volume_annual = sum(feed.quant for feed in shit.content.values())  # T/A
        
        # Calculate output volume after digestion (approximation - assume similar density)
        # This would normally be calculated after digestion, but for now use input as approximation
        total_output_volume_annual = total_input_volume_annual * 0.85  # Assume 15% mass reduction
        
        # Calculate total digestion volume (primary + secondary)
        total_digestion_volume = results['primary_volume'] + results['secondary_volume']  # m³
        
        # Convert annual rates to daily rates for retention time calculation
        daily_input_volume = total_input_volume_annual / 365.25  # T/day (assuming density ~1)
        daily_output_volume = total_output_volume_annual / 365.25  # T/day
        
        # Calculate retention times
        if daily_input_volume > 0:
            results['retention_time_input'] = total_digestion_volume / daily_input_volume  # days
        
        if (daily_input_volume + daily_output_volume) > 0:
            average_daily_volume = (daily_input_volume + daily_output_volume) / 2
            results['retention_time_average'] = total_digestion_volume / average_daily_volume  # days
        
    except Exception as e:
        print(f"Error calculating hydraulic parameters: {e}")
    
    return results


if __name__ == "__main__":
    shit = Shit()

    # 1. INITIAL FEED - must be first
    initial_feed(shit, "feed.csv")
    stats = shit.stats()
    print("FEED")
    print("------------------------------------")
    print(stats[0])
    print(f"DM PERCENTAGE: {stats[1]} %\n")

    # 2. MIX
    mix(
        shit,
        FeedStock("clean_water", CLEAN_WATER_RATE, 0, 0, 0, 0, 0),
        FeedStock("recirc_fluid", 1000, 5, 0, 0, 0, 0),
    )
    stats = shit.stats()
    print("MIX")
    print("------------------------------------")
    print(stats[0])
    print(f"DM PERCENTAGE: {stats[1]} %\n")

    # 3. DIGEST
    methane_yield, mass_reduction_table = digest(shit)
    stats = shit.stats()
    print("DIGEST")
    print("------------------------------------")
    print(stats[0])
    print(f"DM PERCENTAGE: {stats[1]} %")
    print(f"METHANE YIELD: {methane_yield} m³/A")
    
    print("\nMASS REDUCTION TABLE:")
    print("------------------------------------")
    if not mass_reduction_table.empty:
        # Format the DataFrame for better display
        display_cols = ['feed_name', 'initial_mass', 'mass_reduction', 'final_mass', 
                       'mass_reduction_perc', 'biogas_yield', 'methane_yield']
        display_table = mass_reduction_table[display_cols].copy()
        display_table.columns = ['Feed', 'Initial Mass (T/A)', 'Mass Reduction (T/A)', 
                               'Final Mass (T/A)', 'Reduction %', 'Biogas Yield (m³/A)', 'Methane Yield (m³/A)']
        
        # Round numeric values for better display
        numeric_cols = ['Initial Mass (T/A)', 'Mass Reduction (T/A)', 'Final Mass (T/A)', 
                       'Reduction %', 'Biogas Yield (m³/A)', 'Methane Yield (m³/A)']
        for col in numeric_cols:
            display_table[col] = display_table[col].round(2)
        
        print(display_table.to_string(index=False))
    print()

    # 4. PASTEURIZE
    pasteurize(shit)
    stats = shit.stats()
    print("PASTEURIZE")
    print("------------------------------------")
    print(stats[0])
    print(f"DM PERCENTAGE: {stats[1]} %\n")

    # 5. SEPARATE - Sequential separation stages
    stages = [
        {'present': True, 'dm_removal_percent': 30, 'sludge_dm': 15},
        {'present': True, 'dm_removal_percent': 25, 'sludge_dm': 20},
        {'present': False, 'dm_removal_percent': 20, 'sludge_dm': 25}
    ]
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
    print()
