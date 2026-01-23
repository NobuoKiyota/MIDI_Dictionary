from PySide6.QtWidgets import QDialog, QFormLayout, QComboBox, QLineEdit, QDialogButtonBox, QLabel, QVBoxLayout, QGridLayout
import ui_constants as C

class RegistrationDialog(QDialog):
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Register MIDI")
        self.resize(400, 360)
        self.data = initial_data or {}
        
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Register MIDI & Train AI")
        self.resize(650, 600)
        self.data = initial_data or {}
        
        # Main Layout
        main_layout = QVBoxLayout(self)
        
        
        grid = QGridLayout()
        grid.setSpacing(10)
        main_layout.addLayout(grid)
        
        # Headers
        headers = ["Parameter", "AI Prediction", "User Correction (Entry/Edit)"]
        colors = ["white", "#4da6ff", "#ff9933"] # StyleTrainer colors
        
        for col, (text, color) in enumerate(zip(headers, colors)):
            lbl = QLabel(text)
            lbl.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {color};")
            grid.addWidget(lbl, 0, col)
            
        self.widgets = {} # Store user widgets
        inferred = self.data.get("inferred_meta", {})
        
        # Helper to add row
        row_idx = 1
        def add_row(label, ai_val, user_widget):
            nonlocal row_idx
            # Label
            grid.addWidget(QLabel(label), row_idx, 0)
            
            # AI Label (Readonly Entry style)
            ai_edit = QLineEdit(str(ai_val))
            ai_edit.setReadOnly(True)
            ai_edit.setStyleSheet("color: #aaa; background-color: #2b2b2b; border: 1px solid #444;")
            grid.addWidget(ai_edit, row_idx, 1)
            
            # User Widget
            grid.addWidget(user_widget, row_idx, 2)
            row_idx += 1

        # --- Fields ---
        
        # 1. File Name
        # Logic: Combined AI Proposal + Original
        # AI Col: The Pure "Auto Name"
        # User Col: The Combined Text (for editing)
        original_name = self.data.get("filename", "")
        
        # Re-calc auto name for display
        style_val = inferred.get("Style", "")
        inst_val = inferred.get("Instruments", "")
        # Note: Instrument might vary if user changes combobox? 
        # But here we show INITIAL AI thought.
        
        # We need to construct the AI name based on INFERRED RAW data effectively.
        # inferred dict has keys from midi_utils mapping.
        
        parts = []
        if style_val: parts.append(style_val)
        parts.append(inst_val if inst_val else "Unknown")
        suffix = inferred.get("CommentSuffix", "")
        if suffix: parts.append(suffix)
        ai_filename = "_".join(parts)
        
        self.name_edit = QLineEdit()
        # User Request: Original Name Only (AI Name is in column 1)
        self.name_edit.setText(original_name)
             
        add_row("File Name", ai_filename, self.name_edit)
        
        # 2. Key
        self.root_combo = QComboBox()
        self.root_combo.addItems(C.KEY_LIST)
        root_val = inferred.get("Root", "-") # Current best guess
        if root_val == "No": root_val = "-"
        if "#" in str(root_val): root_val = str(root_val).replace("#", "s")
        self.root_combo.setCurrentText(root_val if root_val in C.KEY_LIST else "-")
        
        add_row("Key (Root)", inferred.get("Root", "-"), self.root_combo)
        
        # 3. Scale
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["Major", "Minor", "Dorian", "Mixolydian", "Lydian", "Phrygian", "Locrian", "Unknown"])
        scale_val = inferred.get("Scale", "Major")
        self.scale_combo.setCurrentText(scale_val)
        
        add_row("Scale", scale_val, self.scale_combo)
        
        # 4. Category
        self.category_combo = QComboBox()
        self.category_combo.addItems(C.CATEGORY_LIST)
        cat_val = inferred.get("Category", "Rythem")
        self.category_combo.setCurrentText(cat_val if cat_val in C.CATEGORY_LIST else "Rythem")
        
        add_row("Category", cat_val, self.category_combo)
        
        # 5. Instruments
        self.instruments_combo = QComboBox()
        self.instruments_combo.addItems(C.INSTRUMENT_LIST)
        
        # Selection Logic (Pre-filled)
        def_inst = original_name
        inferred_inst = inferred.get("Instruments", "")
        
        target_inst = "Acoustic Grand Piano"
        if inferred_inst and inferred_inst in C.INSTRUMENT_LIST:
            target_inst = inferred_inst
        elif not inferred_inst:
             for name in C.INSTRUMENT_LIST:
                if name.lower() in def_inst.lower():
                    target_inst = name
                    break
        self.instruments_combo.setCurrentText(target_inst)
        
        add_row("Instruments", inferred_inst, self.instruments_combo)
        
        # 6. Time Sig
        self.ts_edit = QLineEdit(self.data.get("time_signature", "4/4"))
        add_row("Time Signature", inferred.get("TimeSignature", "4/4"), self.ts_edit)
        
        # 7. Bar
        self.bar_edit = QLineEdit(str(self.data.get("duration_bars", "4")))
        add_row("Bar Length", inferred.get("DurationBars", "4"), self.bar_edit)
        
        # 8. Chord
        self.chord_combo = QComboBox()
        self.chord_combo.addItems(C.CHORD_LIST)
        chord_val = inferred.get("Chord", "None")
        found_idx = self.chord_combo.findText(chord_val)
        if found_idx >= 0: self.chord_combo.setCurrentIndex(found_idx)
        else:
            if "m" in chord_val: self.chord_combo.setCurrentText("minor")
            elif "7" in chord_val: self.chord_combo.setCurrentText("7th")
            else: self.chord_combo.setCurrentText("None")
            
        add_row("Chord", chord_val, self.chord_combo)
        
        # 9. Groove
        self.groove_edit = QLineEdit(inferred.get("Groove", ""))
        self.groove_edit.setPlaceholderText("Straight if empty")
        add_row("Groove", inferred.get("Groove", "Straight"), self.groove_edit)
        
        # 10. Style
        self.style_edit = QLineEdit(inferred.get("Style", ""))
        add_row("Style", inferred.get("Style", ""), self.style_edit)
        
        # 11. Group (No AI usually)
        self.group_edit = QLineEdit("")
        add_row("Group", "-", self.group_edit)
        
        # 12. Comment
        self.comment_edit = QLineEdit("")
        add_row("Comment", "-", self.comment_edit)
        
        main_layout.addStretch()
        
        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        main_layout.addWidget(self.buttons)

    def get_metadata(self):
        inferred = self.data.get("inferred_meta", {})
        return {
            "FileName": self.name_edit.text(),
            "Root": self.root_combo.currentText(),
            "Scale": self.scale_combo.currentText(),
            "Category": self.category_combo.currentText(),
            "Instruments": self.instruments_combo.currentText(),
            "TimeSignature": self.ts_edit.text(),
            "Bar": self.bar_edit.text(),
            "Chord": self.chord_combo.currentText(),
            "Groove": self.groove_edit.text(),
            "Style": self.style_edit.text(),
            "Group": self.group_edit.text(),
            "Comment": self.comment_edit.text(),
            "_raw_ai_result": inferred.get("_raw_ai_result", {})
        }
