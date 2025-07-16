# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pandas",
# ]
# ///
from dataclasses import dataclass

import pandas as pd


# TODO put these params in a file
SLUDGE_DM_PERCENT = 5
DM_REMOVAL_PERCENT = 10
CLEAN_WATER_RATE = 1000


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
            lambda row: row.vs_rate * self.content[row.feed_name].gas_yield / 100,
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


def digest(shit: Shit) -> float:
    """
    Converts shit to methane. Finds the total volatile solids for each feed and
    and calculates the methane yield using the gas_yield and meth_perc for each
    feed type

    Reduces the dry matter in each feed type by digest_reduction factor.

    Updates the "shit" by mutating "shit.

    args:
    shit: the input to the process that will be updated by mutation

    returns:
    meth_yield (TpA): the rate of methane production
    """
    meth_yield = 0
    for feed in shit.content.values():
        dm_rate = feed.quant * (feed.dm_perc / 100)
        # calculates methane yield per feed type
        meth_yield += (
            dm_rate * (feed.vs_perc / 100) * feed.gas_yield * (feed.meth_perc / 100)
        )

        dm_reduction = dm_rate * feed.digest_reduction_factor / 100
        # mutate total quantity and dry matter prop. after digestion
        feed.quant -= dm_reduction
        feed.dm_perc = (dm_rate - dm_reduction) * 100 / feed.quant
    return meth_yield


# TODO
def pasteurize(shit: Shit):
    pass


def separate(
    shit: Shit,
    dm_remv_perc: int = DM_REMOVAL_PERCENT,
    sludge_dm_perc: int = SLUDGE_DM_PERCENT,
) -> tuple[float, float, float]:
    """
    Performs liquid-sludge separation & calculates the rates for each matter.

    NOTE: the input, "shit", is no longer relevant after performing this process
    as we do not update the contents.

    TODO: reduce dry matter of each feedstock type in proportion and update
    "shit" -> then we can report stats etc.

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

    # 5. SEPARATE
    separation_fluids = separate(shit)
    print("SEPARATE")
    print("------------------------------------")
    print(f"SLUDGE_RATE: {separation_fluids[0]} TpA")
    print(f"LIQUID_RATE: {separation_fluids[1]} TpA")
    print(f"LIQUID_DM_PERCENTAGE: {separation_fluids[2]} %")
