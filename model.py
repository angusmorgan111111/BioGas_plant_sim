from dataclasses import dataclass

import pandas


@dataclass
class FeedStock:
    name: str
    quant: float # quantity / rate (the units are Tons PA)
    dm_perc: float
    vs_perc: float
    gas_yeild: float #m3 per tonne of volitile
    meth_perc: float #perc of the gas yeild
    digest_recduction_factor: float # percentage reduction in VS

class Shit:
    def __init__(self):
        self.content = {}

    def add_feedstock(self, feed: FeedStock):
        self.content[feed.name] = feed

    def stats(self):
        mean_dm_perc = sum([feed.dm_perc for feed in self.content.values()]) / len(self.content)
        dm_rate = {}
        vs_rate = {}
        gas_rate = {}
        meth_rate ={}
        for feed in self.content.values():
            dm_rate[feed.name] = feed.quant * feed.dm_perc / 100
            vs_rate[feed.name] = dm_rate[feed.name] * feed.vs_perc / 100
            gas_rate[feed.name] = vs_rate[feed.name] * feed.gas_yeild / 100
            meth_rate[feed.name] = gas_rate[feed.name] * feed.meth_perc / 100
        return mean_dm_perc, dm_rate, vs_rate, gas_rate, meth_rate


def feed(input_path: str):
    shit = Shit()
    df_feed = pandas.read_csv(input_path, index_col="feed_name")
    df_feed.apply(lambda feed: shit.add_feedstock(FeedStock(feed.name, feed.rate, feed.dm_perc,
                                                            feed.vs_perc, feed.gas_yeild, feed.meth_perc,
                                                            feed.digest_reduction_factor)),
                 axis=1)
    print(shit.stat())
    return shit


def mix(shit: Shit, clean_water: FeedStock, recirc_fluid: FeedStock):
    shit.add_feedstock(clean_water)
    shit.add_feedstock(recirc_fluid)
    print(shit.stats())
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
    shit.add_feedstock(FeedStock("slurry", 18500, 8, 80, foo, bar, 60))
    shit.add_feedstock(FeedStock("fym", 6000, 30, 80, foo, bar, 60))
    print(shit.stats())
    feed("feed.csv")
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
