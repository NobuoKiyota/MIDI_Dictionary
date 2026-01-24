import os
import sys
import pretty_midi
import pandas as pd
import numpy as np
# Ensure import from EnsembleGenerator folder
sys.path.append(os.path.join(os.path.dirname(__file__), '../EnsembleGenerator'))
from midi_ensemble_generator import ExternalArpStyle, load_arp_catalog, get_tempo_at_time

# Mocking data for standalone test
class MockNote:
    def __init__(self, start, end, velocity, pitch):
        self.start = start
        self.end = end
        self.velocity = velocity
        self.pitch = pitch

def test_excel_loading():
    print("--- Testing Excel Loading ---")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(script_dir, "arpeggio_patterns.xlsx")
    
    catalog = load_arp_catalog(excel_path)
    if not catalog:
        print("FAIL: Could not load catalog.")
        return False
        
    print(f"Loaded {len(catalog)} styles.")
    if "LoFi_01" in catalog:
        print("PASS: LoFi_01 found.")
        # Verify specific data point
        seq = catalog["LoFi_01"]["sequence"]
        print(f"Sequence LoFi_01: {seq[:5]}...")
        if str(seq[1]) == '-1':
            print("PASS: Rest detected correctly at index 1.")
        else:
            print(f"FAIL: Expected rest at index 1, got {seq[1]}")
    else:
        print("FAIL: LoFi_01 not found.")
        
    return catalog

def test_arp_generation(catalog):
    print("\n--- Testing Arp Generation (Strum_Slow) ---")
    
    if "Strum_Slow" not in catalog:
        print("Skipping Strum_Slow test (not in catalog).")
        return

    style_data = catalog["Strum_Slow"]
    arp = ExternalArpStyle(style_data)
    
    chord_notes = [60, 64, 67] # C Maj
    bass_note = MockNote(0.0, 2.0, 100, 36) # 2 seconds long
    
    # Mock midi data for tempo (120 BPM -> 0.5s per beat, 0.125s per 16th)
    # 2.0s = 4 beats = 16 steps
    
    generated_notes = arp.apply(chord_notes, bass_note, 1.0, None) # No midi data, defaults 120
    
    print(f"Generated {len(generated_notes)} notes.")
    
    # Check Step 0: Should have 3 notes (Strum 0,1,2)
    # Strum delays: 0.0, 0.005, 0.010
    
    step0_notes = [n for n in generated_notes if n.start < 0.1]
    step0_notes.sort(key=lambda x: x.start)
    
    if len(step0_notes) == 3:
        print(f"PASS: Correctly generated 3 notes for Step 0 Strum.")
        offsets = [n.start - 0.0 for n in step0_notes]
        print(f"Offsets: {offsets}")
        if offsets[1] > 0.004 and offsets[2] > 0.009:
            print("PASS: Strum timing offset confirmed.")
        else:
            print("FAIL: Strum timing too tight or wrong.")
    else:
        print(f"FAIL: Expected 3 notes in step 0, got {len(step0_notes)}")

def test_octave_wrapping():
    print("\n--- Testing Octave Wrapping ---")
    # Manually create a style data with huge index
    data = {
        'sequence': ['5', '-1'] * 8, # Index 5
        'gate_ratios': [1.0] * 16,
        'velocity_mults': [1.0] * 16,
        'swing': 0.0
    }
    arp = ExternalArpStyle(data)
    chord_notes = [60, 64, 67] # Len 3
    # Index 5 -> 5 % 3 = 2 (67). 5 // 3 = 1 octave shift (+12) -> 79
    
    bass_note = MockNote(0.0, 0.2, 100, 36)
    notes = arp.apply(chord_notes, bass_note)
    
    if notes:
        p = notes[0].pitch
        print(f"Generated Pitch for Index 5 with Chord [60,64,67]: {p}")
        if p == 79:
            print("PASS: Octave wrapping correct (67 + 12 = 79).")
        else:
            print(f"FAIL: Expected 79, got {p}")
    else:
        print("FAIL: No notes generated.")

if __name__ == "__main__":
    cat = test_excel_loading()
    if cat:
        test_arp_generation(cat)
        test_octave_wrapping()
