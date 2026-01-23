import os
import pandas as pd
import numpy as np

class MidiPredictor:
    def __init__(self, learning_file_path):
        self.learning_file_path = learning_file_path
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
                print(f"Prediction: Failed to load learning data: {e}")
                
    def predict(self, current_features, current_filename):
        """
        Returns a dictionary of predicted metadata overrides based on history.
        current_features: dict of features from analyzer (e.g. {'poly_ratio': 0.5, ...})
        current_filename: string
        """
        if self.df is None or self.df.empty:
            return {}
            
        predictions = {}
        
        # 1. Filename-based Prediction (Strong Heuristic)
        # Look for past files with similar names?
        # Or simple token matching against successful past entries?
        # Let's try simple exact/partial match of filename "stems" or keywords found in history?
        # For now, let's rely on Feature Matching primarily for "AI", and use filename only for "Known Drum" check handled in analyzer.
        # But user asked "from midi filename AND xlsx content".
        
        # Try to find if we've seen this EXACT filename before (re-import)?
        # If so, return its last known GT.
        match_name = self.df[self.df['FileName'] == current_filename]
        if not match_name.empty:
            # Return the latest entry
            latest = match_name.iloc[-1]
            for col in self.gt_cols:
                key = col.replace("GT_", "")
                predictions[key] = latest[col]
            print(f"Predictor: Found exact filename match for {current_filename}")
            return predictions

        # 2. Feature-based Nearest Neighbor
        # Normalize features? 
        # For simple KNN with few dimensions, raw distance might work if scales are similar (0-1).
        # PolyRatio: 0-1, AvgDur: 0-5?, Interval: 0-12?
        # We should roughly normalize.
        
        if not self.feature_cols:
            return {}
            
        # Convert current features to vector
        # Missing features default to 0
        current_vec = []
        for col in self.feature_cols:
            key = col.replace("FEAT_", "")
            current_vec.append(current_features.get(key, 0))
        current_vec = np.array(current_vec, dtype=float)
        
        # Calculate distances
        # Vectorize?
        # Extract matches
        vectors = self.df[self.feature_cols].fillna(0).values
        
        # Euclidean Distance
        # dists = sqrt(sum((x-y)^2))
        dists = np.linalg.norm(vectors - current_vec, axis=1)
        
        # Find min distance
        min_idx = np.argmin(dists)
        min_dist = dists[min_idx]
        
        print(f"Predictor: Nearest Neighbor Dist: {min_dist:.4f}")
        
        # Threshold? If too far, don't predict?
        # Let's be aggressive for now if user wants "Proposals".
        # But if completely different, maybe bad.
        
        best_row = self.df.iloc[min_idx]
        
        # Extract GTs from best match
        # Only use if IsUserCorrected is True? Or if AI was right? 
        # We trust the row in the learning DB (it represents final state).
        
        for col in self.gt_cols:
            key = col.replace("GT_", "") # e.g. "style", "root"
            # Map back to UI expectations if needed?
            # Key map was: Root->root, etc. Matches.
            val = best_row[col]
            if pd.notna(val) and str(val) != "nan":
                 # Use capitalized Keys for UI consistency if needed?
                 # Analysis returns lowercase keys mostly?
                 # Actually inferred_meta expects specific keys.
                 # Let's map them.
                 
                 # Map: root -> Root, scale -> Scale...
                 # But our GT_ keys actally CAME from UI keys or AI keys?
                 # In midi_utils.save: GT_{ai_k}. ai_k are lowercase.
                 
                 # We need to return keys that matching 'inferred_meta' in midi_utils.
                 # midi_utils expects: "Root", "Scale", "Chord", "Groove", "Style", "TimeSignature"
                 
                 ui_key = key.capitalize() # root->Root
                 if key == "time_signature": ui_key = "TimeSignature"
                 elif key == "beat_type": continue # Not explicitly in dialog input fields? 
                 # Dialog has no BeatType input? It generates "Groove" from it? No.
                 # Dialog uses Groove field.
                 
                 predictions[ui_key] = val
                 
        # 3. Filename "Tokinization" Matching against History
        # If user names file "MyFunkyBass", and history has "FunkyBass" -> Style "Funk"?
        # This is powerful.
        current_lower = current_filename.lower()
        
        # Check simple substring hits in history FileNames
        # Score history items by how much their filename overlaps with current?
        # Simple implementation:
        # If a history file name (minus extension) is a substring of current, or vice versa?
        
        return predictions
