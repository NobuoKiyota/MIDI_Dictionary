from PySide6.QtWidgets import QDialog, QFormLayout, QComboBox, QLineEdit, QDialogButtonBox, QLabel

class RegistrationDialog(QDialog):
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Register MIDI")
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
        def_inst = inferred.get("Instruments", "")
        if not def_inst: # Fallback to filename based logic if needed or just empty
             def_inst = "Drum" if "Rythem" in (self.data.get("filename", "") or "") else ""
        self.instruments_edit = QLineEdit(def_inst) 
        self.layout.addRow("Instruments:", self.instruments_edit)
        
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
        
        # 8. Group
        self.group_edit = QLineEdit("")
        self.layout.addRow("Group:", self.group_edit)
        
        # 9. Comment (Auto-generated)
        # Format: "Instruments_Chord_Bars_Beat_Groove_Style"
        # We have "CommentSuffix" from analysis.
        # We need to prepend Instruments/Category to make "Bass_Am7..."
        
        suffix = inferred.get("CommentSuffix", "")
        # Construct prefix
        # Use Category or Instruments? Request: "Bass_Am7..." -> Category usually.
        # But also "Epiano_Ds9..." -> Instruments?
        # Let's use Instruments if present, else Category.
        
        prefix = self.instruments_edit.text()
        if not prefix:
            prefix = self.category_combo.currentText()
            
        auto_comment = f"{prefix}_{suffix}" if suffix else ""
        
        self.comment_edit = QLineEdit(auto_comment)
        self.layout.addRow("Comment:", self.comment_edit)
        
        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addRow(self.buttons)

    def get_metadata(self):
        return {
            "FileName": self.name_edit.text(),
            "Root": self.root_combo.currentText(),
            "Category": self.category_combo.currentText(),
            "Instruments": self.instruments_edit.text(),
            "TimeSignature": self.ts_edit.text(),
            "Bar": self.bar_edit.text(),
            "Chord": self.chord_combo.currentText(),
            "Group": self.group_edit.text(),
            "Comment": self.comment_edit.text()
        }
