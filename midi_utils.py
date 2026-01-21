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
        Analyzes a MIDI file to extract metadata for the preview and database using MidiAnalyzer.
        """
        from midi_analyzer import MidiAnalyzer
        analyzer = MidiAnalyzer()
        
        # Use simple load first to check validity and get basic notes for preview
        pm = self.load_midi(file_path)
        if not pm:
            return None

        # Detailed Analysis
        analysis_result = analyzer.analyze(file_path) # This does the heavy lifting
        
        # Prepare notes for UI Piano Roll
        notes_data = []
        max_velocity = 0
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

        # Construct result dictionary matching expectation + new metadata
        # infer_metadata is now populated by analysis_result
        
        # Map analysis result to "inferred_meta" structure expected by Dialog
        inferred_meta = {
            "Category": "", # Still needs some category guessing if analyzer didn't return it partially
            "Instruments": "", # Will fill with filename in dialog logic usually
            "Chord": analysis_result.get('chord', ''),
            "Root": analysis_result.get('root', ''),
            "TimeSignature": analysis_result.get('time_signature', '4/4'),
            "DurationBars": analysis_result.get('duration_bars', 4),
            "CommentSuffix": analysis_result.get('comment_suffix', '')
        }

        # Basic Category Guessing (Ported/Simplified from old logic if Analyzer doesn't provide it)
        # Analyzer provides 'style', let's use that to help Category?
        # Or keep the Polyphony/Pitch logic?
        # Let's simple check:
        avg_pitch = sum(n['pitch'] for n in notes_data) / len(notes_data) if notes_data else 60
        if avg_pitch < 48:
            inferred_meta["Category"] = "Bass"
        elif analysis_result['chord']: # Strong chord indication
            inferred_meta["Category"] = "Chord"
        else:
            inferred_meta["Category"] = "Melody" # Default
            
        return {
            'time_signature': analysis_result['time_signature'],
            'duration_bars': analysis_result['duration_bars'],
            'max_velocity': max_velocity,
            'notes': notes_data,
            'tempo': analysis_result['tempo'],
            'inferred_meta': inferred_meta
        }

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
