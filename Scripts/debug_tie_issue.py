import os
import pandas as pd
import sys
# Ensure import from EnsembleGenerator folder
sys.path.append(os.path.join(os.path.dirname(__file__), '../EnsembleGenerator'))
from midi_ensemble_generator import load_arp_catalog, ExternalArpStyle

class MockNote:
    def __init__(self, start, end, velocity, pitch):
        self.start = start
        self.end = end
        self.velocity = velocity
        self.pitch = pitch

def debug_excel_loading():
    print("--- 1. Debugging Excel Loading ---")
    file_path = "arpeggio_patterns.xlsx"
    if not os.path.exists(file_path):
        print("Excel file not found!")
        return

    catalog = load_arp_catalog(file_path)
    
    print(f"Loaded {len(catalog)} styles.")
    for name, style in catalog.items():
        print(f"\n[Style: {name}]")
        print(f"  Seq (first 8): {style['sequence'][:8]}")
        print(f"  Gate (first 8): {style['gate_ratios'][:8]}")
        print(f"  Vel (first 8): {style['velocity_mults'][:8]}")
        
    return catalog

def debug_generation(catalog):
    print("\n--- 2. Debugging Generation Logic ---")
    if "Strum_Slow" not in catalog: return

    style_data = catalog["Strum_Slow"]
    # Force a simple sequence to test Tie specifically if Strum_Slow is complex
    # Let's mock the data to be sure
    mock_data = style_data.copy()
    mock_data['sequence'] = ['0', 'r', '0', 'r'] + ['-1']*12
    mock_data['gate_ratios'] = [2.0, 1.0, 0.5, 1.0] + [1.0]*12 # Step 0 has Gate 2.0 (Tie)
    
    arp = ExternalArpStyle(mock_data)
    
    chord_notes = [60, 64, 67]
    bass_note = MockNote(0.0, 2.0, 100, 36) # 2 seconds
    
    # Mock tempo: 120 BPM -> Beat=0.5s, Step(16th)=0.125s
    # Step 0: Start=0.0. Gate=2.0 -> Duration = 0.125 * 2 = 0.25s. End=0.25
    
    notes = arp.apply(chord_notes, bass_note)
    
    print(f"Generated {len(notes)} notes.")
    for i, n in enumerate(notes):
        dur = n.end - n.start
        print(f" Note {i}: Pitch={n.pitch}, Start={n.start:.3f}, End={n.end:.3f}, Dur={dur:.3f}")
        
        if i == 0:
            expected_dur = 0.125 * 2.0
            if abs(dur - expected_dur) < 0.01:
                print(f"  PASS: Note 0 duration is {dur:.3f} (Matches 2 steps)")
            else:
                print(f"  FAIL: Note 0 duration {dur:.3f} != Expected {expected_dur:.3f}")

if __name__ == "__main__":
    cat = debug_excel_loading()
    if cat:
        debug_generation(cat)
