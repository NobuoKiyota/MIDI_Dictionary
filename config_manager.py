from PySide6.QtCore import QSettings, QPoint, QSize
from PySide6.QtGui import QColor

class ConfigManager:
    def __init__(self):
        self.settings = QSettings("MyCompany", "MidiDictionary")
        
        # Default Colors for 12 pitch classes (C, C#, D...)
        # A nice starting palette (Rainbow-ish or Standard)
        self.default_colors = [
            "#FF0000",   # C  (Red)
            "#FF7F00",   # C#
            "#FFFF00",   # D  (Yellow)
            "#7FFF00",   # D#
            "#00FF00",   # E  (Green)
            "#00FF7F",   # F
            "#00FFFF",   # F# (Cyan)
            "#007FFF",   # G
            "#0000FF",   # G# (Blue)
            "#7F00FF",   # A
            "#FF00FF",   # A# (Magenta)
            "#FF007F"    # B
        ]

    def get_note_color(self, pitch_class):
        # pitch_class 0-11
        key = f"Display/Color_{pitch_class}"
        hex_color = self.settings.value(key, self.default_colors[pitch_class])
        return QColor(hex_color)

    def set_note_color(self, pitch_class, color):
        key = f"Display/Color_{pitch_class}"
        self.settings.setValue(key, color.name())

    def get_note_colors_all(self):
        return [self.get_note_color(i) for i in range(12)]

    def save_window_state(self, window):
        self.settings.setValue("Window/Geometry", window.saveGeometry())
        self.settings.setValue("Window/State", window.saveState())
        self.settings.setValue("Window/AlwaysOnTop", window.windowFlags() & Qt.WindowStaysOnTopHint > 0)

    def load_window_state(self, window):
        geom = self.settings.value("Window/Geometry")
        if geom:
            window.restoreGeometry(geom)
        state = self.settings.value("Window/State")
        if state:
            window.restoreState(state)
        
        # Always On Top is a flag, not part of saveState usually?
        # Actually saveState stores dock/toolbar stuff. Geometry stores pos/size.
        # We need custom generic flag.
        
        is_top = self.settings.value("Window/AlwaysOnTop", False)
        # Convert string 'true'/'false' if QSettings messed up, 
        # but usually PySide handles bool if saved as bool? 
        # QSettings INI format might correspond to string.
        
        return str(is_top).lower() == 'true'

from PySide6.QtCore import Qt
