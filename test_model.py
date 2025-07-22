import unittest
import tempfile
import os
import pandas as pd
from model import FeedStock, Shit, initial_feed, mix, digest, separate


class TestFeedStock(unittest.TestCase):
    def test_feedstock_creation(self):
        feed = FeedStock("test_feed", 100, 20, 80, 15, 60, 50)
        self.assertEqual(feed.name, "test_feed")
        self.assertEqual(feed.quant, 100)
        self.assertEqual(feed.dm_perc, 20)
        self.assertEqual(feed.vs_perc, 80)
        self.assertEqual(feed.gas_yield, 15)
        self.assertEqual(feed.meth_perc, 60)
        self.assertEqual(feed.digest_reduction_factor, 50)


class TestShit(unittest.TestCase):
    def setUp(self):
        self.shit = Shit()
        self.feed1 = FeedStock("feed1", 1000, 10, 80, 20, 50, 40)
        self.feed2 = FeedStock("feed2", 500, 15, 75, 25, 55, 45)
    
    def test_shit_initialization(self):
        self.assertEqual(len(self.shit.content), 0)
    
    def test_add_feed(self):
        self.shit.add_feed(self.feed1)
        self.assertEqual(len(self.shit.content), 1)
        self.assertIn("feed1", self.shit.content)
        self.assertEqual(self.shit.content["feed1"], self.feed1)
    
    def test_add_multiple_feeds(self):
        self.shit.add_feed(self.feed1)
        self.shit.add_feed(self.feed2)
        self.assertEqual(len(self.shit.content), 2)
        self.assertIn("feed1", self.shit.content)
        self.assertIn("feed2", self.shit.content)
    
    def test_stats_single_feed(self):
        self.shit.add_feed(self.feed1)
        stats_df, total_dm_perc = self.shit.stats()
        
        self.assertAlmostEqual(stats_df.loc["feed1", "tot_rate"], 1000)
        self.assertAlmostEqual(stats_df.loc["feed1", "dm_rate"], 100)  # 1000 * 10/100
        self.assertAlmostEqual(stats_df.loc["feed1", "vs_rate"], 80)   # 100 * 80/100
        self.assertAlmostEqual(stats_df.loc["feed1", "gas_rate"], 16)  # 80 * 20/100
        self.assertAlmostEqual(stats_df.loc["feed1", "meth_rate"], 8)  # 16 * 50/100
        self.assertAlmostEqual(total_dm_perc, 10)
    
    def test_stats_multiple_feeds(self):
        self.shit.add_feed(self.feed1)
        self.shit.add_feed(self.feed2)
        stats_df, total_dm_perc = self.shit.stats()
        
        self.assertAlmostEqual(stats_df.loc["*total", "tot_rate"], 1500)
        self.assertAlmostEqual(stats_df.loc["*total", "dm_rate"], 175)  # 100 + 75
        expected_total_dm_perc = 175 * 100 / 1500
        self.assertAlmostEqual(total_dm_perc, expected_total_dm_perc)


class TestInitialFeed(unittest.TestCase):
    def setUp(self):
        self.test_csv_content = """feed_name,rate,dm_perc,vs_perc,gas_yield,meth_perc,digest_reduction_factor
slurry,1000,8,80,10,50,40
fym,500,30,80,15,55,45"""
        
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        self.temp_file.write(self.test_csv_content)
        self.temp_file.close()
    
    def tearDown(self):
        os.unlink(self.temp_file.name)
    
    def test_initial_feed_loading(self):
        shit = Shit()
        initial_feed(shit, self.temp_file.name)
        
        self.assertEqual(len(shit.content), 2)
        self.assertIn("slurry", shit.content)
        self.assertIn("fym", shit.content)
        
        slurry = shit.content["slurry"]
        self.assertEqual(slurry.quant, 1000)
        self.assertEqual(slurry.dm_perc, 8)
        self.assertEqual(slurry.vs_perc, 80)
        self.assertEqual(slurry.gas_yield, 10)
        self.assertEqual(slurry.meth_perc, 50)
        self.assertEqual(slurry.digest_reduction_factor, 40)


class TestMix(unittest.TestCase):
    def test_mix_function(self):
        shit = Shit()
        feed1 = FeedStock("initial", 1000, 10, 80, 20, 50, 40)
        shit.add_feed(feed1)
        
        additional_feed = FeedStock("water", 500, 0, 0, 0, 0, 0)
        mix(shit, additional_feed)
        
        self.assertEqual(len(shit.content), 2)
        self.assertIn("water", shit.content)
        self.assertEqual(shit.content["water"].quant, 500)
    
    def test_mix_multiple_feeds(self):
        shit = Shit()
        feed1 = FeedStock("initial", 1000, 10, 80, 20, 50, 40)
        shit.add_feed(feed1)
        
        water = FeedStock("water", 500, 0, 0, 0, 0, 0)
        recirc = FeedStock("recirc", 200, 5, 0, 0, 0, 0)
        mix(shit, water, recirc)
        
        self.assertEqual(len(shit.content), 3)
        self.assertIn("water", shit.content)
        self.assertIn("recirc", shit.content)


