from PySide6.QtCore import QSettings, QPoint, QSize
from PySide6.QtGui import QColor

class ConfigManager:
    def __init__(self):
        self.settings = QSettings("MyCompany", "MidiDictionary")
        
        # Default Colors for 12 pitch classes (C, C#, D...)
        # A nice starting palette (Rainbow-ish or Standard)
        self.default_colors = [
            "#FF0000",   # C  (Red)
            "#59FF00",   # C#
            "#FFD900",   # D  (Yellow)
            "#00CCF8",   # D#
            "#FF4800",   # E  (Green)
            "#FFF700",   # F
            "#00AEFF",   # F# (Cyan)
            "#FF9D00",   # G
            "#62FF00",   # G# (Blue)
            "#FF00E6",   # A
            "#91FF00",   # A# (Magenta)
            "#6600FF"    # B
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
