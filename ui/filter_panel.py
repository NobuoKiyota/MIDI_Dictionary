from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QRadioButton, QButtonGroup, QLabel, QGroupBox, QPushButton
from PySide6.QtCore import Signal, Qt
import ui_constants as C

class FilterPanel(QWidget):
    filtersChanged = Signal(dict)

    def __init__(self):
        super().__init__()
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(5)
        
        self.groups = {}
        
        # 0. Root
        root_opts = ["No"] + ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        self.create_row("Root", root_opts)

        # 1. Category
        cat_opts = [
            "Rythem", "Bass", "Chord", "Arp", "Melody",
            "Fill", "FX", "Perc", "Pad", "Lead"
        ]
        self.create_row("Category", cat_opts)
        
        # 2. Time Signature
        ts_opts = ["2/4", "3/4", "4/4", "5/8", "6/8", "7/8", "8/8", "9/8", "12/8"]
        self.create_row("TimeSignature", ts_opts, title_text="Time Sig")
        
        # 3. Measure
        measure_opts = ["1BAR", "2BAR", "3BAR", "4BAR", "8BAR", "16BAR"]
        self.create_row("Measure", measure_opts)
        
        # 4. Chord (2 Rows) or expanded
        # User requested specific Chords list:
        # None, Power, Major, minor, M7, 7th
        # sus4, aug, 9th, b9, 11, b11, 13, b13
        chord_row1 = ["None", "Power", "Major", "minor", "m7", "M7", "7th"]
        chord_row2 = ["sus4", "aug", "9th", "b9", "11", "b11", "13", "b13"]
        self.create_chord_group("Chord", chord_row1, chord_row2)

        # Reset Button
        reset_layout = QHBoxLayout()
        self.reset_btn = QPushButton("Reset Filters")
        self.reset_btn.setFixedWidth(100)
        self.reset_btn.clicked.connect(self.reset_filters)
        reset_layout.addWidget(self.reset_btn)
        reset_layout.addStretch()
        
        self.main_layout.addLayout(reset_layout)
        self.main_layout.addStretch() 

        # Apply Stylesheet (Text Only, Red Highlight)
        self.setStyleSheet(f"""
            QGroupBox {{
                border: none;
                margin: 0px;
                padding: 0px;
            }}
            QLabel {{
                font-size: {C.FONT_SIZE_MAIN};
                font-weight: bold;
                color: #aaa;
            }}
            QRadioButton {{
                spacing: 0px;
                font-size: {C.FONT_SIZE_RADIO};
                padding: 1px;
                color: #888;
                border: none;
                background: none;
            }}
            QRadioButton::indicator {{
                width: 0px;
                height: 0px;
                border: none;
                background: none;
            }}
            QRadioButton:checked {{
                color: #ff0000; /* Red */
                font-weight: bold;
            }}
            QRadioButton:hover {{
                color: #ddd;
            }}
            QPushButton {{
                font-size: {C.FONT_SIZE_MAIN};
                padding: 2px;
            }}
        """)

    def create_row(self, title, options, title_text=None):
        # Container
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0) # Tighter spacing for commas
        layout.setAlignment(Qt.AlignLeft)
        
        # Label
        lbl_text = title_text if title_text else f"{title}:"
        lbl = QLabel(lbl_text)
        lbl.setFixedWidth(C.FILTER_LABEL_WIDTH) 
        lbl.setStyleSheet("margin-right: 5px;")
        layout.addWidget(lbl)
        
        # Radio Buttons
        btn_group = QButtonGroup(self)
        btn_group.setExclusive(True)
        
        for i, opt in enumerate(options):
            rb = QRadioButton(opt)
            rb.setCursor(Qt.PointingHandCursor)
            btn_group.addButton(rb)
            layout.addWidget(rb)
            rb.toggled.connect(self.emit_filters)
            
            # Add Comma separator
            if i < len(options) - 1:
                sep = QLabel(",")
                sep.setStyleSheet("color: #888; margin-left: 0px; margin-right: 6px;")
                layout.addWidget(sep)
            
        layout.addStretch() 
        
        self.main_layout.addWidget(container)
        self.groups[title] = btn_group

    def create_chord_group(self, title, row1, row2):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignLeft)
        
        # Label
        lbl = QLabel(f"{title}:")
        lbl.setFixedWidth(C.FILTER_LABEL_WIDTH)
        lbl.setStyleSheet("margin-right: 5px;")
        layout.addWidget(lbl)
        
        # Vertical Box for Rows
        vbox = QVBoxLayout()
        vbox.setContentsMargins(0,0,0,0)
        vbox.setSpacing(0)
        
        btn_group = QButtonGroup(self)
        btn_group.setExclusive(True)
        
        # Row 1
        r1 = QHBoxLayout()
        r1.setAlignment(Qt.AlignLeft)
        r1.setSpacing(0)
        for i, opt in enumerate(row1):
            rb = QRadioButton(opt)
            rb.setCursor(Qt.PointingHandCursor)
            btn_group.addButton(rb)
            r1.addWidget(rb)
            rb.toggled.connect(self.emit_filters)
            
            # Comma (always add for row 1 if it continues? or just within row)
            # Row 1 and Row 2 are logically one group "Chord".
            # The last item of Row 1 is visually separated from first of Row 2 by line break.
            # So basically standard comma logic within row.
            if i < len(row1) - 1:
                sep = QLabel(",")
                sep.setStyleSheet("color: #888; margin-left: 0px; margin-right: 6px;")
                r1.addWidget(sep)
                
        r1.addStretch()
        vbox.addLayout(r1)
        
        # Row 2
        r2 = QHBoxLayout()
        r2.setAlignment(Qt.AlignLeft)
        r2.setSpacing(0)
        for i, opt in enumerate(row2):
            rb = QRadioButton(opt)
            rb.setCursor(Qt.PointingHandCursor)
            btn_group.addButton(rb)
            r2.addWidget(rb)
            rb.toggled.connect(self.emit_filters)
            
            if i < len(row2) - 1:
                sep = QLabel(",")
                sep.setStyleSheet("color: #888; margin-left: 0px; margin-right: 6px;")
                r2.addWidget(sep)

        r2.addStretch()
        vbox.addLayout(r2)
        
        layout.addLayout(vbox)
        layout.addStretch()
        
        self.main_layout.addWidget(container)
        self.groups[title] = btn_group

    def emit_filters(self):
        current_filters = {}
        for title, group in self.groups.items():
            btn = group.checkedButton()
            if btn:
                current_filters[title] = btn.text()
            else:
                current_filters[title] = None
        
        self.filtersChanged.emit(current_filters)

    def reset_filters(self):
        for name, group in self.groups.items():
            group.setExclusive(False)
            if group.checkedButton():
                group.checkedButton().setChecked(False)
            group.setExclusive(True)
        self.emit_filters()
