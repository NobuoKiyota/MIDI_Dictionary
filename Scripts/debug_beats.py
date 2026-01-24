import pretty_midi

def dump_beats():
    midi = pretty_midi.PrettyMIDI(initial_tempo=120)
    # Just accessing beats without notes might return empty?
    # Add dummy note to ensure duration
    inst = pretty_midi.Instrument(program=33)
    inst.notes.append(pretty_midi.Note(100, 40, 0, 4.0))
    midi.instruments.append(inst)
    
    beats = midi.get_beats()
    print("Beats:", beats)
    
    # Check our test note positions
    # Beat 4 starts at 2.0 (Beat index 4, counting 0,1,2,3,4?)
    # 120bpm -> 0.5s per beat.
    # 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0...
    
    # Test Note p2: 2.125
    # Beat start: 2.0
    # Duration: 0.5
    # Fraction: (2.125 - 2.0) / 0.5 = 0.125 / 0.5 = 0.25. Should be correct.

if __name__ == "__main__":
    dump_beats()
