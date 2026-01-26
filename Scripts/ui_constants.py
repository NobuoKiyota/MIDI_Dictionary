# Window Size
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700

# Panel Sizes
# Left/Right Split Width
PANEL_WIDTH = 660 # Applied to the Right Panel (Piano/Filter). List Panel takes remaining space.

# Panel Heights
LIST_PANEL_HEIGHT = WINDOW_HEIGHT
PIANO_ROLL_HEIGHT = 450 # Top Right
FILTER_PANEL_HEIGHT = 250 # Bottom Right

# Font Sizes
FONT_SIZE_MAIN = "11px"   # General font size for FilterPanel styling
FONT_SIZE_LABEL = "11px"  # Label font size
FONT_SIZE_RADIO = "16px"  # Radio button font size

# Widget Dims
FILTER_LABEL_WIDTH = 60
FILTER_ROW_SPACING = 2

# Search Bar
SEARCH_PLACEHOLDER = "Search..."

# Master Lists
CHORD_LIST = [
    "None", "Power", "Major", "minor", "M7", "m7", "7th", "m7b5", "mM7","sus4", "aug", "dim",
     "9","m9", "b9","mb9", "11", "m11", "b11", "mb11", "13", "m13", "b13", "mb13"
]

KEY_LIST = ['-', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

CATEGORY_LIST = [
    "Rythem", "Bass", "Chord", "Arp", "Melody",
    "Fill", "FX", "Perc", "Pad", "Lead"
]

from instrument_config import INSTRUMENT_MAP
INSTRUMENT_LIST = sorted(INSTRUMENT_MAP.keys())
