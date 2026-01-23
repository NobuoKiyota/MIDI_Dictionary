import os
import shutil
import pretty_midi
import math
import pandas as pd
from datetime import datetime
import hashlib

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
        
        groove_val = analysis_result.get('groove', '')
        groove_display = "" if groove_val == "Straight" else groove_val # Mask Straight

        # Map analysis result to "inferred_meta" structure expected by Dialog
        inferred_meta = {
            "Category": "", # Still needs some category guessing
            "Instruments": analysis_result.get('instrument', ''), 
            "Chord": analysis_result.get('chord', ''),
            "Root": analysis_result.get('root', ''),
            "Scale": analysis_result.get('scale', ''),
            "Groove": groove_display,
            "Style": analysis_result.get('style', 'Melody'),
            "TimeSignature": analysis_result.get('time_signature', '4/4'),
            "DurationBars": analysis_result.get('duration_bars', 4),
            "CommentSuffix": analysis_result.get('comment_suffix', ''),
            
            # Internal fields for Learning
            "_raw_ai_result": analysis_result
        }
        
        # --- Data-Driven Refinement ---
        # --- Data-Driven Refinement ---
        try:
             from learning_manager import LearningManager
             # Default path handling inside manager now
             lm = LearningManager()
             
             # Extract features to pass
             features = analysis_result.get('style_features', {})
             current_filename = os.path.basename(file_path)
             
             overrides = lm.predict(features, current_filename)
             if overrides:
                 print(f"Applying Learning Overrides: {overrides}")
                 inferred_meta.update(overrides)
                 
        except Exception as e:
             print(f"Prediction Error: {e}")

        # Basic Category Guessing
        avg_pitch = sum(n['pitch'] for n in notes_data) / len(notes_data) if notes_data else 60
        if avg_pitch < 48:
            inferred_meta["Category"] = "Bass"
        elif analysis_result.get('chord'): # Strong chord indication
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

    def copy_to_library(self, src_path, target_filename=None):
        """
        Copies the file to the MIDI_Library/[Hostname]/ folder. 
        Returns new absolute path.
        If target_filename is provided, it uses that name (handling extension).
        """
        import platform
        hostname = platform.node()
        
        # Subdirectory for this host
        host_lib_path = os.path.join(self.library_path, hostname)
        if not os.path.exists(host_lib_path):
            os.makedirs(host_lib_path)
            
        if target_filename:
            # Sanitize filename (remove illegal chars)
            forbidden = '<>:"/\\|?*\n\r\t'
            for char in forbidden:
                target_filename = target_filename.replace(char, '_')
            
            # Ensure extension matches source (or assume midi?) assumption safe for now
            src_ext = os.path.splitext(src_path)[1]
            if not target_filename.lower().endswith(src_ext.lower()):
                target_filename += src_ext
            filename = target_filename
        else:
            filename = os.path.basename(src_path)
            
        dest_path = os.path.join(host_lib_path, filename)
        
        # Collision handling: append _1, _2...
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(host_lib_path, f"{base}_{counter}{ext}")
            counter += 1
            
        shutil.copy2(src_path, dest_path)
        return dest_path

    def save_learning_data(self, src_path, updated_meta):
        """
        Saves the learning data to MIDI_learning folder via LearningManager.
        updated_meta: The final metadata from the dialog (User Corrected).
        """
        raw_ai = updated_meta.get("_raw_ai_result", {})
        if not raw_ai: return 

        try:
             from learning_manager import LearningManager
             # We can instantiate it fresh, or share singleton? 
             # Fresh is safer for file locks/updates.
             lm = LearningManager()
             lm.save_learning_data(src_path, updated_meta, raw_ai)
             
        except Exception as e:
            print(f"MidiHandler: Error saving learning data: {e}")
