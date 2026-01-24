import pretty_midi
import math
from midi_analyzer import MidiAnalyzer

def test_v1_3_analysis():
    print("\n--- Testing V1.3 Analysis Features ---")
    
    midi = pretty_midi.PrettyMIDI(initial_tempo=120)
    inst = pretty_midi.Instrument(program=33)
    
    # 1. Sub-beat Test (Quarter Note = 0.5s)
    # 2.0: 1 (On Beat)
    # 2.125: e (+0.125s)
    # 2.25: & (+0.25s)
    # 2.375: a (+0.375s)
    notes_rhythm = [
        pretty_midi.Note(100, 40, 2.0, 2.1),   # 1
        pretty_midi.Note(100, 40, 2.125, 2.2), # e
        pretty_midi.Note(100, 40, 2.25, 2.35), # &
        pretty_midi.Note(100, 40, 2.375, 2.45) # a
    ]
    
    # 2. Dynamic Mute Test
    # Avg Vel will be around 100. Threshold 60 -> 60.
    # Note Mute 1: Short time (0.015s) - Should be mute regardless of Vel.
    # Note Mute 2: Short beat (0.1 beat), Low Vel (40). Should be mute.
    # Note Active: Short beat (0.1 beat), High Vel (100). Should NOT be mute.
    
    notes_mute = [
        pretty_midi.Note(100, 40, 0.0, 0.015), # Mute (Time)
        pretty_midi.Note(40, 40, 1.0, 1.05),   # Mute (Vel+Beat). 0.05s is 0.1 beat. Vel 40 < 60.
        pretty_midi.Note(100, 40, 1.5, 1.55)   # Active (Vel High).
    ]
    
    # 3. Harmonic Window Test
    # Pattern: E2(40) -> E2(40) -> E2(40) -> E3(52) -> E3(52) -> E2(40)
    # Window should stabilize E3s to E2s?
    # Window size 3.
    # 1. 40. Window [40]. Avg 40.
    # 2. 40. Window [40, 40]. Avg 40.
    # 3. 40. Window [40, 40, 40]. Avg 40.
    # 4. 52. Dist 12 > 7. Prev=40. 52%12 == 40%12. Octave Jump!
    #    -> Fold to Prev (40). Harmonic=40. Window [40, 40, 40].
    # 5. 52. Dist 12. Prev=40 (Wait, Harmonic was 40).
    #    Logic uses "last_pitch = pitch_window[-1]" which is harmonic pitch.
    #    So Prev is 40. 52 folds to 40.
    # 6. 40. Normal.
    
    notes_harmonic = [
        pretty_midi.Note(100, 40, 3.0, 3.5),
        pretty_midi.Note(100, 40, 3.5, 4.0),
        pretty_midi.Note(100, 40, 4.0, 4.5),
        pretty_midi.Note(100, 52, 4.5, 5.0), # Octave Jump E3
        pretty_midi.Note(100, 52, 5.0, 5.5), # Sustained E3?
        pretty_midi.Note(100, 40, 5.5, 6.0)  # Back to E2
    ]
    
    inst.notes.extend(notes_mute + notes_rhythm + notes_harmonic)
    # sort by start time? pretty_midi might require sorted notes for some internal logic, 
    # but MidiAnalyzer iterates sequentially. 
    # Let's sort to be safe and match expected indices.
    inst.notes.sort(key=lambda n: n.start)
    
    midi.instruments.append(inst)
    
    analyzer = MidiAnalyzer(midi)
    analysis = analyzer.analyze_track(inst)
    
    # Verify Mute (Indices 0, 1, 2)
    print(f"Mute 1 (Time): {analysis[0].is_mute} (Exp: True)")
    print(f"Mute 2 (Vel): {analysis[1].is_mute} (Exp: True)")
    print(f"Mute 3 (Active): {analysis[2].is_mute} (Exp: False)")
    
    # Verify Rhythm (Indices 3, 4, 5, 6)
    # 2.0 -> 1
    # 2.125 -> e
    # 2.25 -> &
    # 2.375 -> a
    r_types = [a.sub_beat_type for a in analysis[3:7]]
    print(f"Rhythm Types: {r_types} (Exp: ['1', 'e', '&', 'a'])")
    
    # Verify Harmonic (Indices 7, 8, 9, 10, 11, 12)
    # Pitches: 40, 40, 40, 52, 52, 40
    # Expected Harmonic: 40, 40, 40, 40, 40, 40
    h_pitches = [a.harmonic_pitch for a in analysis[7:]]
    print(f"Harmonic Pitches: {h_pitches} (Exp: [40, 40, 40, 40, 40, 40])")
    
    pass_mute = analysis[0].is_mute and analysis[1].is_mute and not analysis[2].is_mute
    pass_rhythm = r_types == ['1', 'e', '&', 'a']
    pass_harmonic = h_pitches == [40, 40, 40, 40, 40, 40]
    
    if pass_mute and pass_rhythm and pass_harmonic:
        print("[SUCCESS] All V1.3 Checks Passed")
    else:
        print("[FAIL] Some Checks Failed")

if __name__ == "__main__":
    test_v1_3_analysis()
