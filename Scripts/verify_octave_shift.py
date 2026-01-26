
import sys
import os

# Add project root to path
# Add project root and module dir to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'EnsembleGenerator'))

from EnsembleGenerator.style_strategies import ExternalStyleStrategy

def test_octave_shift():
    print("Testing ExternalStyleStrategy Octave Shift...")
    
    # Mock voices_data (minimal structure)
    voices_data = [{'voice': 1, 'type': 'seq', 'data': [], 'swing': 0.0}]
    strategy = ExternalStyleStrategy(voices_data)
    
    # Test Case 1: Bass Range
    root_pitch = 36 # C2
    step_val = 0    # No steps up from root
    chord_type = "Major" # Defines intervals
    
    # Expected: 36 + 12 = 48
    result = strategy._get_pitch_from_step(step_val, root_pitch, chord_type)
    print(f"Test 1 (Root=36, Step=0): Expected 48, Got {result}")
    
    if result == 48:
        print("PASS")
    else:
        print("FAIL")

    # Test Case 2: Interval Check
    # Major Interval: [4, 3, 5]
    # Step 1 should be Root + 12 + 4 = 16 + 36 = 52
    step_val = 1
    result = strategy._get_pitch_from_step(step_val, root_pitch, chord_type)
    print(f"Test 2 (Root=36, Step=1): Expected 52 (48+4), Got {result}")
    
    if result == 52:
        print("PASS")
    else:
        print("FAIL")

    # Test Case 3: Rename Logic Check
    # Mock row with rename_src
    voices_data_rename = [{'voice': 1, 'type': 'seq', 'data': [], 'swing': 0.0, 'rename_src': 'Piano'}]
    strategy_rename = ExternalStyleStrategy(voices_data_rename)
    
    # Check if property is set
    result_rename = getattr(strategy_rename, 'rename_src', None)
    print(f"Test 3 (Rename Logic): Expected 'Piano', Got '{result_rename}'")
    
    if result_rename == 'Piano':
        print("PASS")
    else:
        print("FAIL")

if __name__ == "__main__":
    test_octave_shift()
