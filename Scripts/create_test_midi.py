import pretty_midi

def create_test_midi(filename="test_bass.mid"):
    midi = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=33) # Electric Bass
    # Create 4 notes: C2, G2, A2, F2 (Common progression)
    # C2 = 36
    notes = [
        (36, 0.0, 1.0, 100),   # C2
        (43, 1.0, 2.0, 110),   # G2
        (45, 2.0, 3.0, 90),    # A2
        (41, 3.0, 4.0, 120),   # F2
    ]
    
    for pitch, start, end, vel in notes:
        note = pretty_midi.Note(velocity=vel, pitch=pitch, start=start, end=end)
        inst.notes.append(note)
        
    midi.instruments.append(inst)
    midi.write(filename)
    print(f"Created {filename}")

if __name__ == "__main__":
    create_test_midi()
