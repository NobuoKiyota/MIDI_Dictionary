from PySide6.QtWidgets import QDialog, QFormLayout, QComboBox, QLineEdit, QDialogButtonBox, QLabel
from instrument_config import INSTRUMENT_MAP

class RegistrationDialog(QDialog):
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Register MIDI")
        self.resize(400, 360)
        self.data = initial_data or {}
        
        self.layout = QFormLayout(self)
        
        inferred = self.data.get("inferred_meta", {})
        
        # 1. File Name
        self.name_edit = QLineEdit(self.data.get("filename", ""))
        self.layout.addRow("File Name:", self.name_edit)
        
        # 2. Root
        self.root_combo = QComboBox()
        self.root_combo.addItems(["No"] + ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])
        root_val = inferred.get("Root", self.data.get("root", "No"))
        self.root_combo.setCurrentText(root_val if root_val else "No")
        self.layout.addRow("Root:", self.root_combo)
        
        # 2b. Scale
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["Major", "Minor", "Dorian", "Mixolydian", "Lydian", "Phrygian", "Locrian", "Unknown"])
        scale_val = inferred.get("Scale", "Major")
        self.scale_combo.setCurrentText(scale_val if scale_val else "Major")
        self.layout.addRow("Scale:", self.scale_combo)
        
        # 3. Category (Expanded)
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Rythem", "Bass", "Chord", "Arp", "Melody",
            "Fill", "FX", "Perc", "Pad", "Lead"
        ])
        cat_val = inferred.get("Category", "Rythem")
        self.category_combo.setCurrentText(cat_val if cat_val else "Rythem")
        self.layout.addRow("Category:", self.category_combo)
        
        # 4. Instruments
        # Use ComboBox with GM Instruments
        self.instruments_combo = QComboBox()
        # Sort keys for display
        inst_list = sorted(INSTRUMENT_MAP.keys())
        self.instruments_combo.addItems(inst_list)
        
        # Default selection logic
        def_inst = self.data.get("filename", "")
        # Try to find a match in filename or meta?
        # User said "Instrument to be selectable".
        # If inferred meta has something useful, use it.
        # Otherwise, default to Piano? Or try to fuzzy match filename?
        
        # Let's try to match inferred "Category" or just Piano
        # Or if "Instruments" was passed in data (from file?) -> data["filename"] is usually just filename.
        # Let's default to "Acoustic Grand Piano" (0)
        self.instruments_combo.setCurrentText("Acoustic Grand Piano")
        
        # If there is a hint in filename (e.g. "bass"), try to select it
        lower_name = def_inst.lower()
        for name in inst_list:
            if name.lower() in lower_name:
                self.instruments_combo.setCurrentText(name)
                break
                
        self.layout.addRow("Instruments:", self.instruments_combo)
        
        # 5. Time Signature
        self.ts_edit = QLineEdit(self.data.get("time_signature", "4/4")) 
        self.layout.addRow("Time Signature:", self.ts_edit)
        
        # 6. Bar Length
        self.bar_edit = QLineEdit(str(self.data.get("duration_bars", "4")))
        self.layout.addRow("Bar Length:", self.bar_edit)
        
        # 7. Chord
        self.chord_combo = QComboBox()
        # Add broad list, but we can also set custom text if needed or just select nearest
        self.chord_combo.addItems([
            "None", 
            "Power", "Major", "minor", "M7", "m7", "7th",
            "sus4", "aug", "dim", "MajorTension", "MinorTension"
        ])
        # Map specific chord string to general category if needed, or just standard names
        chord_val = inferred.get("Chord", "None")
        # Try to match fuzzy or exact
        found_idx = self.chord_combo.findText(chord_val) # exact match
        if found_idx >= 0:
            self.chord_combo.setCurrentIndex(found_idx)
        else:
            # If not exact match (e.g. CmM7), maybe default to "MinorTension"?
            # For now just set text if editable? Combo is typically fixed list here.
            # Let's try to map common ones.
            if "m" in chord_val:
                self.chord_combo.setCurrentText("minor")
            elif "7" in chord_val:
                self.chord_combo.setCurrentText("7th")
            else:
                 self.chord_combo.setCurrentText("None")
        self.layout.addRow("Chord:", self.chord_combo)
        
        # 7b. Groove (Artic)
        self.groove_edit = QLineEdit(inferred.get("Groove", ""))
        self.groove_edit.setPlaceholderText("Straight if empty")
        self.layout.addRow("Groove:", self.groove_edit)

        # 7c. Style
        self.style_edit = QLineEdit(inferred.get("Style", ""))
        self.layout.addRow("Style:", self.style_edit)
        
        # 8. Group
        self.group_edit = QLineEdit("")
        self.layout.addRow("Group:", self.group_edit)
        
        # 9. Comment
        self.comment_edit = QLineEdit("")
        self.layout.addRow("Comment:", self.comment_edit)
        
        # Auto-Generate Filename from Metadata
        # Format: "Instruments_Chord_Bars_Beat_Groove_Style" (based on suffix)
        suffix = inferred.get("CommentSuffix", "")
        prefix = self.instruments_combo.currentText()
        if not prefix:
            prefix = self.category_combo.currentText()
            
        auto_name = f"{prefix}_{suffix}" if suffix else prefix
        self.name_edit.setText(auto_name)
        
        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

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
