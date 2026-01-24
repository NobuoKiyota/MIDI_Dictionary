import pretty_midi
from midi_ensemble_generator import EnsembleGenerator

def test_merge_unit():
    print("\n--- Testing Merge Unit Logic ---")
    gen = EnsembleGenerator()
    
    # Mock Events: C Maj, C Maj, G Maj
    # Timings: 0.0-0.5, 0.5-1.0, 1.0-1.5
    e1 = {'start':0.0, 'end':0.5, 'chord_notes':[48,52,55], 'notes':[], 'velocity':100}
    e2 = {'start':0.5, 'end':1.0, 'chord_notes':[48,52,55], 'notes':[], 'velocity':100}
    e3 = {'start':1.0, 'end':1.5, 'chord_notes':[55,59,62], 'notes':[], 'velocity':100}
    
    events = [e1, e2, e3]
    merged = gen.merge_events(events)
    
    print(f"Original Count: {len(events)}")
    print(f"Merged Count: {len(merged)}")
    
    # Exp: 2 events.
    # Event 1: Start 0.0, End 1.0.
    # Event 2: Start 1.0, End 1.5.
    
    if len(merged) == 2:
        print("[PASS] Merge Count Correct.")
        if merged[0]['end'] == 1.0:
            print("[PASS] Merge Duration Correct.")
        else:
            print(f"[FAIL] Merge Duration Error: {merged[0]['end']}")
    else:
        print(f"[FAIL] Merge Count Error: {len(merged)}")

def test_merge_integration():
    print("\n--- Testing Merge Integration ---")
    # Same input as beat generation: C-E-G-C (all C Maj harmony)
    # This spans 1 Beat or 4 beats?
    # Original test was scaled to 0.5s (1 beat).
    # If I use the EXTENDED test file (2.0s = 4 beats), let's see.
    # If the input plays C-C-C-C over 4 beats. 
    # Beat 1: C. Beat 2: C. Beat 3: C. Beat 4: C.
    # Beat Chords: C - C - C - C.
    # Merged: 1 event (C, duration 2.0s).
    # Pad should generate 1 Note (Chord).
    
    # Reuse valid input file creation
    input_file = "z:/MIDI_Dictionary/test_merge_gen.mid"
    midi = pretty_midi.PrettyMIDI(initial_tempo=120)
    inst = pretty_midi.Instrument(program=33)
    # 4 beats of C2.
    inst.notes.append(pretty_midi.Note(100, 36, 0.0, 0.5))
    inst.notes.append(pretty_midi.Note(100, 36, 0.5, 1.0))
    inst.notes.append(pretty_midi.Note(100, 36, 1.0, 1.5))
    inst.notes.append(pretty_midi.Note(100, 36, 1.5, 2.0))
    midi.instruments.append(inst)
    midi.write(input_file)
    
    gen = EnsembleGenerator()
    gen.generate(input_file, velocity_scale=1.0)
    
    # Check Pad output
    pad_file = "z:/MIDI_Dictionary/test_merge_gen_Maj_Pad.mid"
    pad_midi = pretty_midi.PrettyMIDI(pad_file)
    notes = pad_midi.instruments[0].notes
    
    print(f"Pad Notes: {len(notes)}")
    # Should be 3 notes (1 chord) if merged.
    # If not merged, would be 4 beats * 3 notes = 12 notes.
    
    if len(notes) == 3:
        print("[PASS] Integration: Pad generated single merged chord.")
        print(f"Duration: {notes[0].end - notes[0].start}")
    else:
        print(f"[FAIL] Integration: Pad generated {len(notes)} notes.")

if __name__ == "__main__":
    test_merge_unit()
    test_merge_integration()
