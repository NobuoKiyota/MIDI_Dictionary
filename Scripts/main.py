import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QMenuBar, QMenu, QLineEdit, QTextEdit
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QTimer
import pandas as pd

# Import our modules
from data_manager import DataManager
from midi_utils import MidiHandler
from ui.piano_roll import PianoRollWidget
from ui.file_list import FileListWidget
from ui.filter_panel import FilterPanel
from ui.register_dialog import RegistrationDialog
from ui.color_dialog import ColorConfigDialog
from ui.help_dialog import HelpDialog
from ui.help_dialog import HelpDialog
from config_manager import ConfigManager
from midi_player import MidiPlayer
import ui_constants as C

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIDI Dictionary")
        self.setFixedSize(C.WINDOW_WIDTH, C.WINDOW_HEIGHT)
        
        # Config Logic
        self.config_manager = ConfigManager()
        
        # Paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(script_dir) # Go up one level to root
        self.base_dir = self.project_root # Alias for compatibility if needed
        self.lib_path = os.path.join(self.project_root, "MIDI_Library")
        self.db_path = os.path.join(self.project_root, "library.xlsx")
        
        # Core Logic
        self.midi_handler = MidiHandler(self.lib_path)
        self.data_manager = DataManager(self.db_path, self.base_dir)
        self.player = MidiPlayer()
        self.auto_play_enabled = False
        
        # UI Setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_h_layout = QHBoxLayout(central_widget)
        self.main_h_layout.setContentsMargins(0, 0, 0, 0)
        self.main_h_layout.setSpacing(0)
        
        # --- Panel A (List Side) ---
        self.panel_a = QWidget()
        # Allow dynamic width (Window 1200 - Panel 700 = 500)
        self.panel_a.setFixedHeight(C.LIST_PANEL_HEIGHT)
        layout_a = QVBoxLayout(self.panel_a)
        layout_a.setContentsMargins(5, 5, 5, 5)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(C.SEARCH_PLACEHOLDER)
        self.search_bar.textChanged.connect(self.handle_search_text)
        layout_a.addWidget(self.search_bar)
        
        self.file_list = FileListWidget()
        layout_a.addWidget(self.file_list, stretch=1) # Stretch list
        
        # Bottom Comment Display
        self.comment_display = QTextEdit()
        self.comment_display.setReadOnly(True)
        self.comment_display.setPlaceholderText("Selected file comment...")
        self.comment_display.setFixedHeight(80) # Small fixed height
        layout_a.addWidget(self.comment_display)
        
        # --- Panel B (Right Side) ---
        self.panel_b = QWidget()
        self.panel_b.setFixedSize(C.PANEL_WIDTH, C.WINDOW_HEIGHT) # Should be full height container
        layout_b = QVBoxLayout(self.panel_b)
        layout_b.setContentsMargins(0, 0, 0, 0)
        layout_b.setSpacing(0)
        
        # Piano Roll (Top Right)
        # 480x270
        self.piano_roll = PianoRollWidget(self.config_manager)
        self.piano_roll.setFixedSize(C.PANEL_WIDTH, C.PIANO_ROLL_HEIGHT)
        layout_b.addWidget(self.piano_roll)
        
        # Filter Panel (Bottom Right)
        # 480x270
        self.filter_panel = FilterPanel()
        self.filter_panel.setFixedSize(C.PANEL_WIDTH, C.FILTER_PANEL_HEIGHT)
        layout_b.addWidget(self.filter_panel)
        
        # Initial Layout: A | B
        self.main_h_layout.addWidget(self.panel_a)
        self.main_h_layout.addWidget(self.panel_b)
        self.is_layout_swapped = False
        
        # Menus
        self.create_menus()
        
        # Connect Signals
        self.piano_roll.fileDropped.connect(self.handle_import)
        self.filter_panel.filtersChanged.connect(self.handle_filter)
        self.file_list.fileSelected.connect(self.handle_selection)
        self.file_list.fileRenamed.connect(self.handle_rename)
        
        # State used for filtering
        self.current_filters = {}
        self.current_search_text = ""
        
        # Restore State
        self.restore_app_state()
        
        # Initial Load
        # Integrate Master DB first (Startup Logic)
        self.data_manager.integrate_master_db()
        
        self.refresh_list()
        
        # Shortcut for Media Key (Space)
        # Using QShortcut ensures it works even if focus is on child widgets
        from PySide6.QtGui import QShortcut, QKeySequence
        self.space_shortcut = QShortcut(QKeySequence(Qt.Key_Space), self)
        self.space_shortcut.activated.connect(self.toggle_playback)

    def toggle_playback(self):
        if self.player.is_playing():
            self.player.stop()
        else:
             if hasattr(self, 'last_selected_path') and self.last_selected_path:
                 self._play_file(self.last_selected_path)

    def create_menus(self):
        menubar = self.menuBar()
        
        # View Menu
        view_menu = menubar.addMenu("View")
        
        self.aot_action = QAction("Always on Top", self, checkable=True)
        self.aot_action.triggered.connect(self.toggle_always_on_top)
        view_menu.addAction(self.aot_action)
        
        self.swap_action = QAction("Switch Layout", self)
        self.swap_action.triggered.connect(self.toggle_layout)
        view_menu.addAction(self.swap_action)
        
        view_menu.addSeparator()
        
        self.vis_action = QAction("Visualize Learning Progress...", self)
        self.vis_action.triggered.connect(self.open_visualization)
        view_menu.addAction(self.vis_action)
        
        # Settings Menu
        settings_menu = menubar.addMenu("Settings")
        
        color_action = QAction("Note Colors...", self)
        color_action.triggered.connect(self.open_color_config)
        settings_menu.addAction(color_action)
        
        self.auto_play_action = QAction("Auto Play", self, checkable=True)
        self.auto_play_action.triggered.connect(self.toggle_auto_play)
        settings_menu.addAction(self.auto_play_action)
        
        # Help Menu
        help_menu = menubar.addMenu("Help")
        help_action = QAction("Manual...", self)
        help_action.triggered.connect(self.open_help)
        help_menu.addAction(help_action)
        
        # Tools Menu
        tools_menu = menubar.addMenu("Tools")
        
        checker_action = QAction("MIDI Checker Tool...", self)
        checker_action.triggered.connect(self.open_midi_checker)
        tools_menu.addAction(checker_action)

    def open_midi_checker(self):
        # Prevent GC by keeping reference
        from midi_checker import MidiCheckerWindow
        self.midi_checker_window = MidiCheckerWindow()
        self.midi_checker_window.show()

    def open_visualization(self):
        from learning_visualizer import LearningVisualizer
        learning_path = os.path.join(self.base_dir, "MIDI_learning", "learning_data.xlsx")
        # LearningVisualizer expects a master window but we can pass self.
        # Note: Visualizer is a Toplevel so it opens a new window.
        LearningVisualizer(self, learning_path)

    def toggle_layout(self):
        # Swap A and B
        # Remove both
        self.main_h_layout.removeWidget(self.panel_a)
        self.main_h_layout.removeWidget(self.panel_b)
        
        self.is_layout_swapped = not self.is_layout_swapped
        
        if self.is_layout_swapped:
            # B | A
            self.main_h_layout.addWidget(self.panel_b)
            self.main_h_layout.addWidget(self.panel_a)
        else:
            # A | B
            self.main_h_layout.addWidget(self.panel_a)
            self.main_h_layout.addWidget(self.panel_b)

    def toggle_always_on_top(self, checked):
        if checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show() # Re-show needed after flag change

    def open_color_config(self):
        dlg = ColorConfigDialog(self.config_manager, self)
        if dlg.exec():
            # Refresh Piano Roll
            self.piano_roll.refresh_colors()

    def open_help(self):
        dlg = HelpDialog(self)
        dlg.exec()
        
    def toggle_auto_play(self, checked):
        self.auto_play_enabled = checked
        if not checked:
             self.player.stop()
            
    def _play_file(self, file_path):
        if not os.path.exists(file_path): return
        
        # Get metadata for instrument override
        # Fix path matching
        try:
            rel_path = os.path.relpath(file_path, self.base_dir)
        except:
            rel_path = file_path
            
        mask = (self.data_manager.df['FilePath'] == file_path) | (self.data_manager.df['FilePath'] == rel_path)
        
        inst_text = None
        if mask.any():
            inst_text = self.data_manager.df.loc[mask, 'Instruments'].iloc[0]
            if pd.isna(inst_text): inst_text = None
            else: inst_text = str(inst_text)
            
        print(f"DEBUG: Selected File: {file_path}")
        print(f"DEBUG: Found Instrument in DB: {inst_text}")
            
        self.player.play(file_path, inst_text)

    def restore_app_state(self):
        # Load Window State / Geometry / AOT
        is_top = self.config_manager.load_window_state(self)
        self.aot_action.setChecked(is_top)
        self.toggle_always_on_top(is_top)

    def closeEvent(self, event):
        # Save State
        self.config_manager.save_window_state(self)
        super().closeEvent(event)

    def refresh_list(self):
        # Create a display copy of the dataframe
        display_df = self.data_manager.df.copy()
        
        # Convert relative paths to absolute for display/usage logic
        # We assume database stores relative paths now.
        if not display_df.empty and 'FilePath' in display_df.columns:
            display_df['FilePath'] = display_df['FilePath'].apply(
                lambda p: os.path.abspath(os.path.join(self.base_dir, p)) if p and not os.path.isabs(p) else p
            )
            
        self.file_list.populate(display_df)

    def handle_import(self, file_path):
        # 1. Analyze
        info = self.midi_handler.analyze_midi(file_path)
        if not info:
            QMessageBox.warning(self, "Error", "Failed to parse MIDI file.")
            return

        # Prepare initial data for dialog
        filename = os.path.basename(file_path)
        filename = os.path.splitext(filename)[0]
        
        init_data = {
            "filename": filename,
            "time_signature": info['time_signature'],
            "duration_bars": info['duration_bars'],
            "inferred_meta": info.get('inferred_meta', {})
        }

        # 2. Show Dialog
        dialog = RegistrationDialog(self, init_data)
        if dialog.exec():
            metadata = dialog.get_metadata()
            
            # Pass the user-edited filename to copy_to_library
            # This ensures the physical file is named as requested.
            target_name = metadata.get("FileName", "")
            new_path = self.midi_handler.copy_to_library(file_path, target_name)
            
            # Update metadata with the ACTUAL final path and filename (in case of collision renaming)
            metadata["FilePath"] = new_path
            metadata["FileName"] = os.path.splitext(os.path.basename(new_path))[0]
            
            self.data_manager.add_entry(metadata)
            
            # Save Learning Data (Feedback Loop)
            self.midi_handler.save_learning_data(file_path, metadata)
            
            self.refresh_list()
            
            # Parse TS for numerator
            ts_str = info['time_signature']
            try:
                num = int(ts_str.split('/')[0])
            except:
                num = 4
                
            self.piano_roll.set_notes(info['notes'], info.get('tempo', 120), num, new_path)

    def handle_search_text(self, text):
        self.current_search_text = text.lower()
        self.apply_filters()
        
    def handle_filter(self, filters):
        self.current_filters = filters
        self.apply_filters()
        
    def apply_filters(self):
        # Get base filtered data from DataManager
        filtered_df = self.data_manager.get_filtered_data(self.current_filters)
        
        # Apply Text Search if needed
        if self.current_search_text:
            mask = False
            for col in ["FileName", "Group", "Comment"]:
                if col in filtered_df.columns:
                    mask |= filtered_df[col].astype(str).str.lower().str.contains(self.current_search_text)
            
            filtered_df = filtered_df[mask]
            
        self.file_list.populate(filtered_df)

    def handle_selection(self, file_path):
        if os.path.exists(file_path):
            info = self.midi_handler.analyze_midi(file_path)
            if info:
                ts_str = info['time_signature']
                try:
                    num = int(ts_str.split('/')[0])
                except:
                    num = 4
                self.piano_roll.set_notes(info['notes'], info.get('tempo', 120), num, file_path)
            
            self.last_selected_path = file_path # Track for Space key
            
            if self.auto_play_enabled:
                 self._play_file(file_path)
            
            # Update Comment Display
            # Fix path matching (DB uses relative, UI uses absolute)
            try:
                rel_path = os.path.relpath(file_path, self.base_dir)
            except:
                rel_path = file_path
                
            mask = (self.data_manager.df['FilePath'] == file_path) | (self.data_manager.df['FilePath'] == rel_path)
            
            if mask.any():
                comment = self.data_manager.df.loc[mask, 'Comment'].iloc[0] # Use iloc[0] for safety
                self.comment_display.setText(str(comment) if pd.notna(comment) else "")
            else:
                self.comment_display.clear()

    def _play_file(self, file_path):
        if not os.path.exists(file_path): return
        
        # Get metadata for instrument override
        # Fix path matching
        try:
            rel_path = os.path.relpath(file_path, self.base_dir)
        except:
            rel_path = file_path
            
        mask = (self.data_manager.df['FilePath'] == file_path) | (self.data_manager.df['FilePath'] == rel_path)
        
        inst_text = None
        if mask.any():
            inst_text = self.data_manager.df.loc[mask, 'Instruments'].iloc[0]
            if pd.isna(inst_text): inst_text = None
            else: inst_text = str(inst_text)
            
        print(f"DEBUG: Selected File: {file_path}")
        print(f"DEBUG: Found Instrument in DB: {inst_text}")
        
        self.player.play(file_path, inst_text)


    def handle_rename(self, old_path, new_name):
        if not os.path.exists(old_path):
            return

        directory = os.path.dirname(old_path)
        ext = os.path.splitext(old_path)[1]
        
        if not new_name.lower().endswith(ext.lower()):
            new_name += ext
            
        new_path = os.path.join(directory, new_name)
        
        if new_path == old_path:
            return

        # Collision Check
        if os.path.exists(new_path):
            reply = QMessageBox.question(
                self, "Overwrite Confirmation",
                f"File '{new_name}' already exists.\\nOverwrite?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                QTimer.singleShot(0, self.refresh_list)
                return
            else:
                try:
                    os.remove(new_path)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to delete existing file:\\n{e}")
                    QTimer.singleShot(0, self.refresh_list)
                    return

        # Rename
        try:
            os.rename(old_path, new_path)
            
            mask = self.data_manager.df['FilePath'] == old_path
            if mask.any():
                self.data_manager.df.loc[mask, 'FileName'] = os.path.splitext(new_name)[0]
                self.data_manager.df.loc[mask, 'FilePath'] = new_path
                self.data_manager.save_db()
            
            QTimer.singleShot(0, self.refresh_list)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to rename file:\\n{e}")
            QTimer.singleShot(0, self.refresh_list)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    app.setStyleSheet("""
        QMainWindow, QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QTableWidget {
            background-color: #1e1e1e;
            gridline-color: #3e3e3e;
            selection-background-color: #3d5afe;
        }
        QHeaderView::section {
            background-color: #3e3e3e;
            color: white;
        }
        QLineEdit, QComboBox, QTextEdit {
            background-color: #3e3e3e;
            color: white;
            border: 1px solid #5e5e5e;
        }
        QPushButton {
            background-color: #3d5afe;
            color: white;
            border: none;
            padding: 5px;
        }
        QMenuBar {
            background-color: #333;
            color: white;
        }
        QMenuBar::item:selected {
            background-color: #555;
        }
    """)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
