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
        try:
             from midi_predictor import MidiPredictor
             learning_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MIDI_learning", "learning_data.xlsx")
             predictor = MidiPredictor(learning_path)
             
             # Extract features to pass
             features = analysis_result.get('style_features', {})
             current_filename = os.path.basename(file_path)
             
             overrides = predictor.predict(features, current_filename)
             if overrides:
                 print(f"Applying Learning Overrides: {overrides}")
                 inferred_meta.update(overrides)
                 # Note: Category is not in GT usually? 
                 # If GT has Category, we could map it. 
                 # But learning_data.xlsx schema (via style_trainer) currently doesn't seem to save Category explicitly in GT?
                 # It saves Root, Scale, Chord, TimeSig, Groove, Style.
                 # So Category guessing logic below still runs, which is fine.
                 
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
        Saves the learning data to MIDI_learning folder.
        updated_meta: The final metadata from the dialog (User Corrected).
        """
        raw_ai = updated_meta.get("_raw_ai_result", {})
        if not raw_ai: return # Should not happen if flow is correct

        filename = os.path.basename(src_path)
        learning_dir = "MIDI_learning"
        
        # 1. Prepare Directory
        if not os.path.exists(learning_dir):
            os.makedirs(learning_dir)
            
        # 2. Copy MIDI File
        dest_path = os.path.join(learning_dir, filename)
        try:
            shutil.copy2(src_path, dest_path)
        except Exception as e:
            print(f"Error copying learning file: {e}") 
            # Continue to save excel even if copy fails? No, better warn but we are in logic class.
            
        # 3. Prepare Data for Excel
        # Helper to convert numpy types
        def to_native(obj):
            if hasattr(obj, 'item'): 
                return obj.item()
            return obj

        # Map UI keys (Capitalized) to AI keys (snake_case)
        # UI: Root, Scale, Chord, TimeSignature, Groove, Style
        # AI: root, scale, chord, time_signature, groove, style
        
        key_map = {
            "Root": "root",
            "Scale": "scale",
            "Chord": "chord",
            "TimeSignature": "time_signature",
            "Groove": "groove",
            "Style": "style"
        }

        # Determine corrections
        correction_count = 0
        ground_truth = {}
        
        for ui_k, ai_k in key_map.items():
            user_val = str(updated_meta.get(ui_k, "")).strip()
            ai_val = str(raw_ai.get(ai_k, "")).strip()
            
            # Groove Special: UI might be empty for Straight
            if ai_k == "groove" and ai_val == "Straight" and user_val == "":
                # Matches (UI empty == Straight)
                ground_truth[ai_k] = "Straight"
            else:
                ground_truth[ai_k] = user_val if user_val else ai_val # Fallback? No, UI value IS the truth.
                # If UI value matches AI value (or empty is not allowed logic), count diffs.
                # In main app, UI is pre-filled. So User val IS always present.
                if user_val != ai_val:
                    # Specific check for Groove Straight vs Empty
                    if ai_k == "groove" and ai_val == "Straight" and user_val == "":
                        pass # No correction
                    else:
                        correction_count += 1
        
        row = {
            "FileName": filename,
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "IsUserCorrected": correction_count > 0,
            "CorrectionCount": correction_count
        }
        
        # Add Ground Truth
        for ui_k, ai_k in key_map.items():
             # If UI Groove is empty, it means Straight
            val = updated_meta.get(ui_k, "")
            if ui_k == "Groove" and val == "":
                val = "Straight"
            row[f"GT_{ai_k}"] = val
            
        # Add AI Prediction
        for ai_k in key_map.values():
            row[f"AI_{ai_k}"] = str(raw_ai.get(ai_k, ""))
            
        # Add Features
        features = raw_ai.get('style_features', {})
        for k, v in features.items():
            row[f"FEAT_{k}"] = to_native(v)
            
        # 4. Save to Excel
        excel_path = os.path.join(learning_dir, "learning_data.xlsx")
        try:
            if os.path.exists(excel_path):
                df = pd.read_excel(excel_path)
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            else:
                df = pd.DataFrame([row])
            df.to_excel(excel_path, index=False)
        except Exception as e:
            print(f"Excel Save Error: {e}")
