import os
import glob
import pandas as pd
import sys

# Setup paths (mimicking main.py)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR) # z:\MIDI_Dictionary
MIDI_LIB_PATH = os.path.join(ROOT_DIR, "MIDI_Library")

print(f"--- Debug Integration ---")
print(f"Root Dir: {ROOT_DIR}")
print(f"Midi Lib Path: {MIDI_LIB_PATH}")

if not os.path.exists(MIDI_LIB_PATH):
    print("ERROR: MIDI_Library folder does not exist!")
    sys.exit(1)

# Test Recursive Glob
pattern = os.path.join(MIDI_LIB_PATH, "**", "*.xlsx")
print(f"Glob Pattern: {pattern}")
files = glob.glob(pattern, recursive=True)

print(f"Found {len(files)} files:")
for f in files:
    print(f" - {f}")

# Try Reading
dfs = []
for f in files:
    if "~" in f: 
        print(f"Skipping temp file: {f}")
        continue
    
    try:
        print(f"Reading {os.path.basename(f)}...", end="")
        d = pd.read_excel(f)
        print(f" OK. Rows: {len(d)}")
        dfs.append(d)
    except Exception as e:
        print(f" FAIL. Error: {e}")

if dfs:
    combined = pd.concat(dfs, ignore_index=True)
    print(f"Total Combined Rows: {len(combined)}")
    
    # Try Saving
    dest = os.path.join(ROOT_DIR, "MasterLibraly_DEBUG.xlsx")
    try:
        combined.to_excel(dest, index=False)
        print(f"Saved debug master to: {dest}")
    except Exception as e:
        print(f"Error saving: {e}")
else:
    print("No data collected.")
