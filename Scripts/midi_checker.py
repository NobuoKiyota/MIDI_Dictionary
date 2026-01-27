import sys
import os
import pathlib
import pandas as pd
import pretty_midi
import shutil
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QLabel, QTextEdit, QPushButton, QProgressBar,
                               QCheckBox, QSpinBox, QHBoxLayout)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont

class AnalysisWorker(QThread):
    """Worker thread to run analysis without freezing GUI."""
    log_signal = Signal(str)
    progress_signal = Signal(int) # 0-100
    finished_signal = Signal(str) # Result message

    def __init__(self, target_folder, auto_fix=False, max_iterations=10):
        super().__init__()
        self.target_folder = target_folder
        self.auto_fix = auto_fix
        self.max_iterations = max_iterations
        self.is_running = True

    def run(self):
        target_path = pathlib.Path(self.target_folder)
        self.log_signal.emit(f"Scanning folder: {target_path}...")
        if self.auto_fix:
            self.log_signal.emit(f"Auto-Fix Enabled (Max Iterations: {self.max_iterations})")

        midi_files = list(target_path.rglob("*.mid"))
        if not midi_files:
            self.log_signal.emit("No MIDI files found.")
            self.finished_signal.emit("No MIDI files found.")
            return

        self.log_signal.emit(f"Found {len(midi_files)} MIDI files.")
        
        results = []
        total = len(midi_files)
        
        for i, midi_file in enumerate(midi_files):
            if not self.is_running:
                break
                
            rel_path = midi_file.relative_to(target_path)
            status = "OK"
            was_fixed = False
            
            try:
                # Load MIDI
                pm = pretty_midi.PrettyMIDI(str(midi_file))
                
                # Auto-Fix
                if self.auto_fix:
                    fixed_count = self.fix_overlaps(pm, midi_file)
                    if fixed_count > 0:
                        was_fixed = True
                        status = f"Fixed ({fixed_count} overlaps)"
                        self.log_signal.emit(f"Fixed {fixed_count} overlaps in {rel_path}")
                
                # 1. Overlap Check (Post-Fix)
                is_overlap = self.check_overlap(pm)
                
                # 2. Duration (ms)
                duration_sec = pm.get_end_time()
                duration_ms = int(duration_sec * 1000)
                
                results.append({
                    "RelativePath": str(rel_path),
                    "HasOverlap": is_overlap,
                    "Duration_ms": duration_ms,
                    "Status": status
                })
                
            except Exception as e:
                self.log_signal.emit(f"Error processing {rel_path}: {e}")
                results.append({
                    "RelativePath": str(rel_path),
                    "HasOverlap": "Error",
                    "Duration_ms": 0,
                    "Status": f"Error: {e}"
                })
            
            # Progress
            percent = int((i + 1) / total * 100)
            self.progress_signal.emit(percent)

        if not self.is_running:
            self.finished_signal.emit("Cancelled.")
            return

        # Export
        output_path = target_path.parent / f"{target_path.name}_check.xlsx"
        try:
            df = pd.DataFrame(results)
            df.to_excel(output_path, index=False)
            self.log_signal.emit(f"Successfully created report: {output_path.name}")
            self.finished_signal.emit(f"Done. Saved to {output_path.name}")
        except Exception as e:
            self.log_signal.emit(f"Error saving Excel: {e}")
            self.finished_signal.emit("Error saving Excel.")

    def fix_overlaps(self, pm, file_path):
        """
        Recursively fixes overlaps by shortening prev note by 5 ticks.
        Returns total number of fixes made.
        """
        total_fixes = 0
        file_modified = False
        
        for iteration in range(self.max_iterations):
            fixes_this_pass = 0
            
            for inst in pm.instruments:
                if inst.is_drum: continue
                
                # Group by pitch
                notes_by_pitch = {}
                for note in inst.notes:
                    if note.pitch not in notes_by_pitch: notes_by_pitch[note.pitch] = []
                    notes_by_pitch[note.pitch].append(note)
                
                for pitch, notes in notes_by_pitch.items():
                    sorted_notes = sorted(notes, key=lambda x: x.start)
                    for i in range(len(sorted_notes) - 1):
                        curr = sorted_notes[i]
                        next_n = sorted_notes[i+1]
                        
                        # Check overlap
                        if curr.end > next_n.start + 0.001:
                            # Calculate ticks
                            start_tick = pm.time_to_tick(next_n.start)
                            # Target end is 5 ticks before next start
                            new_end_tick = start_tick - 5
                            if new_end_tick <= pm.time_to_tick(curr.start):
                                # If note becomes effectively zero length, maybe set to 1 tick len?
                                new_end_tick = pm.time_to_tick(curr.start) + 1
                            
                            new_end_time = pm.tick_to_time(new_end_tick)
                            curr.end = new_end_time
                            fixes_this_pass += 1
            
            total_fixes += fixes_this_pass
            if fixes_this_pass > 0:
                file_modified = True
            else:
                break # No more fixes needed
                
        if file_modified:
            # Create Backup
            backup_path = str(file_path) + ".bak"
            if not os.path.exists(backup_path):
                shutil.copy2(file_path, backup_path)
            
            # Save
            try:
                pm.write(str(file_path))
            except Exception as e:
                self.log_signal.emit(f"Error saving fixed file {file_path}: {e}")
                
        return total_fixes

    def check_overlap(self, pm):
        has_overlap = False
        for inst in pm.instruments:
            if inst.is_drum:
                continue
            
            # Group notes by pitch
            notes_by_pitch = {}
            for note in inst.notes:
                if note.pitch not in notes_by_pitch:
                    notes_by_pitch[note.pitch] = []
                notes_by_pitch[note.pitch].append(note)
            
            # Check overlaps within each pitch
            for pitch, notes in notes_by_pitch.items():
                # Sort by start time
                sorted_notes = sorted(notes, key=lambda x: x.start)
                for i in range(len(sorted_notes) - 1):
                    # If current note ends after next note starts -> Overlap
                    if sorted_notes[i].end > sorted_notes[i+1].start + 0.001: 
                        has_overlap = True
                        break
                if has_overlap:
                    break
            if has_overlap:
                break
        return has_overlap

    def stop(self):
        self.is_running = False


class MidiCheckerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIDI Checker Tool v1.1")
        self.resize(600, 500)
        self.setAcceptDrops(True)
        
        # UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Label
        self.label = QLabel("Drag & Drop Folder Here")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont("Arial", 16, QFont.Bold))
        self.label.setStyleSheet("border: 2px dashed #aaa; padding: 20px; color: #555;")
        layout.addWidget(self.label)
        
        # Controls Layout
        controls_layout = QHBoxLayout()
        
        # Checkbox
        self.chk_autofix = QCheckBox("Auto Fix Overlaps (-5 ticks)")
        self.chk_autofix.setStyleSheet("font-size: 14px; font-weight: bold;")
        controls_layout.addWidget(self.chk_autofix)
        
        # Iterations
        controls_layout.addStretch()
        controls_layout.addWidget(QLabel("Max Iterations:"))
        self.spin_iterations = QSpinBox()
        self.spin_iterations.setRange(1, 100)
        self.spin_iterations.setValue(10)
        controls_layout.addWidget(self.spin_iterations)
        
        layout.addLayout(controls_layout)
        
        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        layout.addWidget(self.progress)
        
        # Log Area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: #f0f0f0; font-family: Consolas;")
        layout.addWidget(self.log_area)
        
        # Worker
        self.worker = None

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if os.path.isdir(file_path):
                self.start_analysis(file_path)
            else:
                self.log("Please drop a folder, not a file.")

    def start_analysis(self, folder_path):
        if self.worker and self.worker.isRunning():
            self.log("Analysis already running. Please wait.")
            return

        self.label.setText(f"Analyzing: {os.path.basename(folder_path)}")
        self.log(f"Starting analysis for: {folder_path}")
        self.progress.setValue(0)
        
        auto_fix = self.chk_autofix.isChecked()
        max_iter = self.spin_iterations.value()
        
        self.worker = AnalysisWorker(folder_path, auto_fix, max_iter)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    @Slot(str)
    def log(self, message):
        self.log_area.append(message)
        # Also print to stdout for terminal view
        print(message) 

    @Slot(str)
    def on_finished(self, message):
        self.label.setText("Drag & Drop Folder Here")
        self.log("-" * 20)
        self.log(message)
        self.worker = None

def main():
    app = QApplication(sys.argv)
    window = MidiCheckerWindow()
    window.show()
    
    # Check command line args (if dropped on batch)
    if len(sys.argv) > 1:
        target_arg = sys.argv[1].strip('"')
        if os.path.isdir(target_arg):
            # Use QTimer to start after window load
            from PySide6.QtCore import QTimer
            QTimer.singleShot(500, lambda: window.start_analysis(target_arg))
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
