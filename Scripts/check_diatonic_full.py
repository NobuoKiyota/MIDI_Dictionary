import pretty_midi
from midi_ensemble_generator import DiatonicTriadStrategy

def test_c_major():
    print("\n--- Testing C Major Scale (Bass: C D E F G A B) ---")
    strategy = DiatonicTriadStrategy()
    key_info = (0, 'Major') # C Major
    
    # Bass Notes: C2(36) to B2(47)
    bass_notes = [36, 38, 40, 41, 43, 45, 47]
    names = ["C", "D", "E", "F", "G", "A", "B "]
    # I, ii, iii, IV, V, vi, vii°
    expected_qualities = ["Maj", "min", "min", "Maj", "Maj", "min", "dim"]
    
    for i, root in enumerate(bass_notes):
        notes = strategy.get_notes(root, key_info)
        # Normalize to root=0 for interval check
        base = root + 12
        intervals = [n - base for n in notes]
        intervals.sort()
        
        quality = "Unknown"
        if intervals == [0, 4, 7]: quality = "Maj"
        elif intervals == [0, 3, 7]: quality = "min"
        elif intervals == [0, 3, 6]: quality = "dim"
        
        expected = expected_qualities[i]
        status = "PASS" if quality == expected else "FAIL"
        print(f"Bass {names[i]}: Generated {quality} ({notes}) -> {status}")

def test_a_minor():
    print("\n--- Testing A Minor Scale (Bass: A B C D E F G) ---")
    strategy = DiatonicTriadStrategy()
    key_info = (9, 'Minor') # A Minor
    
    # Bass Notes: A1(33) to G2(43)
    # A B C D E F G
    bass_notes = [33, 35, 36, 38, 40, 41, 43]
    names = ["A", "B", "C", "D", "E", "F", "G"]
    # Natural Minor Diatonic Chords:
    # i(min), ii°(dim), III(Maj), iv(min), v(min), VI(Maj), VII(Maj)
    expected_qualities = ["min", "dim", "Maj", "min", "min", "Maj", "Maj"]
    
    for i, root in enumerate(bass_notes):
        notes = strategy.get_notes(root, key_info)
        base = root + 12
        intervals = [n - base for n in notes]
        intervals.sort()
        
        quality = "Unknown"
        if intervals == [0, 4, 7]: quality = "Maj"
        elif intervals == [0, 3, 7]: quality = "min"
        elif intervals == [0, 3, 6]: quality = "dim"
        
        expected = expected_qualities[i]
        status = "PASS" if quality == expected else "FAIL"
        print(f"Bass {names[i]}: Generated {quality} ({notes}) -> {status}")

if __name__ == "__main__":
    test_c_major()
    test_a_minor()
