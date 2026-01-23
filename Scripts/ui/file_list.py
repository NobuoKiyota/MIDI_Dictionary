from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
from PySide6.QtCore import Qt, Signal, QMimeData, QUrl
from PySide6.QtGui import QDrag
import os

class FileListWidget(QTableWidget):
    fileSelected = Signal(str) # Path
    fileRenamed = Signal(str, str) # OldPath, NewName (FileName cell text)

    def __init__(self):
        super().__init__()
        self.setColumnCount(8)
        self.setHorizontalHeaderLabels([
            "FileName", "Key", "Category", 
            "Inst", "Beat", "BAR", 
            "Chord", "Group"
        ])
        
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive) 
        header.setStretchLastSection(False) 
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        
        # Set Min Widths 
        self.setColumnWidth(0, 200) # FileName
        self.setColumnWidth(1, 40)  # Key
        self.setColumnWidth(2, 60)  # Category
        self.setColumnWidth(3, 60)  # Inst
        self.setColumnWidth(4, 40)  # Beat
        self.setColumnWidth(5, 30)  # BAR
        self.setColumnWidth(6, 60)  # Chord
        self.setColumnWidth(7, 80)  # Group
        
        self.horizontalHeader().setMinimumSectionSize(30)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed) # Allow edit
        self.setSortingEnabled(True)
        self.setDragEnabled(True)
        
        self.itemSelectionChanged.connect(self.on_selection_changed)
        self.itemChanged.connect(self.on_item_changed)
        
        self.is_populating = False
        self.is_updating = False

    def populate(self, df):
        self.is_populating = True
        self.setSortingEnabled(False)
        self.setRowCount(0)
        self.setRowCount(len(df))
        
        # Columns: FileName, Key, Category, Inst, Beat, BAR, Chord, Group
        
        for row_idx, (_, row_data) in enumerate(df.iterrows()):
            # 0. FileName
            file_name = str(row_data.get('FileName', ''))
            item0 = QTableWidgetItem(file_name)
            item0.setData(Qt.UserRole, row_data.get('FilePath', ''))
            self.setItem(row_idx, 0, item0)
            
            # 1. Key (Root)
            item1 = QTableWidgetItem(str(row_data.get('Root', '')))
            self.setItem(row_idx, 1, item1)

            # 2. Category
            item2 = QTableWidgetItem(str(row_data.get('Category', '')))
            self.setItem(row_idx, 2, item2)
            
            # 3. Inst (Instruments)
            item3 = QTableWidgetItem(str(row_data.get('Instruments', '')))
            self.setItem(row_idx, 3, item3)
            
            # 4. Beat (TimeSignature)
            item4 = QTableWidgetItem(str(row_data.get('TimeSignature', '')))
            self.setItem(row_idx, 4, item4)
            
            # 5. BAR
            # Try BAR, then Bar
            val = row_data.get('BAR', row_data.get('Bar', ''))
            item5 = QTableWidgetItem(str(val)) 
            self.setItem(row_idx, 5, item5)
            
            # 6. Chord
            item6 = QTableWidgetItem(str(row_data.get('Chord', '')))
            self.setItem(row_idx, 6, item6)
            
            # 7. Group
            item7 = QTableWidgetItem(str(row_data.get('Group', '')))
            item7.setFlags(item7.flags() | Qt.ItemIsEditable) 
            self.setItem(row_idx, 7, item7)
            
        self.setSortingEnabled(True)
        self.is_populating = False
        
        # Prevent Column 0 collapse
        if self.columnWidth(0) < 50:
            self.setColumnWidth(0, 200)

    def on_selection_changed(self):
        items = self.selectedItems()
        if items:
            row = self.currentRow()
            first_item = self.item(row, 0)
            if first_item:
                path = first_item.data(Qt.UserRole)
                if path:
                    self.fileSelected.emit(path)

    def on_item_changed(self, item):
        if self.is_populating or self.is_updating: return
        
        row = item.row()
        col = item.column()
        text = item.text()
        
        # Auto-Correction Logic
        corrected_text = text
        if col == 1: # Key
            corrected_text = text.capitalize() # c# -> C#
        elif col == 6: # Chord
             # Simplistic: "major" -> "Major", "minor" -> "minor" (wait convention?)
             # User said "Uppercase". 
             # Let's just Capitalize first letter for visual consistency?
             # Or keep user input if complex?
             # For Key, definitely C, D, etc.
             pass
        
        if corrected_text != text:
             self.is_updating = True
             item.setText(corrected_text)
             self.is_updating = False
             text = corrected_text # Use corrected for emit

        # If FileName column changed
        if col == 0:
            old_path = item.data(Qt.UserRole)
            if old_path:
                self.fileRenamed.emit(old_path, text)
        else:
            # Handle other metadata updates if needed.
            pass

    def startDrag(self, supportedActions):
        row = self.currentRow()
        if row < 0: return
        
        first_item = self.item(row, 0)
        path = first_item.data(Qt.UserRole)
        if not path: return
        
        mime = QMimeData()
        url = QUrl.fromLocalFile(path)
        mime.setUrls([url])
        
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec_(supportedActions)
