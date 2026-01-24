import pretty_midi
import os

def check_midi(file_path):
    try:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return

        midi = pretty_midi.PrettyMIDI(file_path)
        if not midi.instruments:
            print("No instruments found")
            return

        inst = midi.instruments[0]
        print(f"File: {file_path}")
        print(f"Note Count: {len(inst.notes)}")
        for i, note in enumerate(inst.notes):
            print(f"Note {i}: Pitch={note.pitch}, Vel={note.velocity}, Start={note.start:.2f}, End={note.end:.2f}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_midi("z:/MIDI_Dictionary/output/test_bass_Closed_Rhythm.mid")
