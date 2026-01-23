import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import json
import hashlib
from midi_analyzer import MidiAnalyzer
import shutil
import pandas as pd
from datetime import datetime

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    print("tkinterdnd2 module not found. Drag and drop will be disabled.")

# Settings
DATA_FILE = "midi_learning_data.json"
APPEARANCE_MODE = "Dark"
COLOR_THEME = "blue"

ctk.set_appearance_mode(APPEARANCE_MODE)
ctk.set_default_color_theme(COLOR_THEME)

class StyleTrainerApp(ctk.CTk, TkinterDnD.DnDWrapper if HAS_DND else object):
    def __init__(self):
        super().__init__()
        
        if HAS_DND:
            self.TkdndVersion = TkinterDnD._require(self)

        self.title("MIDI Dictionary - Style Trainer")
        self.geometry("800x600")
        
        # Enable DnD
        if HAS_DND:
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.on_drop)
        
        self.analyzer = MidiAnalyzer()
        self.current_midi_path = None
        self.current_result = None
        
        # Grid Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=1) # Main Content
        self.grid_rowconfigure(2, weight=0) # Footer

        # --- Top Area: File Info & Load ---
        self.top_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        
        self.btn_load = ctk.CTkButton(self.top_frame, text="Load MIDI", width=100, command=self.load_midi)
        self.btn_load.pack(side="left", padx=(0, 20))
        
        self.lbl_filename = ctk.CTkLabel(self.top_frame, text="Drag & Drop MIDI file here", font=("Arial", 16))
        self.lbl_filename.pack(side="left", fill="x", expand=True)

        # --- Main Area: The Grid ---
        # Scrollable frame for parameters
        self.grid_frame = ctk.CTkScrollableFrame(self, label_text="Analysis Result & Correction")
        self.grid_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.grid_frame.grid_columnconfigure(0, weight=1) # Param Name
        self.grid_frame.grid_columnconfigure(1, weight=2) # AI
        self.grid_frame.grid_columnconfigure(2, weight=2) # USER
        
        # Define Rows
        # Key: (Label, DictionaryKey)
        self.param_defs = [
            ("Root", "root"),
            ("Scale", "scale"),
            ("Chord", "chord"),
            ("Time Sig", "time_signature"),
            ("Beat", "beat_type"),
            ("Groove (Artic)", "groove"),
            ("Style", "style")
        ]
        
        self.rows = {} # store widgets for each row
        
        # Header Row
        ctk.CTkLabel(self.grid_frame, text="Parameter", font=("Arial", 14, "bold")).grid(row=0, column=0, pady=5, sticky="w")
        ctk.CTkLabel(self.grid_frame, text="AI Prediction", font=("Arial", 14, "bold"), text_color="#4da6ff").grid(row=0, column=1, pady=5, sticky="w")
        ctk.CTkLabel(self.grid_frame, text="USER Correction (Leave empty if correct)", font=("Arial", 14, "bold"), text_color="#ff9933").grid(row=0, column=2, pady=5, sticky="w")
        
        for i, (label, key) in enumerate(self.param_defs, start=1):
            # Label
            lbl = ctk.CTkLabel(self.grid_frame, text=label)
            lbl.grid(row=i, column=0, pady=5, padx=10, sticky="w")
            
            # AI Value
            lbl_ai = ctk.CTkEntry(self.grid_frame, state="readonly", fg_color="#2b2b2b", text_color="white")
            lbl_ai.grid(row=i, column=1, pady=5, padx=10, sticky="ew")
            
            # User Value (Entry with placeholder)
            ent_user = ctk.CTkEntry(self.grid_frame, placeholder_text="Enter correct value if wrong")
            ent_user.grid(row=i, column=2, pady=5, padx=10, sticky="ew")
            
            self.rows[key] = {
                "ai_widget": lbl_ai,
                "user_widget": ent_user,
                "row_index": i
            }

        # --- Footer Area: Learned Button ---
        self.footer_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.footer_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
        
        # Grid for footer buttons
        self.footer_frame.grid_columnconfigure(0, weight=1)
        self.footer_frame.grid_columnconfigure(1, weight=1)

        self.btn_vis = ctk.CTkButton(self.footer_frame, text="📊 Visualize Progress", height=50, font=("Arial", 14), fg_color="#555", command=self.open_visualization)
        self.btn_vis.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.btn_learn = ctk.CTkButton(self.footer_frame, text="LEARNED", height=50, font=("Arial", 18, "bold"), command=self.on_learn, state="disabled")
        self.btn_learn.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        
        # Status Label below buttons
        self.lbl_status = ctk.CTkLabel(self.footer_frame, text="Ready", text_color="gray")
        self.lbl_status.grid(row=1, column=0, columnspan=2, pady=5)
        
    def open_visualization(self):
        from learning_visualizer import LearningVisualizer
        learning_path = os.path.join("MIDI_learning", "learning_data.xlsx")
        LearningVisualizer(self, learning_path)

    def on_drop(self, event):
        if not event.data: return
        files = self.tk.splitlist(event.data)
        for f in files:
            path = f.strip('{}').strip('"')
            if os.path.isfile(path) and (path.lower().endswith(".mid") or path.lower().endswith(".midi")):
                self.analyze_file(path)
                return

    def load_midi(self):
        file_path = filedialog.askopenfilename(filetypes=[("MIDI files", "*.mid")])
        if file_path:
            self.analyze_file(file_path)

    def analyze_file(self, file_path):
        self.current_midi_path = file_path
        filename = os.path.basename(file_path)
        self.lbl_filename.configure(text=f"Editing: {filename}")
        
        try:
            self.current_result = self.analyzer.analyze(file_path)
            
            # Populate Grid
            for key, widgets in self.rows.items():
                val = str(self.current_result.get(key, ""))
                
                # Special handling for Groove
                if key == "groove" and val == "Straight":
                    val = ""
                
                # Set AI Value
                widgets["ai_widget"].configure(state="normal")
                widgets["ai_widget"].delete(0, "end")
                widgets["ai_widget"].insert(0, val)
                widgets["ai_widget"].configure(state="readonly")
                
                # Clear User Value
                widgets["user_widget"].delete(0, "end")
            
            self.btn_learn.configure(state="normal")
            self.lbl_status.configure(text="Analysis Complete. Please review and correct if necessary.", text_color="cyan")
            
        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed: {e}")
            self.lbl_status.configure(text=f"Error: {e}", text_color="red")

    def on_learn(self):
        if not self.current_midi_path or not self.current_result: return
        
        # Gather Data
        learned_data = {}
        correction_count = 0
        
        for key, widgets in self.rows.items():
            ai_val = widgets["ai_widget"].get()
            user_val = widgets["user_widget"].get().strip()
            
            if user_val:
                # User corrected
                learned_data[key] = user_val
                correction_count += 1
            else:
                # AI correct
                learned_data[key] = ai_val
                
        # Save
        self.save_data(learned_data, correction_count)

    def save_data(self, final_data, correction_count):
        filename = os.path.basename(self.current_midi_path)
        learning_dir = "MIDI_learning"
        
        # 1. Prepare Directory
        if not os.path.exists(learning_dir):
            os.makedirs(learning_dir)
            
        # 2. Copy MIDI File
        dest_path = os.path.join(learning_dir, filename)
        try:
            shutil.copy2(self.current_midi_path, dest_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy MIDI file: {e}")
            return

        # 3. Prepare Data for Excel
        # Helper to convert numpy types to native python types
        def to_native(obj):
            if hasattr(obj, 'item'): # numpy types often have .item()
                return obj.item()
            return obj

        # Flatten data for Excel
        row = {
            "FileName": filename,
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "IsUserCorrected": correction_count > 0,
            "CorrectionCount": correction_count
        }
        
        # Add Ground Truth (Prefix GT_)
        for k, v in final_data.items():
            row[f"GT_{k}"] = v
            
        # Add AI Prediction (Prefix AI_)
        for k, v in final_data.items():
            # Retrieve from raw result to ensure we get what AI originally said
            raw_val = str(self.current_result.get(k, ""))
            row[f"AI_{k}"] = raw_val
            
        # Add Features (Prefix FEAT_)
        features = self.current_result.get('style_features', {})
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
            
            # Also update JSON (Legacy/Backup)
            self._save_json_backup(filename, final_data, correction_count)
            
            self.lbl_status.configure(text=f"Saved to Excel & {learning_dir}!", text_color="green")
            self.btn_learn.configure(state="disabled")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save Excel: {e}")

    def _save_json_backup(self, filename, final_data, correction_count):
        # Helper to convert numpy types to native python types
        def to_native(obj):
            if hasattr(obj, 'item'): 
                return obj.item()
            if isinstance(obj, dict):
                return {k: to_native(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [to_native(i) for i in obj]
            return obj
            
        with open(self.current_midi_path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()

        entry = {
            "filename": filename,
            "hash": file_hash,
            "ground_truth": final_data,
            # Ensure serialization by converting values to string
            "ai_raw_prediction": {k: str(self.current_result.get(k)) for k in final_data.keys()},
            "internal_features": to_native(self.current_result.get('style_features', {})),
            "corrections_made": correction_count > 0,
            "correction_count": correction_count
        }
        
        data = {}
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding='utf-8') as f:
                    data = json.load(f)
            except:
                data = {}
        
        data[filename] = entry
        
        with open(DATA_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    app = StyleTrainerApp()
    app.mainloop()
