import pretty_midi
import math
from midi_ensemble_generator import EnsembleGenerator, MidiAnalyzer

def test_dominant_logic():
    print("\n--- Test 1: Dominant Logic (Downbeat vs Duration) ---")
    gen = EnsembleGenerator()
    
    class MockNote:
        def __init__(self, start, end, vel, pitch):
            self.start = start
            self.end = end
            self.velocity = vel
            self.pitch = pitch
            
    class MockAna:
        def __init__(self, note):
            self.note = note
            self.harmonic_pitch = note.pitch
            
    n1 = MockNote(0.0, 0.1, 110, 40) # E (Downbeat, Fast, Strong)
    n2 = MockNote(0.1, 0.5, 80, 45)  # A (Offbeat, Long, Weak)
    
    notes = [MockAna(n1), MockAna(n2)]
    
    best = gen.get_dominant_root(notes, beat_start=0.0)
    print(f"Selected Pitch: {best.note.pitch}")
    
    if best.note.pitch == 40:
        print("[PASS] Dominant Logic selected Downbeat/Strong note.")
    else:
        print("[FAIL] Dominant Logic selected Long note (Legacy behavior).")

def test_voice_leading():
    print("\n--- Test 2: Voice Leading (Centroid Minimization) ---")
    gen = EnsembleGenerator()
    
    prev_centroid = 51.66 # C Major avg
    
    target_notes = [55, 59, 62] # G Major
    best_notes, new_centroid = gen.get_best_voicing(target_notes, prev_centroid)
    
    print(f"Prev Centroid: {prev_centroid}")
    print(f"Naive Target: {target_notes} (Avg {sum(target_notes)/3:.2f})")
    print(f"Voiced Result: {best_notes} (Avg {new_centroid:.2f})")
    
    dist_naive = abs(58.66 - prev_centroid)
    dist_voiced = abs(new_centroid - prev_centroid)
    
    if dist_voiced < dist_naive:
        print("[PASS] Voice Leading reduced centroid distance.")
    else:
        print("[FAIL] Voice Leading did not improve distance.")

def test_rhythm_thinning():
    print("\n--- Test 3: Rhythm Thinning (Anti-Mud) ---")
    input_file = "z:/MIDI_Dictionary/test_thinning.mid"
    midi = pretty_midi.PrettyMIDI(initial_tempo=120)
    inst = pretty_midi.Instrument(program=33)
    
    # Note 1: 0.0-0.125 (Downbeat -> Full)
    inst.notes.append(pretty_midi.Note(100, 36, 0.0, 0.125))
    # Note 2: 0.125-0.250 (Offbeat -> Thinned)
    inst.notes.append(pretty_midi.Note(100, 36, 0.125, 0.250))
    # Dummy
    inst.notes.append(pretty_midi.Note(100, 36, 3.9, 4.0))
    midi.instruments.append(inst)
    midi.write(input_file)
    
    gen = EnsembleGenerator()
    generated = gen.generate(input_file, velocity_scale=1.0)
    
    rhythm_file = [f for f in generated if "Maj_Rhythm" in f][0]
    out_midi = pretty_midi.PrettyMIDI(rhythm_file)
    notes = out_midi.instruments[0].notes
    notes_b1 = [n for n in notes if n.start < 0.5]
    
    c1 = [n for n in notes_b1 if abs(n.start - 0.0) < 0.01]
    c2 = [n for n in notes_b1 if abs(n.start - 0.125) < 0.01]
    
    print(f"Chord 1 Count: {len(c1)}")
    print(f"Chord 2 Count: {len(c2)}")
    
    if len(c1) >= 3 and len(c2) < 3:
        print("[PASS] Rhythm Thinning applied to Offbeat Fast Note.")
    else:
        print("[FAIL] Thinning logic failed.")

if __name__ == "__main__":
    test_dominant_logic()
    test_voice_leading()
    test_rhythm_thinning()
