import pretty_midi

def create_midi(filename, notes):
    midi = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=33) # Bass
    current_time = 0.0
    duration = 1.0
    
    for pitch in notes:
        note = pretty_midi.Note(velocity=100, pitch=pitch, start=current_time, end=current_time + duration)
        inst.notes.append(note)
        current_time += duration
        
    midi.instruments.append(inst)
    midi.write(filename)
    print(f"Created {filename}")

if __name__ == "__main__":
    # E Major Scale: E, F#, G#, A, B, C#, D#
    # E2 = 40
    # E2(40), F#2(42), G#2(44), A2(45), B2(47), C#3(49), D#3(51)
    e_major_notes = [40, 42, 44, 45, 47, 49, 51]
    create_midi("z:/MIDI_Dictionary/Bass_E_Major.mid", e_major_notes)

    # G Minor Scale: G, A, Bb, C, D, Eb, F
    # G2 = 43
    # G2(43), A2(45), Bb2(46), C3(48), D3(50), Eb3(51), F3(53)
    g_minor_notes = [43, 45, 46, 48, 50, 51, 53]
    create_midi("z:/MIDI_Dictionary/Bass_G_Minor.mid", g_minor_notes)
