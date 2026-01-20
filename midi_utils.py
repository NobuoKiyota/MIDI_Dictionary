import os
import shutil
import pretty_midi
import math

class MidiHandler:
    def __init__(self, library_path):
        self.library_path = library_path
        if not os.path.exists(self.library_path):
            os.makedirs(self.library_path)

    def load_midi(self, file_path):
        """Loads a MIDI file using pretty_midi."""
        try:
            pm = pretty_midi.PrettyMIDI(file_path)
            return pm
        except Exception as e:
            print(f"Error loading MIDI {file_path}: {e}")
            return None

    def analyze_midi(self, file_path):
        """
        Analyzes a MIDI file to extract metadata for the preview and database.
        Returns a dictionary with:
        - duration_bar: Approx duration in bars (assuming 4/4 if not found or using first TS)
        - time_signature: "num/den" string
        - notes: List of dicts {pitch, start, end, velocity}
        - max_velocity: int
        """
        pm = self.load_midi(file_path)
        if not pm:
            return None

        # Get Time Signature
        ts_str = "4/4"
        if pm.time_signature_changes:
            ts = pm.time_signature_changes[0]
            ts_str = f"{ts.numerator}/{ts.denominator}"
        
        # Calculate Duration in Bars
        # This is an approximation. If multiple TS changes exist, it's complex.
        # We will use the global tempo and first TS for a rough estimate if beats are available.
        # Or simply use the max end time and assume a standard tempo if none.
        # For simplicity, let's rely on pretty_midi's get_beats() or get_end_time().
        
        # Calculate bars based on first TS and tempo
        # detailed bar calc can be complex, for now let's just return duration in seconds
        # and let the user input the bar count manually or estimate it.
        # BUT the requirement says "Auto analyze measure count".
        # Let's try to estimate bars:
        end_time = pm.get_end_time()
        
        # Estimate BPM if available, else 120
        tempo = 120.0
        if pm.get_tempo_changes()[1].size > 0:
            tempo = pm.get_tempo_changes()[1][0]
        
        seconds_per_beat = 60.0 / tempo
        beats = end_time / seconds_per_beat
        
        # Assume numerator from TS
        numerator = 4
        if pm.time_signature_changes:
            numerator = pm.time_signature_changes[0].numerator
            
        bars = math.ceil(beats / numerator)

        # Collect Notes for Preview
        notes_data = []
        max_velocity = 0
        
        for instrument in pm.instruments:
            if instrument.is_drum:
                continue # Optionally skip drums for melody preview or handle differently? 
                # Request says "Midi Note Piano Roll", usually usually implies all notes.
                # Let's include everything but maybe mark tracks.
                # For now, merge all.
            pass

        # Re-iterate to include all
        for instrument in pm.instruments:
            for note in instrument.notes:
                notes_data.append({
                    'pitch': note.pitch,
                    'start': note.start,
                    'end': note.end,
                    'velocity': note.velocity
                })
                if note.velocity > max_velocity:
                    max_velocity = note.velocity
        
        return {
            'time_signature': ts_str,
            'duration_bars': bars,
            'max_velocity': max_velocity,
            'notes': notes_data,
            'tempo': tempo,
            'inferred_meta': self._infer_metadata(pm, notes_data, file_path)
        }

    def _infer_metadata(self, pm, notes, file_path):
        meta = {
            "Category": "",
            "Instruments": "",
            "Chord": "",
            "Root": ""
        }
        
        # 1. Instruments (from filename or tracks)
        fname = os.path.basename(file_path)
        meta["Instruments"] = os.path.splitext(fname)[0]
        
        # 2. Drums Detection
        is_drum = False
        # Check channel 10 (index 9)
        for inst in pm.instruments:
            if inst.is_drum:
                is_drum = True
                break
        
        # Check specific GM notes if not flagged
        if not is_drum:
            drum_notes = {36, 38, 42, 46, 49, 51} # C1, D1, F#1, Bb1, C#2, Eb2 (Common Kick/Snare/Hat)
            hit_count = 0
            for n in notes:
                if n['pitch'] in drum_notes:
                    hit_count += 1
            if len(notes) > 0 and (hit_count / len(notes)) > 0.3:
                is_drum = True

        if is_drum:
            meta["Category"] = "Perc" # or "Rythem"?
            return meta

        # 3. Analyze Pitch & Polyphony
        if not notes:
            return meta
            
        avg_pitch = sum(n['pitch'] for n in notes) / len(notes)
        
        # Polyphony Check (overlap)
        # Simply sort by start time
        sorted_notes = sorted(notes, key=lambda x: x['start'])
        max_polyphony = 0
        current_active = 0
        events = [] # (time, type) +1 start, -1 end
        for n in notes:
            events.append((n['start'], 1))
            events.append((n['end'], -1))
        events.sort(key=lambda x: (x[0], x[1])) # Process start before end if same time?
        
        temp_poly = 0
        for _, type_ in events:
            temp_poly += type_
            max_polyphony = max(max_polyphony, temp_poly)
            
        # 4. Bass Detection
        # Low pitch + Monophonic (or low polyphony)
        if avg_pitch < 48 and max_polyphony <= 1:
            meta["Category"] = "Bass"
            # Infer Root? Most frequent pitch class
            # ...
        
        # 5. Chord Detection
        elif max_polyphony >= 3:
            meta["Category"] = "Chord"
            # Try to identify first chord
            # Group notes at start
            first_time = sorted_notes[0]['start']
            first_chord_notes = [n['pitch'] for n in sorted_notes if abs(n['start'] - first_time) < 0.1]
            
            if len(first_chord_notes) >= 3:
                # Naive chord ID
                root, quality = self._identify_chord(first_chord_notes)
                if root: meta["Root"] = root
                if quality: meta["Chord"] = quality

        else:
            # Melody / Lead / Arp
            meta["Category"] = "Melody"
            
            # Infer Root
            # Most distinct bass note or first note?
            # Use First Note as Root guess for now
            pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            root_pc = sorted_notes[0]['pitch'] % 12
            meta["Root"] = pitch_classes[root_pc]

        return meta

    def _identify_chord(self, pitches):
        # pitches: list of midi numbers
        # Remove duplicates, sort
        unique_pcs = sorted(list(set([p % 12 for p in pitches])))
        
        pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        
        if len(unique_pcs) < 3:
            return None, None
            
        # Brute force: check intervals from each note as root
        # Major: 0, 4, 7
        # Minor: 0, 3, 7
        # 7th: 0, 4, 7, 10
        # M7: 0, 4, 7, 11
        
        for root in unique_pcs:
            intervals = set([(p - root) % 12 for p in unique_pcs])
            
            if {0, 4, 7}.issubset(intervals):
                if 11 in intervals: return pitch_classes[root], "M7"
                if 10 in intervals: return pitch_classes[root], "7th"
                return pitch_classes[root], "Major"
            
            if {0, 3, 7}.issubset(intervals):
                if 10 in intervals: return pitch_classes[root], "minor" # minor7 technically but stick to basic
                return pitch_classes[root], "minor"

        return None, None

    def copy_to_library(self, src_path):
        """Copies the file to the MIDI_Library folder. Returns new absolute path."""
        filename = os.path.basename(src_path)
        dest_path = os.path.join(self.library_path, filename)
        
        # Simple collision handling
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(self.library_path, f"{base}_{counter}{ext}")
            counter += 1
            
        shutil.copy2(src_path, dest_path)
        return dest_path