class TestDigest(unittest.TestCase):
    def test_digest_methane_calculation(self):
        shit = Shit()
        feed = FeedStock("test", 1000, 10, 80, 20, 50, 40)  # Modified to match calculation
        shit.add_feed(feed)
        
        methane_yield = digest(shit)
        
        # Expected: dm_rate = 1000 * 0.1 = 100
        # vs_rate = 100 * 0.8 = 80
        # methane = 80 * 20 * 0.5 = 800
        expected_methane = 800
        self.assertAlmostEqual(methane_yield, expected_methane)
    
    def test_digest_feed_mutation(self):
        shit = Shit()
        original_quant = 1000
        original_dm_perc = 10
        reduction_factor = 40
        
        feed = FeedStock("test", original_quant, original_dm_perc, 80, 20, 50, reduction_factor)
        shit.add_feed(feed)
        
        digest(shit)
        
        # Check that feed properties were mutated
        mutated_feed = shit.content["test"]
        
        # Expected dm_reduction = 100 * 40/100 = 40
        # Expected new_quant = 1000 - 40 = 960
        # Expected new_dm_perc = (100 - 40) * 100 / 960 = 6.25
        expected_new_quant = 960
        expected_new_dm_perc = 6.25
        
        self.assertAlmostEqual(mutated_feed.quant, expected_new_quant)
        self.assertAlmostEqual(mutated_feed.dm_perc, expected_new_dm_perc)


class TestSeparate(unittest.TestCase):
    def test_separate_calculation(self):
        shit = Shit()
        feed = FeedStock("test", 1000, 10, 80, 20, 50, 40)
        shit.add_feed(feed)
        
        dm_removal = 10
        sludge_dm = 5
        
        sludge_rate, liquid_rate, liquid_dm_perc = separate(shit, dm_removal, sludge_dm)
        
        # Expected calculations:
        # total_dm = 1000 * 10/100 = 100
        # removed_dm = 100 * 10/100 = 10
        # sludge_rate = 10 * 100/5 = 200
        # liquid_rate = 1000 - 10 = 990
        # liquid_dm_perc = (100 - 10) / 990 * 100 = 9.09
        
        self.assertAlmostEqual(sludge_rate, 200)
        self.assertAlmostEqual(liquid_rate, 990)
        self.assertAlmostEqual(liquid_dm_perc, 9.090909090909092, places=5)
    
    def test_separate_multiple_feeds(self):
        shit = Shit()
        feed1 = FeedStock("test1", 1000, 10, 80, 20, 50, 40)
        feed2 = FeedStock("test2", 500, 20, 75, 15, 45, 35)
        shit.add_feed(feed1)
        shit.add_feed(feed2)
        
        sludge_rate, liquid_rate, liquid_dm_perc = separate(shit)
        
        # total_dm = (1000 * 10/100) + (500 * 20/100) = 100 + 100 = 200
        # removed_dm = 200 * 10/100 = 20
        # sludge_rate = 20 * 100/5 = 400
        # liquid_rate = 1500 - 20 = 1480
        # liquid_dm_perc = (200 - 20) / 1480 * 100 = 12.16
        
        self.assertAlmostEqual(sludge_rate, 400)
        self.assertAlmostEqual(liquid_rate, 1480)
        self.assertAlmostEqual(liquid_dm_perc, 12.162162162162161, places=5)


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.test_csv_content = """feed_name,rate,dm_perc,vs_perc,gas_yield,meth_perc,digest_reduction_factor
slurry,1000,8,80,10,50,40
fym,500,30,80,15,55,45"""
        
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        self.temp_file.write(self.test_csv_content)
        self.temp_file.close()
    
    def tearDown(self):
        os.unlink(self.temp_file.name)
    
    def test_full_process_flow(self):
        shit = Shit()
        
        # 1. Initial feed
        initial_feed(shit, self.temp_file.name)
        initial_stats = shit.stats()
        self.assertEqual(len(shit.content), 2)
        
        # 2. Mix
        water = FeedStock("clean_water", 1000, 0, 0, 0, 0, 0)
        recirc = FeedStock("recirc_fluid", 1000, 5, 0, 0, 0, 0)
        mix(shit, water, recirc)
        mix_stats = shit.stats()
        self.assertEqual(len(shit.content), 4)
        
        # 3. Digest
        methane_yield = digest(shit)
        self.assertGreater(methane_yield, 0)
        
        # 4. Separate
        sludge_rate, liquid_rate, liquid_dm_perc = separate(shit)
        self.assertGreater(sludge_rate, 0)
        self.assertGreater(liquid_rate, 0)
        self.assertGreater(liquid_dm_perc, 0)


if __name__ == '__main__':
    unittest.main()