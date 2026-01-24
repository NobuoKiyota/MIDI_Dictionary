import pretty_midi
from midi_ensemble_generator import DiatonicTriadStrategy

def test_harmonic_minor():
    print("\n--- Testing A Harmonic Minor Scale ---")
    # A B C D E F G#
    # V chord (Root E) should be E Major (E G# B) because G# is in scale.
    # In Natural Minor (A B C D E F G), V chord is E Minor (E G B).
    
    strategy = DiatonicTriadStrategy()
    key_info = (9, 'Harmonic Minor') # A Harmonic Minor (Root 9=A)
    
    # Bass E2 (40)
    root = 40 
    expected_notes = [52, 56, 59] # E3(52), G#3(56), B3(59) -> E Major
    
    notes = strategy.get_notes(root, key_info)
    notes.sort()
    
    print(f"Bass E (V): {notes}")
    if notes == expected_notes:
        print("PASS: Generated E Major (Dominant V) correctly for Harmonic Minor.")
    elif notes == [52, 55, 59]:
        print("FAIL: Generated E Minor (Natural Minor behavior).")
    else:
        print(f"FAIL: Unexpected notes {notes}")

def test_melodic_minor():
    print("\n--- Testing A Melodic Minor Scale ---")
    # Ascending: A B C D E F# G#
    # IV chord (Root D) should be D Major (D F# A).
    # In Natural/Harmonic Minor, IV is D Minor (D F A).
    
    strategy = DiatonicTriadStrategy()
    key_info = (9, 'Melodic Minor')
    
    # Bass D2 (38)
    root = 38
    expected_notes = [50, 54, 57] # D3(50), F#3(54), A3(57) -> D Major
    
    notes = strategy.get_notes(root, key_info)
    notes.sort()
    
    print(f"Bass D (IV): {notes}")
    if notes == expected_notes:
        print("PASS: Generated D Major (Major IV) correctly for Melodic Minor.")
    else:
        print(f"FAIL: Unexpected notes {notes}")

if __name__ == "__main__":
    test_harmonic_minor()
    test_melodic_minor()
