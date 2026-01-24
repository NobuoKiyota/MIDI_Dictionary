import pretty_midi
from midi_ensemble_generator import EnsembleGenerator
from midi_analyzer import NoteAnalysis

def test_grouping():
    print("--- Testing group_by_beat ---")
    gen = EnsembleGenerator()
    
    # Mock Analysis Objects (Minimal necessary attributes)
    # Notes at 0.0, 0.125, 0.25, 0.375
    notes = []
    times = [0.0, 0.125, 0.25, 0.375]
    for t in times:
        n = pretty_midi.Note(100, 40, t, t+0.1)
        # NoteAnalysis: note, is_on_beat, sub_beat_type, is_syncopated, is_mute, is_dotted, harmonic_pitch
        ana = NoteAnalysis(n, True, '1', False, False, False, 40)
        notes.append(ana)
        
    beats = [0.0, 0.5, 1.0, 1.5]
    
    print(f"Notes start: {[n.note.start for n in notes]}")
    print(f"Beats: {beats}")
    
    groups = gen.group_by_beat(notes, beats)
    print(f"Result Groups Count: {len(groups)}")
    
    for i, g in enumerate(groups):
        print(f"Group {i}: Start={g['start']}, End={g['end']}, NoteCount={len(g['notes'])}")

if __name__ == "__main__":
    test_grouping()
