import pretty_midi
import os
from midi_ensemble_generator import EnsembleGenerator, DiatonicTriadStrategy

def create_minor_test_midi(filename="check_diatonic_minor_bass.mid"):
    midi = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=33)
    # C Minor Scale: C, D, Eb, F, G, Ab, Bb
    # C2 = 36
    notes = [
        (36, 0, 1), # C -> C min (C, Eb, G) [0, 3, 7]
        (38, 1, 2), # D -> D dim (D, F, Ab) [2, 5, 8]
        (39, 2, 3), # Eb -> Eb Maj (Eb, G, Bb) [3, 7, 10]
        (43, 3, 4), # G -> G min (G, Bb, D) [7, 10, 14] (Natural Minor v)
    ]
    for p, s, e in notes:
        inst.notes.append(pretty_midi.Note(velocity=100, pitch=p, start=s, end=e))
    midi.instruments.append(inst)
    midi.write(filename)
    return filename

def verify_minor_logic():
    filename = create_minor_test_midi()
    
    print("Testing DiatonicTriadStrategy directly (Key: C Minor)...")
    strategy = DiatonicTriadStrategy()
    key_info = (0, 'Minor') # C Minor
    
    # Expected Note Numbers (Octave +1 from input)
    # Input C2(36) -> C3(48). C min = 48, 51, 55
    # Input D2(38) -> D3(50). D dim = 50, 53, 56
    # Input Eb2(39) -> Eb3(51). Eb Maj = 51, 55, 58
    # Input G2(43) -> G3(55). G min = 55, 58, 62
    
    test_cases = [
        (36, [48, 51, 55]), 
        (38, [50, 53, 56]),
        (39, [51, 55, 58]),
        (43, [55, 58, 62]),
    ]
    
    all_pass = True
    for root, expected in test_cases:
        result = strategy.get_notes(root, key_info)
        result.sort()
        expected.sort()
        if result == expected:
            print(f"[PASS] Root {root}: {result}")
        else:
            print(f"[FAIL] Root {root}: Expected {expected}, Got {result}")
            all_pass = False
            
    if all_pass:
        print("All C Minor Logic Checks Passed.")
    else:
        print("Some Checks Failed.")

if __name__ == "__main__":
    verify_minor_logic()
