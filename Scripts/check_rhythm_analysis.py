import pretty_midi
from midi_analyzer import MidiAnalyzer

def create_and_test_rhythm():
    print("\n--- Testing Advanced Rhythm Analysis ---")
    
    midi = pretty_midi.PrettyMIDI(initial_tempo=120) 
    inst = pretty_midi.Instrument(program=33)
    
    # 1. Mute Note (0.015s < 0.02s) at 0.0
    note_mute = pretty_midi.Note(velocity=100, pitch=40, start=0.0, end=0.015)
    
    # 2. Dotted Note (Dotted 8th = 0.75 beats = 0.375s at 120bpm) 
    # Starts at 1.0. Ends at 1.375.
    note_dotted = pretty_midi.Note(velocity=100, pitch=40, start=1.0, end=1.375)
    
    # 3. 16-beat Pattern (0.25, 0.75 positions)
    # Beat 2.0, 2.25, 2.5, 2.75
    # Just creating this pattern to test Groove Detection
    p1 = pretty_midi.Note(velocity=100, pitch=40, start=2.0, end=2.1)
    p2 = pretty_midi.Note(velocity=100, pitch=40, start=2.125, end=2.2) # 'e' (16th) - 0.25 frac
    p3 = pretty_midi.Note(velocity=100, pitch=40, start=2.375, end=2.45) # 'a' (16th) - 0.75 frac
    p4 = pretty_midi.Note(velocity=100, pitch=40, start=2.5, end=2.6)    # on beat
    
    inst.notes.extend([note_mute, note_dotted, p1, p2, p3, p4])
    midi.instruments.append(inst)
    
    print("\n--- Input Notes ---")
    for n in inst.notes:
        print(f"Note Pitch={n.pitch} Start={n.start:.3f} End={n.end:.3f}")
    
    analyzer = MidiAnalyzer(midi)
    analysis_list = analyzer.analyze_track(inst)
    
    # Check Mute
    if analysis_list[0].is_mute:
        print("[PASS] Note 1 identified as Mute (<0.02s)")
    else:
        print(f"[FAIL] Note 1 Mute detection failed. Duration={note_mute.end - note_mute.start}")
        
    # Check Dotted
    # Note 1 (Mute) is too short to be dotted.
    # Note 2 is the dotted one.
    if analysis_list[1].is_dotted:
        print("[PASS] Note 2 identified as Dotted Note (0.75 beats)")
    else:
        print(f"[FAIL] Note 2 Dotted detection failed.")
        
    # Check Groove Detection
    # Logic in analyze_track prints this. We can't capture print easily here but we can call detect_groove
    groove = analyzer.detect_groove(inst)
    print(f"Detected Groove: {groove}")
    if groove == '16-beat':
        print("[PASS] Groove identified as 16-beat")
    else:
        print(f"[FAIL] Groove identified as {groove}")

if __name__ == "__main__":
    create_and_test_rhythm()
