import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtCore import Qt

# Add script dir to path (for module resolution)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.quick_editor_widget import QuickEditorWidget

class QuickEditorWindow(QMainWindow):
    def __init__(self, file_path=None):
        super().__init__()
        self.setWindowTitle("Quick MIDI Editor")
        self.resize(1000, 600)
        
        self.editor = QuickEditorWidget(file_path=file_path)
        self.setCentralWidget(self.editor)
        self.editor.saved.connect(self.on_save_complete)
        
        self.setAcceptDrops(True)
        
        # Shortcuts
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save)
        self.addAction(save_action)

    def save(self):
        self.editor.save_midi()

    def on_save_complete(self):
        # User requested: Do NOT close on save
        print("Save Complete.")
        # Optional: Flash window title or status?
        orig_title = self.windowTitle()
        self.setWindowTitle(orig_title + " [SAVED]")
        # Restore title after 1 sec? (Requires QTimer, skip for "Quick" simplicity or just leave it)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.mid') or file_path.lower().endswith('.midi'):
                self.editor.load_midi(file_path)
                self.setWindowTitle(f"Quick MIDI Editor - {os.path.basename(file_path)}")
                break

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    file_path = None
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        
    window = QuickEditorWindow(file_path)
    window.show()
    
    sys.exit(app.exec())
