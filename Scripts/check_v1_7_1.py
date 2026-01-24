import os
import sys
import pretty_midi
import pandas as pd
import numpy as np

# Ensure import from EnsembleGenerator folder
sys.path.append(os.path.join(os.path.dirname(__file__), '../EnsembleGenerator'))
from midi_ensemble_generator import ExternalArpStyle, load_arp_catalog, get_tempo_at_time

class MockNote:
    def __init__(self, start, end, velocity, pitch):
        self.start = start
        self.end = end
        self.velocity = velocity
        self.pitch = pitch

def test_v1_7_1():
    print("--- Testing Arpeggio Patterns Excel ---")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(script_dir, "arpeggio_patterns.xlsx")
    
    print(f"Loading: {excel_path}")
    catalog = load_arp_catalog(excel_path)
    
    if not catalog:
        print("FAIL: Could not load catalog (or empty).")
        return

    print(f"Successfully loaded {len(catalog)} styles:")
    for name, style in catalog.items():
        print(f"  - [Style: {name}]")
        seq = style['sequence']
        gates = style['gate_ratios']
        vels = style['velocity_mults']
        
        # Basic Validation
        if len(seq) != 16 or len(gates) != 16 or len(vels) != 16:
            print(f"    FAIL: Length mismatch! Seq={len(seq)}, Gate={len(gates)}, Vel={len(vels)}")
            continue
            
        # Check for valid 'r' parsing (should be '-1')
        r_count = seq.count('-1')
        print(f"    Rests: {r_count}/16 steps")
        
        # Check for strumming
        strum_count = sum(1 for s in seq if ',' in s)
        if strum_count > 0:
            print(f"    Strumming detected in {strum_count} steps.")
            
        # Check Gate Values range
        min_g, max_g = min(gates), max(gates)
        print(f"    Gate Range: {min_g:.1f} - {max_g:.1f}")
        
        # Check Velocity Values range
        min_v, max_v = min(vels), max(vels)
        print(f"    Velocity Range: {min_v:.1f} - {max_v:.1f}")
        
    print("\n--- Validation Complete ---")

if __name__ == "__main__":
    test_v1_7_1()
