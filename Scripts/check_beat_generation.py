import pretty_midi
import os
from midi_ensemble_generator import EnsembleGenerator, DiatonicTriadStrategy

def create_input_midi(filename):
    midi = pretty_midi.PrettyMIDI(initial_tempo=120)
    inst = pretty_midi.Instrument(program=33)
    # Beat 1: C Major Arpeggio Rhythm (16th notes)
    # C2, E2, G2, C3.
    # All in first beat (0.0 - 0.5 sec at 120bpm).
    # 16th duration = 0.125s.
    notes = [
        pretty_midi.Note(100, 36, 0.0, 0.125),   # C2
        pretty_midi.Note(100, 40, 0.125, 0.25),  # E2
        pretty_midi.Note(100, 43, 0.25, 0.375),  # G2
        pretty_midi.Note(100, 48, 0.375, 0.5),   # C3
        # Dummy note to extend duration to 2.0s (4 beats) so pretty_midi detects grid
        pretty_midi.Note(100, 36, 3.9, 4.0) 
    ]
    inst.notes.extend(notes)
    midi.instruments.append(inst)
    midi.write(filename)
    return filename

def verify_beat_generation():
    print("\n--- Testing Beat-Quantized Generation ---")
    input_file = "z:/MIDI_Dictionary/test_beat_gen.mid"
    create_input_midi(input_file)
    
    gen = EnsembleGenerator()
    # Generate Output (Auto Key -> C Major likely)
    generated_files = gen.generate(input_file, velocity_scale=1.0)
    
    # 1. Verify Pad (Should be 1 Chords, Long Sustain)
    pad_file = [f for f in generated_files if "Pad" in f and "Maj_Pad" in f][0] # use Maj_Pad or Diatonic_Pad
    # Let's check Diatonic_Pad if possible, but list might have multiple.
    print(f"Checking Pad File: {pad_file}")
    
    pad_midi = pretty_midi.PrettyMIDI(pad_file)
    if len(pad_midi.instruments) == 0:
        print("[FAIL] Pad MIDI has no instruments.")
        return
        
    pad_notes = pad_midi.instruments[0].notes
    print(f"Pad Note Count: {len(pad_notes)}")
    
    # Expectation: 1 Chord (3 notes). Start~0.0, End~0.5.
    if len(pad_notes) == 0:
        print("[FAIL] Pad generated 0 notes.")
    elif len(pad_notes) == 3:
        print("[PASS] Pad generated 1 chord for the beat.")
    else:
        print(f"[FAIL] Pad generated {len(pad_notes)} notes. Expected 1 chord (3 notes).")
        
    # 2. Verify Rhythm (Should be 4 Chords, same harmony)
    rhythm_file = [f for f in generated_files if "Rhythm" in f and "Maj_Pad" not in f and "Maj_Rhythm" in f][0]
    print(f"Checking Rhythm File: {rhythm_file}")
    
    rhy_midi = pretty_midi.PrettyMIDI(rhythm_file)
    rhy_notes = rhy_midi.instruments[0].notes
    print(f"Rhythm Note Count: {len(rhy_notes)}")
    
    # Expectation: 4 Chords * 3 notes = 12 notes.
    if len(rhy_notes) == 12:
        print("[PASS] Rhythm generated 4 chords.")
        # Check Harmony: All should be C Major (C, E, G).
        # Input bass was C, E, G, C. 
        # Old logic: C->Cmaj, E->Emin, G->Gmaj.
        # New logic: Dominant Root for beat is C (First note/Longest). -> All C Maj.
        
        # Check pitches of second chord (corresp to bass E)
        # It should be C Maj notes (48, 52, 55 etc), NOT E min notes.
        chord2_notes = [n.pitch for n in rhy_notes if 0.12 < n.start < 0.13]
        chord2_notes.sort()
        # C3 Major: 48, 52, 55 (plus octave shift?)
        # Base logic: Root+12. C2(36)->C3(48).
        print(f"Chord 2 Pitches: {chord2_notes}")
        
        # E Minor would be E3(52), G3(55), B3(59).
        if 48 in chord2_notes: # C is present
            print("[PASS] Harmony Stablization: Chord 2 is C Major (not E Minor).")
        else:
            print("[FAIL] Harmony Stabilization failed. Chord 2 does not look like C Major.")
            
    else:
        print(f"[FAIL] Rhythm generated {len(rhy_notes)} notes. Expected 12.")

if __name__ == "__main__":
    verify_beat_generation()
