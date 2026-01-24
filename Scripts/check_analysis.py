import pretty_midi
from midi_analyzer import MidiAnalyzer, NoteAnalysis

def test_octave_jump_analysis():
    print("\n--- Testing Octave Jump Analysis ---")
    
    midi = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=33)
    
    # Note 1: E2 (40)
    # Note 2: E3 (52) - Octave Jump Up
    # Note 3: F#2 (42) - New Root
    notes = [
        pretty_midi.Note(velocity=100, pitch=40, start=0, end=1),
        pretty_midi.Note(velocity=100, pitch=52, start=1, end=2),
        pretty_midi.Note(velocity=100, pitch=42, start=2, end=3)
    ]
    inst.notes.extend(notes)
    midi.instruments.append(inst)
    
    analyzer = MidiAnalyzer(midi)
    analysis_list = analyzer.analyze_track(inst)
    
    # Verify Note 1: E2
    # Harmonic Pitch should be 40
    print(f"Note 1 (E2): Harmonic Pitch = {analysis_list[0].harmonic_pitch} (Expected 40)")
    
    # Verify Note 2: E3
    # Harmonic Pitch should be 40 (Lower of pair) because it's an octave jump
    print(f"Note 2 (E3): Harmonic Pitch = {analysis_list[1].harmonic_pitch} (Expected 40)")
    
    # Verify Note 3: F#2
    # Harmonic Pitch should be 42
    print(f"Note 3 (F#2): Harmonic Pitch = {analysis_list[2].harmonic_pitch} (Expected 42)")
    
    if analysis_list[1].harmonic_pitch == 40:
        print("PASS: Octave Jump correctly normalized to lower octave.")
    else:
        print("FAIL: Octave Jump normalization failed.")

def test_beat_syncopation():
    print("\n--- Testing Beat/Syncopation Analysis ---")
    # 120 BPM. Quarter Note = 0.5s.
    # Bar line at 2.0s (4/4 time).
    midi = pretty_midi.PrettyMIDI(initial_tempo=120) 
    inst = pretty_midi.Instrument(program=33)
    
    # Note 1: On Beat 0.0 -> 0.5 (On Beat, No Sync)
    # Note 2: Off Beat 0.6 -> 0.8 (Off Beat, No Sync)
    # Note 3: Syncopated 1.8 -> 2.2 (Crosses Bar Line at 2.0)
    notes = [
        pretty_midi.Note(velocity=100, pitch=40, start=0.0, end=0.5), # On beat 1
        pretty_midi.Note(velocity=100, pitch=40, start=0.6, end=0.8), # Off beat
        pretty_midi.Note(velocity=100, pitch=40, start=1.8, end=2.2), # Bar crossing
    ]
    inst.notes.extend(notes)
    midi.instruments.append(inst)
    
    analyzer = MidiAnalyzer(midi)
    results = analyzer.analyze_track(inst)
    
    print(f"Note 1 (On Beat): OnBeat={results[0].is_on_beat}, Sync={results[0].is_syncopated}")
    print(f"Note 2 (Off Beat): OnBeat={results[1].is_on_beat}, Sync={results[1].is_syncopated}")
    print(f"Note 3 (Bar Cross): OnBeat={results[2].is_on_beat}, Sync={results[2].is_syncopated}")
    
    if results[0].is_on_beat and not results[1].is_on_beat and results[2].is_syncopated:
        print("PASS: Beat and Syncopation Detection Correct.")
    else:
        print("FAIL: Beat/Syncopation logic error.")

if __name__ == "__main__":
    test_octave_jump_analysis()
    test_beat_syncopation()
