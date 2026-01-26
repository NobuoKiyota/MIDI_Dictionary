import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, 
                             QGraphicsRectItem, QGraphicsItem, QFrame)
from PySide6.QtGui import QBrush, QPen, QColor, QPainter, QCursor, QAction, QKeySequence
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
import pretty_midi

# Constants
KEY_HEIGHT = 16
PIXELS_PER_SEC = 200 # Horizontal Zoom
NOTE_COLOR = QColor("#4caf50")
NOTE_SELECTED_COLOR = QColor("#8bc34a")
BG_COLOR = QColor("#1e1e1e")
GRID_COLOR = QColor("#333333")

class NoteItem(QGraphicsRectItem):
    def __init__(self, note_obj, pixels_per_sec, key_height):
        # Y = (127 - pitch) * H
        pitch = note_obj.pitch
        start = note_obj.start
        end = note_obj.end
        duration = end - start
        
        x = start * pixels_per_sec
        y = (127 - pitch) * key_height
        w = duration * pixels_per_sec
        h = key_height
        
        super().__init__(0, 0, w, h)
        self.setPos(x, y)
        
        self.setBrush(QBrush(NOTE_COLOR))
        self.setPen(QPen(Qt.NoPen))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        self.pixels_per_sec = pixels_per_sec
        self.key_height = key_height
        self.original_velocity = note_obj.velocity
        
        self.is_resizing = False
        self.resize_margin = 10 # Pixels from right edge

    def hoverMoveEvent(self, event):
        # Change cursor on right edge
        if event.pos().x() > self.rect().width() - self.resize_margin:
            self.setCursor(Qt.SizeHorCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if event.pos().x() > self.rect().width() - self.resize_margin:
                self.is_resizing = True
            else:
                self.is_resizing = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_resizing:
            # Resize Logic
            new_w = event.pos().x()
            if new_w < 5: new_w = 5 # Minimum width
            self.setRect(0, 0, new_w, self.rect().height())
        else:
            # Move Logic (Snap Y to grid, Snap X is unnecessary for "Quick" feel unless grid is implemented)
            super().mouseMoveEvent(event)
            # Custom Snap Y
            y = self.y()
            snapped_y = round(y / self.key_height) * self.key_height
            self.setY(snapped_y)
            
            # Snap X (Optional: to nearest 10px? No, free)
            if self.x() < 0: self.setX(0)

    def mouseReleaseEvent(self, event):
        self.is_resizing = False
        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            if value:
                self.setBrush(QBrush(NOTE_SELECTED_COLOR))
            else:
                self.setBrush(QBrush(NOTE_COLOR))
        return super().itemChange(change, value)
    
    def get_data(self):
        # Convert Rect back to MIDI data
        pitch = 127 - int(round(self.y() / self.key_height))
        pitch = max(0, min(127, pitch))
        
        start = self.x() / self.pixels_per_sec
        duration = self.rect().width() / self.pixels_per_sec
        end = start + duration
        
        return pretty_midi.Note(
            velocity=self.original_velocity,
            pitch=pitch,
            start=start,
            end=end
        )

    def update_geometry_zoom(self, new_pixels_per_sec, new_key_height):
        # 1. Recover current abstract time
        current_start = self.x() / self.pixels_per_sec
        current_dur = self.rect().width() / self.pixels_per_sec
        
        # 2. Update params
        self.pixels_per_sec = new_pixels_per_sec
        self.key_height = new_key_height
        
        # 3. Recalc Geometry
        new_x = current_start * self.pixels_per_sec
        new_w = current_dur * self.pixels_per_sec
        
        # Y is unchanged usually unless h changes
        new_y = self.y() # Assuming KeyHeight unchanged
        
        self.setRect(0, 0, new_w, self.key_height)
        self.setPos(new_x, new_y)

class QuickEditorWidget(QWidget):
    saved = Signal() # Emitted on successful save
    
    def __init__(self, file_path=None, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.file_path = file_path
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        
        # Scene & View
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QBrush(BG_COLOR))
        
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        from PySide6.QtWidgets import QSizePolicy
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.layout.addWidget(self.view)
        
        self.pm = None
        
        # If file provided, load
        if self.file_path:
            self.load_midi(self.file_path)

        # Draw Grid (Basic)
        self.draw_grid()

    def draw_grid(self):
        # Just simple horizontal lines for pitches?
        # Drawing infinite grid in Scene is expensive if scene is huge.
        # Only draw visible area? Or use `drawBackground` in Scene subclass.
        # For "Quick" prototype, let's just make scene big enough and add lines.
        w = 10000 
        h = 128 * KEY_HEIGHT
        self.scene.setSceneRect(0, 0, w, h)
        
        pen = QPen(GRID_COLOR)
        # Horiz lines
        for i in range(128):
            y = i * KEY_HEIGHT
            self.scene.addLine(0, y, w, y, pen)
            
    def load_midi(self, path):
        try:
            print(f"Loading MIDI: {path}")
            self.pm = pretty_midi.PrettyMIDI(path)
            self.file_path = path
            self.scene.clear()
            self.draw_grid()
            
            note_items = []
            
            # Add Notes
            for i, instrument in enumerate(self.pm.instruments):
                print(f"Instrument {i}: is_drum={instrument.is_drum}, notes={len(instrument.notes)}")
                if instrument.is_drum: continue
                for note in instrument.notes:
                    item = NoteItem(note, PIXELS_PER_SEC, KEY_HEIGHT)
                    self.scene.addItem(item)
                    note_items.append(item)
                    
            print(f"Added {len(note_items)} note items.")

            # Auto Scroll
            if note_items:
                # Calculate bounding rect of just notes
                x_min = min(item.x() for item in note_items)
                x_max = max(item.x() + item.rect().width() for item in note_items)
                y_min = min(item.y() for item in note_items)
                y_max = max(item.y() + item.rect().height() for item in note_items)
                
                center_x = (x_min + x_max) / 2
                center_y = (y_min + y_max) / 2
                
                print(f"Focusing on Center: {center_x}, {center_y}")
                self.view.centerOn(center_x, center_y)
            else:
                print("No notes found to display.")
            
            # Request Parent Title Update if possible
            if self.parent():
                try:
                    self.parent().setWindowTitle(f"Quick MIDI Editor - {os.path.basename(path)}")
                except:
                    pass

        except Exception as e:
            print(f"Error loading MIDI: {e}")
            import traceback
            traceback.print_exc()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.mid') or file_path.lower().endswith('.midi'):
                self.load_midi(file_path)
                break

    # Wheel Event Handling for Zoom
    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            zoom_factor = 1.2 if delta > 0 else 0.8
            
            # Update Global Scale
            global PIXELS_PER_SEC
            old_pps = PIXELS_PER_SEC
            PIXELS_PER_SEC *= zoom_factor
            PIXELS_PER_SEC = max(10, min(2000, PIXELS_PER_SEC))
            
            if old_pps != PIXELS_PER_SEC:
                # Re-layout all notes
                self.redraw_notes()
            
            event.accept()
        else:
            super().wheelEvent(event)

    def redraw_notes(self):
        # Update all items positions
        for item in self.scene.items():
            if isinstance(item, NoteItem):
                item.update_geometry_zoom(PIXELS_PER_SEC, KEY_HEIGHT)
        
        # Update Grid
        self.draw_grid()
        self.view.update()

    def save_midi(self):
        if not self.file_path or not self.pm: return
        
        # Clear original notes
        # We assume single track editing for simplicity? Or merge all back to Track 0?
        # User requested "Simple". Lets reuse the first non-drum instrument.
        
        target_inst = None
        for inst in self.pm.instruments:
            if not inst.is_drum:
                target_inst = inst
                break
        
        if not target_inst:
            # Create one if missing
            target_inst = pretty_midi.Instrument(program=0)
            self.pm.instruments.append(target_inst)
            
        target_inst.notes = []
        
        # Collect from Scene
        for item in self.scene.items():
            if isinstance(item, NoteItem):
                note = item.get_data()
                target_inst.notes.append(note)
                
        # Write
        try:
            self.pm.write(self.file_path)
            print(f"Saved: {self.file_path}")
            self.saved.emit()
        except Exception as e:
            print(f"Error saving: {e}")
