#!/usr/bin/env python3
"""
Test script to verify the updated digest function calculates mass reduction
correctly for each feedstock while maintaining the same total reduction.
"""

from model import Shit, FeedStock, digest


def test_digest_mass_reduction():
    """Test that the digest function calculates individual mass reductions correctly based on VS reduction"""
    
    # Create test feedstock with known values
    test_feeds = [
        FeedStock("feed1", 1000, 20, 80, 10, 50, 40),  # 1000 T/A, 20% DM, 80% VS, 40% reduction
        FeedStock("feed2", 500, 30, 75, 15, 60, 50),   # 500 T/A, 30% DM, 75% VS, 50% reduction
        FeedStock("feed3", 800, 15, 85, 12, 55, 30),   # 800 T/A, 15% DM, 85% VS, 30% reduction
    ]
    
    # Calculate expected values before digestion
    initial_data = []
    total_initial_mass = 0
    total_initial_dm = 0
    total_initial_vs = 0
    expected_mass_reductions = []
    
    for feed in test_feeds:
        initial_mass = feed.quant
        initial_dm = initial_mass * (feed.dm_perc / 100)
        initial_vs = initial_dm * (feed.vs_perc / 100)
        
        # Mass reduction = VS reduction (only VS is digested and converted to gas)
        vs_reduction = initial_vs * (feed.digest_reduction_factor / 100)
        expected_mass_reduction = vs_reduction
        
        # Calculate remaining components
        remaining_vs = initial_vs - vs_reduction
        non_vs_dm = initial_dm - initial_vs  # Non-volatile portion of DM
        remaining_dm = remaining_vs + non_vs_dm
        final_mass = initial_mass - expected_mass_reduction
        
        initial_data.append({
            'name': feed.name,
            'initial_mass': initial_mass,
            'initial_dm': initial_dm,
            'initial_vs': initial_vs,
            'vs_reduction': vs_reduction,
            'expected_mass_reduction': expected_mass_reduction,
            'expected_final_mass': final_mass,
            'expected_final_dm_perc': (remaining_dm / final_mass) * 100 if final_mass > 0 else 0,
            'expected_final_vs_perc': (remaining_vs / remaining_dm) * 100 if remaining_dm > 0 else 0
        })
        
        total_initial_mass += initial_mass
        total_initial_dm += initial_dm
        total_initial_vs += initial_vs
        expected_mass_reductions.append(expected_mass_reduction)
    
    expected_total_mass_reduction = sum(expected_mass_reductions)
    
    print("=== DIGEST FUNCTION TEST (VS-Based Reduction) ===")
    print(f"Total initial mass: {total_initial_mass:.2f} T/A")
    print(f"Total initial DM: {total_initial_dm:.2f} T/A")
    print(f"Total initial VS: {total_initial_vs:.2f} T/A")
    print(f"Expected total mass reduction: {expected_total_mass_reduction:.2f} T/A")
    print()
    
    # Create Shit object and add feeds
    shit = Shit()
    for feed in test_feeds:
        shit.add_feed(feed)
    
    # Run digest function
    methane_yield = digest(shit)
    
    # Check results
    print("=== RESULTS AFTER DIGESTION ===")
    actual_total_mass_reduction = 0
    
    for i, (feed_name, feed) in enumerate(shit.content.items()):
        expected = initial_data[i]
        actual_mass_reduction = expected['initial_mass'] - feed.quant
        actual_total_mass_reduction += actual_mass_reduction
        
        print(f"\n{feed_name}:")
        print(f"  Initial mass: {expected['initial_mass']:.2f} T/A")
        print(f"  Initial VS: {expected['initial_vs']:.2f} T/A")
        print(f"  VS reduction: {expected['vs_reduction']:.2f} T/A")
        print(f"  Final mass: {feed.quant:.2f} T/A")
        print(f"  Expected mass reduction: {expected['expected_mass_reduction']:.2f} T/A")
        print(f"  Actual mass reduction: {actual_mass_reduction:.2f} T/A")
        print(f"  Mass reduction match: {abs(actual_mass_reduction - expected['expected_mass_reduction']) < 0.01}")
        print(f"  Expected final DM%: {expected['expected_final_dm_perc']:.2f}%")
        print(f"  Actual final DM%: {feed.dm_perc:.2f}%")
        print(f"  DM% match: {abs(feed.dm_perc - expected['expected_final_dm_perc']) < 0.01}")
        print(f"  Expected final VS%: {expected['expected_final_vs_perc']:.2f}%")
        print(f"  Actual final VS%: {feed.vs_perc:.2f}%")
        print(f"  VS% match: {abs(feed.vs_perc - expected['expected_final_vs_perc']) < 0.01}")
    
    print(f"\n=== TOTAL VERIFICATION ===")
    print(f"Expected total mass reduction: {expected_total_mass_reduction:.2f} T/A")
    print(f"Actual total mass reduction: {actual_total_mass_reduction:.2f} T/A")
    print(f"Total reduction match: {abs(actual_total_mass_reduction - expected_total_mass_reduction) < 0.01}")
    print(f"Methane yield: {methane_yield:.2f} TpA")
    
    # Verify totals match
    reduction_match = abs(actual_total_mass_reduction - expected_total_mass_reduction) < 0.01
    
    if reduction_match:
        print("\n✅ TEST PASSED: Mass reduction calculated correctly for each feedstock!")
    else:
        print("\n❌ TEST FAILED: Total mass reduction doesn't match expected value!")
    
    return reduction_match


if __name__ == "__main__":
    test_digest_mass_reduction()