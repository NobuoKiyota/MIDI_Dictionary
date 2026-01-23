from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QColorDialog, QGridLayout
from PySide6.QtGui import QColor

class ColorConfigDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Note Color Settings")
        self.config = config_manager
        self.resize(300, 400)
        
        layout = QVBoxLayout(self)
        
        grid = QGridLayout()
        self.buttons = []
        
        names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        
        for i in range(12):
            lbl = QLabel(names[i])
            btn = QPushButton()
            btn.setFixedSize(50, 30)
            
            # Helper for closure
            def make_handler(idx, b):
                return lambda: self.pick_color(idx, b)
            
            btn.clicked.connect(make_handler(i, btn))
            
            grid.addWidget(lbl, i, 0)
            grid.addWidget(btn, i, 1)
            self.buttons.append(btn)
        
        layout.addLayout(grid)
        
        # Load current
        self.update_buttons()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
    def update_buttons(self):
        colors = self.config.get_note_colors_all()
        for i, col in enumerate(colors):
            self.buttons[i].setStyleSheet(f"background-color: {col.name()}; border: 1px solid #555;")

    def pick_color(self, idx, btn):
        current = self.config.get_note_color(idx)
        new_col = QColorDialog.getColor(current, self, "Select Color")
        if new_col.isValid():
            self.config.set_note_color(idx, new_col)
            self.update_buttons()
