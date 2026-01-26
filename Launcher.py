import sys
import os
import subprocess
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QLabel, QFrame, QMessageBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon

class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIDI Dictionary Suite")
        self.resize(400, 500)
        
        # Styles
        self.setStyleSheet("""
            QMainWindow { background-color: #263238; }
            QPushButton {
                background-color: #37474f;
                color: #eceff1;
                border: 1px solid #546e7a;
                border-radius: 8px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #455a64;
                border: 1px solid #78909c;
            }
            QPushButton:pressed {
                background-color: #263238;
            }
            QLabel { color: #cfd8dc; }
        """)
        
        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 40, 30, 40)
        
        # Header
        title = QLabel("MIDI Dictionary Suite")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Select Tool to Launch")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #90a4ae; font-size: 14px;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Buttons
        self.btn_main = self.create_button("🎵  MIDI Dictionary", "Library Manager & Player")
        self.btn_main.clicked.connect(lambda: self.launch("Scripts/main.py"))
        layout.addWidget(self.btn_main)
        
        self.btn_gen = self.create_button("🎹  Ensemble Generator", "Create Patterns from Bass MIDI")
        self.btn_gen.clicked.connect(lambda: self.launch("EnsembleGenerator/midi_ensemble_gui.py"))
        layout.addWidget(self.btn_gen)
        
        self.btn_edit = self.create_button("✏️  Quick Editor", "Fast Edit & Overwrite")
        self.btn_edit.clicked.connect(lambda: self.launch("Scripts/quick_editor.py"))
        layout.addWidget(self.btn_edit)
        
        layout.addStretch()
        
        footer = QLabel("v2.0 - Unified System")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #546e7a; font-size: 11px;")
        layout.addWidget(footer)

    def create_button(self, text, subtext):
        btn = QPushButton()
        # Custom layout inside button using text? 
        # Easier to just use multiline text
        btn.setText(f"{text}\n   {subtext}")
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 20px;
            }
        """)
        return btn

    def launch(self, script_rel_path):
        try:
            # Resolve path
            base_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(base_dir, script_rel_path)
            
            # Run
            subprocess.Popen([sys.executable, script_path], cwd=base_dir)
            
            # Optional: Hide Launcher? No, keep it open as hub.
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LauncherWindow()
    win.show()
    sys.exit(app.exec())
