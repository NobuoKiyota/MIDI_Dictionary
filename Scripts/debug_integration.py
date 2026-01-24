import pretty_midi
import os
from midi_ensemble_generator import EnsembleGenerator
from midi_analyzer import MidiAnalyzer

def test_integration():
    print("--- Testing Integration ---")
    filename = "z:/MIDI_Dictionary/test_beat_gen.mid"
    if not os.path.exists(filename):
        print("Test file missing!")
        return

    gen = EnsembleGenerator()
    midi_data = gen.load_midi(filename)
    inst = midi_data.instruments[0]
    beats = midi_data.get_beats()
    
    print(f"Notes: {len(inst.notes)}")
    print(f"Beats: {len(beats)}")
    
    analyzer = MidiAnalyzer(midi_data)
    analysis_list = analyzer.analyze_track(inst)
    print(f"Analysis Items: {len(analysis_list)}")
    
    groups = gen.group_by_beat(analysis_list, beats)
    print(f"Groups: {len(groups)}")
    
    if len(groups) > 0:
        notes_in_g0 = groups[0]['notes']
        print(f"Group 0 Notes: {len(notes_in_g0)}")
        if len(notes_in_g0) > 0:
            dom = gen.get_dominant_root(notes_in_g0)
            print(f"Dominant Note: Pitch={dom.note.pitch}")

if __name__ == "__main__":
    test_integration()
