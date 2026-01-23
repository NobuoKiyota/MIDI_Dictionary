import os
import pandas as pd
import numpy as np
import shutil
from datetime import datetime

class LearningManager:
    """
    Centralized manager for AI Learning (Read/Write to Excel).
    Replaces MidiPredictor and duplicated logic in midi_utils/style_trainer.
    """
    def __init__(self, learning_file_path=None):
        if learning_file_path:
            self.learning_file_path = learning_file_path
        else:
             # Default path relative to this file? Or pass from caller.
             # Ideally relative to main.py or known location.
             # Providing a default fallback:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            self.learning_file_path = os.path.join(project_root, "MIDI_learning", "learning_data.xlsx")
            
        self.df = None
        self._load_data()
        
    def _load_data(self):
        if os.path.exists(self.learning_file_path):
            try:
                self.df = pd.read_excel(self.learning_file_path)
                # Ensure we have feature columns
                self.feature_cols = [c for c in self.df.columns if c.startswith("FEAT_")]
                # Ensure we have GT columns
                self.gt_cols = [c for c in self.df.columns if c.startswith("GT_")]
            except Exception as e:
                print(f"LearningManager: Failed to load data: {e}")
                self.df = pd.DataFrame()
        else:
            self.df = pd.DataFrame()

    def predict(self, current_features, current_filename):
        """
        Returns a dictionary of predicted metadata overrides based on history.
        current_features: dict of features from analyzer (e.g. {'poly_ratio': 0.5, ...})
        current_filename: string
        """
        if self.df is None or self.df.empty:
            return {}
            
        predictions = {}
        
        # 1. Filename-based Match (Exact)
        match_name = self.df[self.df['FileName'] == current_filename]
        if not match_name.empty:
            # Return the latest entry
            latest = match_name.iloc[-1]
            for col in self.gt_cols:
                key = col.replace("GT_", "")
                predictions[self._map_key_to_ui(key)] = latest[col]
            print(f"LearningManager: Found exact filename match for {current_filename}")
            return predictions

        # 2. Feature-based Nearest Neighbor
        if not self.feature_cols:
            return {}
            
        # Convert current features to vector
        current_vec = []
        for col in self.feature_cols:
            key = col.replace("FEAT_", "")
            current_vec.append(current_features.get(key, 0))
        current_vec = np.array(current_vec, dtype=float)
        
        vectors = self.df[self.feature_cols].fillna(0).values
        dists = np.linalg.norm(vectors - current_vec, axis=1)
        
        min_idx = np.argmin(dists)
        # min_dist = dists[min_idx] # Could use threshold
        
        best_row = self.df.iloc[min_idx]
        
        for col in self.gt_cols:
            key = col.replace("GT_", "")
            val = best_row[col]
            if pd.notna(val) and str(val) != "nan":
                 predictions[self._map_key_to_ui(key)] = val
                 
        return predictions

    def save_learning_data(self, src_path, updated_meta, raw_ai_data):
        """
        Saves the learning data to Excel.
        src_path: Absolute path to source MIDI
        updated_meta: User Corrected metadata dict (UI Keys Caplitalized)
        raw_ai_data: Original Analysis result (snake_case)
        """
        filename = os.path.basename(src_path)
        learning_dir = os.path.dirname(self.learning_file_path)
        
        # 1. Prepare Directory & Copy File
        if not os.path.exists(learning_dir):
            os.makedirs(learning_dir)
            
        dest_path = os.path.join(learning_dir, filename)
        try:
            shutil.copy2(src_path, dest_path)
        except Exception as e:
            print(f"LearningManager: Error copying file: {e}") 
        
        # 2. Prepare Data Row
        key_map = self._get_key_map()
        correction_count = 0
        ground_truth = {}
        
        # Helper for numpy types
        def to_native(obj):
            if hasattr(obj, 'item'): return obj.item()
            return obj

        for ui_k, ai_k in key_map.items():
            user_val = str(updated_meta.get(ui_k, "")).strip()
            ai_val = str(raw_ai_data.get(ai_k, "")).strip()
            
            # Logic: If UI is empty but AI said Straight (Groove), it's a match.
            # Usually UI Groove field placeholder implies Straight.
            
            # Ground Truth Value
            gt_val = user_val
            if ui_k == "Groove" and user_val == "":
                gt_val = "Straight" # Implicit default
                
            # Compare
            is_diff = False
            if ai_k == "groove" and ai_val == "Straight" and user_val == "":
                is_diff = False
            elif user_val != ai_val:
                is_diff = True
                
            if is_diff:
                correction_count += 1
                
        row = {
            "FileName": filename,
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "IsUserCorrected": correction_count > 0,
            "CorrectionCount": correction_count
        }
        
        # Add Ground Truth
        for ui_k, ai_k in key_map.items():
            val = updated_meta.get(ui_k, "")
            if ui_k == "Groove" and val == "": val = "Straight"
            row[f"GT_{ai_k}"] = val
            
        # Add AI Prediction
        for ai_k in key_map.values():
            row[f"AI_{ai_k}"] = str(raw_ai_data.get(ai_k, ""))
            
        # Add Features
        features = raw_ai_data.get('style_features', {})
        for k, v in features.items():
            row[f"FEAT_{k}"] = to_native(v)
            
        # 3. Save to Excel
        try:
            if os.path.exists(self.learning_file_path):
                # Reload to be safe against concurrency (though single threaded mostly)
                current_df = pd.read_excel(self.learning_file_path)
                current_df = pd.concat([current_df, pd.DataFrame([row])], ignore_index=True)
            else:
                current_df = pd.DataFrame([row])
            
            current_df.to_excel(self.learning_file_path, index=False)
            self.df = current_df # Update cache
            print(f"LearningManager: Saved data for {filename}")
            
        except Exception as e:
            print(f"LearningManager: Excel Save Error: {e}")

    def _get_key_map(self):
        return {
            "Root": "root",
            "Scale": "scale",
            "Chord": "chord",
            "TimeSignature": "time_signature",
            "Groove": "groove",
            "Style": "style"
        }

    def _map_key_to_ui(self, db_key):
        # Reverse map for simple keys, special case for exceptions
        # db_key is snake_case (e.g. time_signature)
        # We want CamelCase (TimeSignature)
        if db_key == "time_signature": return "TimeSignature"
        return db_key.capitalize()
