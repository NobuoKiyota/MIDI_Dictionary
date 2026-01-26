import pretty_midi
try:
    from .constants import NOTE_NAMES
except ImportError:
    from constants import NOTE_NAMES

def detect_key(midi_data):
    """
    Simple Key Detection using simple pitch class counting matching against Major/Minor profiles.
    Returns (root_note_index, scale_type_str) e.g., (0, 'Major') for C Major.
    """
    total_duration = [0] * 12
    for inst in midi_data.instruments:
        if inst.is_drum: continue
        for note in inst.notes:
            duration = note.end - note.start
            total_duration[note.pitch % 12] += duration
            
    # Normalize
    total = sum(total_duration)
    if total == 0: return (0, 'Major') # Default C Major
    
    # Profiles (Simple weights)
    maj_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    min_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
    
    best_score = -float('inf')
    best_key = (0, 'Major')
    
    # Test all 12 roots for Major and Minor
    for root in range(12):
        # Major Correlation
        score = 0
        for i in range(12):
            score += total_duration[(root + i) % 12] * maj_profile[i]
        if score > best_score:
            best_score = score
            best_key = (root, 'Major')
            
        # Minor Correlation
        score = 0
        for i in range(12):
            score += total_duration[(root + i) % 12] * min_profile[i]
        if score > best_score:
            best_score = score
            best_key = (root, 'Minor')
            
    return best_key

def get_tempo_at_time(midi_data, time):
    """
    Get BPM at specific time using tempo changes.
    """
    tempo_changes = midi_data.get_tempo_changes()
    # tempo_changes is unique: (times, bpms) arrays
    
    last_bpm = 120.0 # Default
    times, bpms = tempo_changes
    
    # Linear search (optimized for standard MIDI size)
    for t, bpm in zip(times, bpms):
        if t <= time:
            last_bpm = bpm
        else:
            break
    return last_bpm
