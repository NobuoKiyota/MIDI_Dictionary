from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QPushButton, QHBoxLayout, QLabel, QFrame
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QDrag, QFont
from PySide6.QtCore import Qt, Signal, QMimeData, QSize, QUrl, QPoint
import os

class PianoRollCanvas(QWidget):
    hoverChanged = Signal(str) # New Signal

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.setMouseTracking(True) # For overlay
        
        self.notes = []
        self.view_page_start = 0.0 
        self.view_duration = 0.0
        self.tempo = 120.0
        self.time_signature_num = 4
        
        self.key_height = 20 # Can be zoomed
        self.min_pitch = 0
        self.max_pitch = 127
        
        # Grid Colors
        self.grid_col_octave = QColor(80, 80, 80) # Strong
        self.grid_col_bar = QColor(60, 60, 60)    # Medium
        self.grid_col_beat = QColor(30, 30, 30)   # Light
        self.bg_color = QColor(10, 10, 10)
        
        # Mouse Info
        self.mouse_pos = None
        self.overlay_info = ""

        # Sizing
        self.setMinimumWidth(600)
        self.update_height()

    def update_height(self):
        self.setMinimumHeight(128 * self.key_height)

    def set_data(self, notes, tempo, ts_num, page_start_beat):
        self.notes = notes
        self.tempo = tempo
        self.time_signature_num = ts_num
        
        beats_per_bar = self.time_signature_num
        seconds_per_beat = 60.0 / self.tempo
        
        self.view_page_start = page_start_beat * seconds_per_beat
        self.view_duration = 2 * beats_per_bar * seconds_per_beat
        
        self.update()

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.pos()
        
        # Calc Time
        x = event.pos().x()
        w = self.width()
        
        info_text = ""
        if w > 0 and self.view_duration > 0:
            rel_t = (x / w) * self.view_duration
            abs_t = self.view_page_start + rel_t
            
            seconds_per_beat = 60.0 / self.tempo
            total_beats = abs_t / seconds_per_beat
            
            bar = int(total_beats / self.time_signature_num) + 1
            beat_in_bar = int(total_beats % self.time_signature_num) + 1
            
            info_text = f"Bar {bar} : Beat {beat_in_bar}"
        
        self.hoverChanged.emit(info_text)
        self.update()

    def leaveEvent(self, event):
        self.mouse_pos = None
        self.hoverChanged.emit("")
        self.update()

    def update_overlay_info(self):
        if not self.mouse_pos: return
        
        # Y -> Pitch
        y = self.mouse_pos.y()
        # Pitch 127 is 0.
        pitch = 127 - int(y / self.key_height)
        if pitch < 0: pitch = 0
        if pitch > 127: pitch = 127
        
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        note_name = f"{note_names[pitch % 12]}{pitch // 12 - 1}"
        
        # X -> Time
        x = self.mouse_pos.x()
        w = self.width()
        if w == 0: return
        
        if self.view_duration > 0:
            rel_t = (x / w) * self.view_duration
            abs_t = self.view_page_start + rel_t
            
            seconds_per_beat = 60.0 / self.tempo
            total_beats = abs_t / seconds_per_beat
            
            bar = int(total_beats / self.time_signature_num) + 1
            remainder = total_beats % self.time_signature_num
            beat = int(remainder) + 1
            tick = int((remainder - int(remainder)) * 100) # Simple decimal tick
            
            self.overlay_info = f"{note_name} | {bar}:{beat}:{tick}"
        else:
            self.overlay_info = note_name

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.bg_color)
        
        w = self.width()
        h = self.height()
        
        # --- Time Mapping ---
        def time_to_x(t):
            if self.view_duration <= 0: return 0
            rel_t = t - self.view_page_start
            return (rel_t / self.view_duration) * w

        # --- Draw Horiz Grid (Pitches) ---
        # Draw Octave Lines
        font = QFont() # Default font
        font.setPixelSize(10)
        painter.setFont(font)
        
        for p in range(128):
            y = (127 - p) * self.key_height
            
            is_c = (p % 12 == 0)
            if is_c:
                painter.setPen(QPen(self.grid_col_octave, 1, Qt.SolidLine))
                painter.drawLine(0, y + self.key_height, w, y + self.key_height) # Draw line at bottom of C (between B and C)? Or top?
                # Usually Octave line is between B and C. 
                # C is p%12==0. B is p%12==11.
                # Let's draw line at TOP of C (between C and C#? No).
                # Line between B(prev octave) and C(this octave).
                # Y for C is lower (higher value) than B. 
                # painter y=0 is top. 127 is top. 
                # wait, y = (127-p)*h. p=127 -> y=0. p=0 -> y=max.
                # So high pitch is top.
                # Octave line between B3 and C4. 
                # C4=60. B3=59.
                # Draw grid line at Bottom of C? (y + height).
                pass
            else:
                # Faint line between keys? Optional.
                painter.setPen(QPen(QColor(20, 20, 20), 1))
                painter.drawLine(0, y, w, y)

        # --- Draw Vert Grid (Time) ---
        beats_per_bar = self.time_signature_num
        seconds_per_beat = 60.0 / self.tempo
        total_beats_in_view = 2 * beats_per_bar
        
        start_beat_global = int(self.view_page_start / seconds_per_beat) 

        for i in range(total_beats_in_view + 1):
            # Same logic as before but new colors
            bx = (i / total_beats_in_view) * w
            is_bar = (i % beats_per_bar == 0)
            
            if is_bar:
                painter.setPen(QPen(self.grid_col_bar, 1, Qt.SolidLine))
            else:
                painter.setPen(QPen(self.grid_col_beat, 1, Qt.DashLine)) # 点線 (Dash/Dot)
                
            painter.drawLine(bx, 0, bx, h)

        # --- Draw Notes ---
        if self.notes:
            for note in self.notes:
                start = note['start']
                end = note['end']
                
                if end < self.view_page_start: continue
                if start > (self.view_page_start + self.view_duration): continue
                
                pitch = note['pitch']
                y = (127 - pitch) * self.key_height
                
                x1 = time_to_x(start)
                x2 = time_to_x(end)
                rect_w = max(1, x2 - x1)
                
                if x1 < 0: 
                    rect_w += x1
                    x1 = 0
                if (x1 + rect_w) > w: 
                    rect_w = w - x1

                vel = note['velocity']
                
                # Color from Config
                pitch_class = pitch % 12
                base_color = self.config.get_note_color(pitch_class)
                
                # Alpha formula
                alpha = int((vel / 127.0) ** 3 * 255)
                # Apply alpha to base color
                fill_color = QColor(base_color)
                fill_color.setAlpha(alpha)
                
                painter.fillRect(x1, y, rect_w, self.key_height, fill_color)
                
                # Border
                if alpha > 50:
                    border_col = QColor(base_color)
                    border_col.setAlpha(min(255, alpha + 50))
                    painter.setPen(QPen(border_col, 1))
                    painter.drawRect(x1, y, rect_w, self.key_height)

        # --- Overlay Crosshair ---
        if self.mouse_pos:
            # painter.setPen(QPen(Qt.white, 1)) # Removed text drawing
            # Just draw text at top right corner fixed, per request?
            # "右上あたりに表示"
            # painter.drawText(w - 150, 20, self.overlay_info) # Removed
            
            # Optional: Crosshair lines?
            painter.setPen(QPen(QColor(100, 100, 100, 100), 1, Qt.DotLine))
            painter.drawLine(0, self.mouse_pos.y(), w, self.mouse_pos.y())
            painter.drawLine(self.mouse_pos.x(), 0, self.mouse_pos.x(), h)


class DraggableButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.file_path = None
        self.drag_start_pos = QPoint()

    def set_file_path(self, path):
        if path:
            self.file_path = os.path.abspath(path)
            print(f"[DEBUG] DraggableButton Path Set (Abs): {self.file_path}")
        else:
            self.file_path = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.file_path:
            super().mouseMoveEvent(event)
            return
        if not (event.buttons() & Qt.LeftButton):
            return
        if (event.pos() - self.drag_start_pos).manhattanLength() < 10: 
            return

        print(f"[DEBUG] Drag attempting. File: {self.file_path}")
        drag = QDrag(self)
        mime = QMimeData()
        url = QUrl.fromLocalFile(self.file_path)
        print(f"[DEBUG] URL created: {url.toString()}")
        mime.setUrls([url])
        drag.setMimeData(mime)
        print("[DEBUG] Executing Drag...")
        result = drag.exec(Qt.CopyAction)
        print(f"[DEBUG] Drag finished with result: {result}")

class PianoRollWidget(QWidget):
    fileDropped = Signal(str)

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.setAcceptDrops(True)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Controls
        ctrl_layout = QHBoxLayout()
        
        # Page Toggle
        self.page_btn = QPushButton("Page 1/2") # Toggle
        self.page_btn.setCheckable(True)
        self.page_btn.clicked.connect(self.toggle_page)
        self.page_btn.setStyleSheet("""
            QPushButton { background-color: #444; color: white; border: 1px solid #666; padding: 5px; }
            QPushButton:checked { background-color: #3d5afe; border: 1px solid #5d7aff; }
        """)
        
        # Zoom Buttons (since slider might be overkill, lets use +/-)
        self.zoom_in_btn = QPushButton("+")
        self.zoom_out_btn = QPushButton("-")
        self.zoom_in_btn.setFixedSize(30, 30)
        self.zoom_out_btn.setFixedSize(30, 30)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        
        # DRAW MIDI
        self.draw_btn = DraggableButton("DRAW MIDI")
        self.draw_btn.setStyleSheet("background-color: #d84315; color: white; font-weight: bold; padding: 5px;")
        
        ctrl_layout.addWidget(QLabel("Zoom:"))
        ctrl_layout.addWidget(self.zoom_out_btn)
        ctrl_layout.addWidget(self.zoom_in_btn)
        ctrl_layout.addSpacing(20)
        ctrl_layout.addWidget(self.page_btn)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.draw_btn)
        
        self.layout.addLayout(ctrl_layout)

        # Scroll
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.canvas = PianoRollCanvas(self.config)
        self.scroll.setWidget(self.canvas)
        self.layout.addWidget(self.scroll)
        
        # Info Overlay Label
        self.info_label = QLabel(self)
        self.info_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.info_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #FFFFFF;
            background-color: rgba(0, 0, 0, 150);
            padding: 4px;
            border-radius: 4px;
        """)
        self.info_label.hide()

        # Connect canvas signal
        self.canvas.hoverChanged.connect(self.update_info_label)

        # State
        self.current_page = 0 # 0=PartA(1-2), 1=PartB(3-4)
        self.notes = []
        self.tempo = 120
        self.ts_num = 4
        
        # Initial key height for 3 octaves in ~270px
        # 270 / 36 = 7.5. Let's use 10px, so 3 octaves = 360px.
        # User can scroll.
        self.canvas.key_height = 12 
        self.canvas.update_height()
        
        # Default scroll to C3 (pitch 48)
        # Pitch 48 Y = (127 - 48) * 12 = 79 * 12 = 948
        # We want this Y to be at the bottom of the scroll view.
        # So scroll_value = 948 - viewport_height
        # Defer this until shown? 
        # We can set it initial value.
        self.scroll.verticalScrollBar().setValue(500) 

    def update_info_label(self, text):
        if text:
            self.info_label.setText(text)
            self.info_label.adjustSize()
            self.info_label.show()
            self.position_info_label()
        else:
            self.info_label.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_info_label()
        
    def position_info_label(self):
        if self.info_label.isVisible():
            # Position at top-right of the scroll area's viewport, with some margin
            # Assuming control layout height is roughly 40-50px
            margin = 10
            x = self.width() - self.info_label.width() - margin
            y = self.layout.itemAt(0).geometry().height() + margin # Below control layout
            self.info_label.move(x, y)

    def set_notes(self, notes_data, tempo=120, ts_num=4, file_path=None):
        self.notes = notes_data
        self.tempo = tempo
        self.ts_num = ts_num
        self.current_page = 0
        self.page_btn.setChecked(False)
        self.page_btn.setText("Bars 1-2")
        
        if file_path:
            self.draw_btn.set_file_path(file_path)
            self.draw_btn.setEnabled(True)
        else:
            self.draw_btn.setEnabled(False)
            
        self.update_canvas()
        
        # User requested: "If list selected, fly to default"
        # "Default" roughly implies centering on the notes or the default C3 view.
        # "画面中央C3を下限として...リストが選択されたらデフォルトに飛ぶように"
        # "With screen center C3 as lower limit... fly to default when list selected"
        # This implies resetting the view anchor.
        
        # Let's try to center on the notes if they exist, but respect C3 as "default base".
        self.auto_scroll_focus()

    def update_canvas(self):
        beats_per_bar = self.ts_num
        start_beat = self.current_page * 2 * beats_per_bar
        self.canvas.set_data(self.notes, self.tempo, self.ts_num, start_beat)
    
    def toggle_page(self):
        if self.page_btn.isChecked():
            self.current_page = 1
            self.page_btn.setText("Bars 3-4")
        else:
            self.current_page = 0
            self.page_btn.setText("Bars 1-2")
        self.update_canvas()

    def zoom_in(self):
        self._set_zoom(self.canvas.key_height + 2)

    def zoom_out(self):
        self._set_zoom(self.canvas.key_height - 2)

    def _set_zoom(self, target_h):
        old_h = self.canvas.key_height
        new_h = max(4, min(50, target_h))
        
        if old_h == new_h: return

        # 1. Calc current center pitch
        scroll_bar = self.scroll.verticalScrollBar()
        current_val = scroll_bar.value()
        viewport_h = self.scroll.viewport().height()
        
        center_y = current_val + (viewport_h / 2)
        # pitch at center Y. Y = (127-p)*h  => p = 127 - (Y/h)
        center_pitch = 127 - (center_y / old_h)
        
        # 2. Update Height
        self.canvas.key_height = new_h
        self.canvas.update_height()
        
        # 3. Restore Scroll to keep center_pitch at center
        # New Y for center pitch
        new_dist_from_top = (127 - center_pitch) * new_h
        new_scroll_val = int(new_dist_from_top - (viewport_h / 2))
        
        scroll_bar.setValue(new_scroll_val)
        self.canvas.update()

    def auto_scroll_focus(self):
        # Default C3=48. 
        # Calculate Y for Pitch 48 (C3)
        # We want C3 to be near the bottom of the view (lower limit)
        # or Center? "Center C3 as lower limit" -> C3 is center? or C3 is lower limit of center?
        # Let's target Pitch 54 (Center of 3 octaves 48-84) to be Center of screen.
        
        target_pitch = 60 # C4 (Middle C)
        
        if self.notes:
            pitches = [n['pitch'] for n in self.notes]
            if pitches:
                target_pitch = sum(pitches) / len(pitches)
        
        view_h = self.scroll.height()
        
        # Y = (127 - pitch) * h
        target_y = (127 - target_pitch) * self.canvas.key_height
        
        # Center target_y
        scroll_to = target_y - (view_h / 2)
        
        self.scroll.verticalScrollBar().setValue(int(scroll_to))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.mid') or file_path.lower().endswith('.midi'):
                self.fileDropped.emit(file_path)
                break
    
    def refresh_colors(self):
        self.canvas.update()
