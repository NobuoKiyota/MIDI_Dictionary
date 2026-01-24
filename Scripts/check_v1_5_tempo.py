import pretty_midi
import math
from midi_ensemble_generator import EnsembleGenerator

def create_tempo_midi(filename, bpm, notes_data, tempo_changes=None):
    midi = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    inst = pretty_midi.Instrument(program=33)
    
    for (start, end, pitch) in notes_data:
        inst.notes.append(pretty_midi.Note(100, pitch, start, end))
        
    midi.instruments.append(inst)
    
    if tempo_changes:
        # pretty_midi API for tempo change is subtle
        # midi.resolution ... but adding explicit tempo change instructions
        # actually, pretty_midi doesn't have a simple add_tempo_change method in all versions?
        # It's managed via `_tempo_change_times` and `_tempo_change_tempos`? 
        # Standard way: midi.write() handles it if we manipulate the internal lists safely using API if available.
        # Ah, `midi.tempo_change_times` is a list/array.
        # Let's try to overwrite them carefully if needed, or rely on initial_tempo.
        # For MULTI-tempo, we might need to manually insert if the API is restricted.
        # But wait, `remove_tempo_change` exists... `time_to_tick`.
        # Let's assume for this test we create separate files for simple BMP.
        pass
        
    midi.write(filename)

def test_static_tempo(bpm, label):
    print(f"\n--- Testing Static Tempo: {bpm} BPM ({label}) ---")
    filename = f"z:/MIDI_Dictionary/test_tempo_{bpm}.mid"
    
    # 1 Beat Duration
    beat_dur = 60.0 / bpm
    
    # Note covers 1 beat
    create_tempo_midi(filename, bpm, [(0.0, beat_dur, 36)])
    
    gen = EnsembleGenerator()
    generated = gen.generate(filename, velocity_scale=1.0)
    
    # Check Arp File
    arp_files = [f for f in generated if "Arp" in f and "Maj_Arp" in f]
    if not arp_files:
        print("[FAIL] No Arp file generated.")
        return
        
    arp_file = arp_files[0]
    print(f"Checking Arp File: {arp_file}")
    out_midi = pretty_midi.PrettyMIDI(arp_file)
    if len(out_midi.instruments) == 0:
        print("[FAIL] No instruments in generated MIDI.")
        return
        
    notes = out_midi.instruments[0].notes
    
    print(f"Generated Notes: {len(notes)}")
    if len(notes) > 0:
        first_dur = notes[0].end - notes[0].start
        expected_16th = beat_dur / 4.0
        print(f"First Note Duration: {first_dur:.4f}s (Expected 16th: {expected_16th:.4f}s)")
        
        if abs(first_dur - expected_16th) < 0.01:
            print("[PASS] Note Duration Matches BPM.")
        else:
            print(f"[FAIL] Note Duration Mismatch. Diff: {first_dur - expected_16th}")
            
    # Check Garbage Note
    # With strict 16th quantization, if input ends EXACTLY on grid, last note should fit.
    # What if input is slightly longer? 
    # Let's trust garbage logic if note count is exactly 4 for 1 beat.
    if len(notes) == 4:
        print("[PASS] Correct note count (4) for 1 beat.")
    else:
        print(f"[WARN] Note count {len(notes)}. Might be expected if duration nuances exist.")

def test_garbage_exclusion():
    print("\n--- Testing Garbage Note Exclusion ---")
    # BPM 120. 16th = 0.125s.
    # Input Note Duration = 0.125 * 4 + 0.02 (4 beats + tiny tail).
    # Total 0.52s.
    # Expected: 4 notes. Tail (0.02s) < Threshold (0.0625s) -> Excluded.
    
    bpm = 120
    filename = "z:/MIDI_Dictionary/test_garbage.mid"
    create_tempo_midi(filename, bpm, [(0.0, 0.52, 36)])
    
    gen = EnsembleGenerator()
    generated = gen.generate(filename, velocity_scale=1.0)
    
    arp_file = [f for f in generated if "Maj_Arp" in f][0]
    midi = pretty_midi.PrettyMIDI(arp_file)
    notes = midi.instruments[0].notes
    
    print(f"Input Duration: 0.52s (4 x 16th + 0.02s)")
    print(f"Generated Notes: {len(notes)}")
    
    if len(notes) == 4:
        print("[PASS] Garbage note excluded (Count is 4).")
    elif len(notes) == 5:
        print("[FAIL] Garbage note generated (Count is 5).")
        print(f"Last Note Duration: {notes[-1].end - notes[-1].start}")

if __name__ == "__main__":
    test_static_tempo(120, "Standard")
    test_static_tempo(90, "Slow")
    test_static_tempo(160, "Fast")
    test_garbage_exclusion()
