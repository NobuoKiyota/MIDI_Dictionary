import pretty_midi
import os
from midi_ensemble_generator import EnsembleGenerator, DiatonicTriadStrategy

def create_diatonic_test_midi(filename="check_diatonic_bass.mid"):
    midi = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=33)
    # C Major Scale: C2, D2, E2, F2, G2, A2, B2
    # C2 = 36
    notes = [
        (36, 0, 1), # C -> Should be C Maj (C, E, G)
        (38, 1, 2), # D -> Should be D min (D, F, A)
        (40, 2, 3), # E -> Should be E min (E, G, B)
        (41, 3, 4), # F -> Should be F Maj (F, A, C)
        (43, 4, 5), # G -> Should be G Maj (G, B, D)
        (45, 5, 6), # A -> Should be A min (A, C, E)
        (47, 6, 7), # B -> Should be B dim (B, D, F)
    ]
    for p, s, e in notes:
        inst.notes.append(pretty_midi.Note(velocity=100, pitch=p, start=s, end=e))
    midi.instruments.append(inst)
    midi.write(filename)
    return filename

def verify_diatonic_logic():
    # 1. Create Test File
    input_file = create_diatonic_test_midi()
    
    # 2. Run Generator directly (Diatonic Only ideally, but we run full suite)
    # Testing Strategy Logic directly is faster/cleaner
    print("Testing DiatonicTriadStrategy directly (Key: C Major)...")
    strategy = DiatonicTriadStrategy()
    key_info = (0, 'Major') # C Major
    
    test_cases = [
        (36, [48, 52, 55]), # C2 -> C3(48), E3(52), G3(55) (Major)
        (38, [50, 53, 57]), # D2 -> D3(50), F3(53), A3(57) (Minor)
        (47, [59, 62, 65]), # B2 -> B3(59), D4(62), F4(65) (Diminished)
    ]
    
    all_pass = True
    for root, expected in test_cases:
        result = strategy.get_notes(root, key_info)
        # Sort for comparison
        result.sort()
        expected.sort()
        if result == expected:
            print(f"[PASS] Root {root}: {result}")
        else:
            print(f"[FAIL] Root {root}: Expected {expected}, Got {result}")
            all_pass = False
            
    if all_pass:
        print("All Diatonic Logic Checks Passed.")
    else:
        print("Some Checks Failed.")

if __name__ == "__main__":
    verify_diatonic_logic()
