import pretty_midi
import math
from midi_ensemble_generator import EnsembleGenerator

def create_test_midi(filename, bpm):
    midi = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    inst = pretty_midi.Instrument(program=33)
    # C2 for 4 beats
    beat_dur = 60.0 / bpm
    inst.notes.append(pretty_midi.Note(100, 36, 0.0, beat_dur*4))
    midi.instruments.append(inst)
    midi.write(filename)

def test_v1_6():
    print("--- Testing V1.6 Advanced Arpeggios ---")
    filename = "z:/MIDI_Dictionary/test_v1_6.mid"
    create_test_midi(filename, 120)
    
    gen = EnsembleGenerator()
    generated = gen.generate(filename, velocity_scale=1.0, key_arg="C Major")
    
    # 1. Test Diatonic 7th Chord
    # Look for Diatonic_7th_Pad (easiest to check pitches)
    d7_files = [f for f in generated if "Diatonic_7th_Pad" in f]
    if d7_files:
        print(f"Checking 7th Chord: {d7_files[0]}")
        midi = pretty_midi.PrettyMIDI(d7_files[0])
        notes = midi.instruments[0].notes
        # Should be C Maj 7: C, E, G, B (48, 52, 55, 59)
        pitches = sorted(list(set([n.pitch for n in notes])))
        print(f"Pitches: {pitches}")
        if len(pitches) >= 4:
            print("[PASS] Generated 4-note 7th chord.")
        else:
            print(f"[FAIL] Expected 4 notes, got {len(pitches)}")
    else:
        print("[FAIL] Diatonic_7th_Pad file missing.")

    # 2. Test Trance Gate
    # Look for Arp_Trance
    trance_files = [f for f in generated if "Arp_Trance" in f and "Maj" in f] # use Maj for simplicity
    if trance_files:
        print(f"\nChecking Trance Arp: {trance_files[0]}")
        midi = pretty_midi.PrettyMIDI(trance_files[0])
        notes = midi.instruments[0].notes
        if len(notes) > 0:
            dur = notes[0].end - notes[0].start
            step = (60/120)/4
            ratio = dur / step
            print(f"Note Duration: {dur:.4f} (Step: {step:.4f}, Ratio: {ratio:.2f})")
            if 0.5 < ratio < 0.7:
                print("[PASS] Trance Gate ~0.6 confirmed.")
            else:
                print(f"[FAIL] Trance Gate mismatch. Ratio {ratio}")
                
    # 3. Test Healing Overlap
    healing_files = [f for f in generated if "Arp_Healing" in f]
    if healing_files:
        print(f"\nChecking Healing Arp: {healing_files[0]}")
        midi = pretty_midi.PrettyMIDI(healing_files[0])
        notes = midi.instruments[0].notes
        if len(notes) > 0:
            dur = notes[0].end - notes[0].start
            step = (60/120)/4
            ratio = dur / step
            print(f"Note Duration: {dur:.4f} (Ratio: {ratio:.2f})")
            if ratio > 1.5:
                print("[PASS] Healing Overlap > 1.5 confirmed.")
            else:
                print(f"[FAIL] Healing Overlap missing. Ratio {ratio}")
                
    # 4. Test LoFi Timing Leg
    lofi_files = [f for f in generated if "Arp_LoFi" in f]
    if lofi_files:
        print(f"\nChecking LoFi Arp: {lofi_files[0]}")
        midi = pretty_midi.PrettyMIDI(lofi_files[0])
        notes = midi.instruments[0].notes
        if len(notes) > 0:
            # Expected start is 0.0 + offset
            start = notes[0].start
            print(f"First Note Start: {start:.4f}s")
            if start > 0.01:
                print("[PASS] LoFi Timing Lag detected.")
            else:
                print("[FAIL] LoFi Timing Lag missing (Start near 0).")

if __name__ == "__main__":
    test_v1_6()
