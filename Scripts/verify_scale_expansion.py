
import unittest
import os
import sys
import pretty_midi

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'EnsembleGenerator'))

from EnsembleGenerator.midi_ensemble_generator import EnsembleGenerator


def test_expand_scale_generation():
    print("Testing Scale Expansion Generation (Plain Script)...")
    
    output_dir = os.path.join(project_root, "temp_test_output")
    input_midi_path = os.path.join(project_root, "temp_test_input.mid")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create dummy MIDI
    pm = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=0)
    # C3 note
    note = pretty_midi.Note(velocity=100, pitch=48, start=0.0, end=1.0)
    inst.notes.append(note)
    pm.instruments.append(inst)
    pm.write(input_midi_path)
    
    generator = EnsembleGenerator(output_dir=output_dir)

    try:
        from EnsembleGenerator.registries import STYLE_REGISTRY
        if not STYLE_REGISTRY:
             print("SKIPPING: No styles registered. Cannot verify generation.")
             return

        # Pick one style
        style_name = list(STYLE_REGISTRY.keys())[0]
        print(f"Using Style: {style_name}")
        
        # Modular Expansion Verification (Simulate '7th' checkbox)
        flags = {'7th': True}
        
        # [Validation Test 2: Note Content Check (Triad vs 7th)]
        # ... (Existing Triad/7th check) ...
        
        print("\n--- Testing Tension Generation (CM9, Em11 check) ---")
        gen_tension = generator.generate(
            input_midi_path,
            key_arg="C Major",
            expansion_flags={'tension': True},
            output_subdir="ExpansionValidation"
        )
        
        # Check for expected filenames
        found_m9 = False
        found_m11 = False
        for f in gen_tension:
            base = os.path.basename(f)
            if "CM9" in base: found_m9 = True
            if "Em11" in base or "m11" in base: found_m11 = True
            
        if found_m9 and found_m11:
             print("PASS: Generated CM9 and Em11 files.")
             
             # Deep Verification: Check pitch content of CM9 file
             cm9_file = next((f for f in gen_tension if "CM9" in os.path.basename(f)), None)
             if cm9_file:
                 pm_9 = pretty_midi.PrettyMIDI(cm9_file)
                 pcs_9 = set()
                 for inst in pm_9.instruments:
                     for note in inst.notes:
                         pcs_9.add(note.pitch % 12)
                 
                 # C Major 9: C(0), E(4), G(7), B(11), D(2).
                 # We expect 2 (D) to be present.
                 if 2 in pcs_9:
                     print(f"PASS: CM9 file contains pitch class 2 (D/9th). PCs: {sorted(list(pcs_9))}")
                 else:
                     print(f"WARN: CM9 file missing 9th (D/2). PCs: {sorted(list(pcs_9))}. (Style voice count might be too low?)")
        else:
             print(f"FAIL: Missing expected tension files. Found: {[os.path.basename(x) for x in gen_tension]}")

        # [Validation Test 3: Stop Event]
        
        # 1. Generate Triad (C Major I -> C Major Triad)
        gen_triad = generator.generate(
            input_midi_path,
            key_arg="C Major",
            expansion_flags={'triad': True},
            output_subdir="ExpansionValidation"
        )
        
        # 2. Generate 7th (C Major I -> C Major 7)
        gen_7th = generator.generate(
            input_midi_path,
            key_arg="C Major",
            expansion_flags={'7th': True},
            output_subdir="ExpansionValidation"
        )
        
        # Analyze first output of each
        if gen_triad and gen_7th:
            file_t = gen_triad[0]
            file_7 = gen_7th[0]
            
            print(f"Triad file: {os.path.basename(file_t)}")
            print(f"7th file:   {os.path.basename(file_7)}")
            
            # Load and check pitch classes
            pm_t = pretty_midi.PrettyMIDI(file_t)
            pm_7 = pretty_midi.PrettyMIDI(file_7)
            
            def get_unique_pcs(pm):
                 pcs = set()
                 for inst in pm.instruments:
                     for note in inst.notes:
                         pcs.add(note.pitch % 12)
                 return pcs

            pcs_t = get_unique_pcs(pm_t) # Expected C, E, G -> {0, 4, 7}
            pcs_7 = get_unique_pcs(pm_7) # Expected C, E, G, B -> {0, 4, 7, 11}
            
            print(f"Triad PCS: {sorted(list(pcs_t))} (Expected C,E,G -> 0,4,7)")
            print(f"7th   PCS: {sorted(list(pcs_7))} (Expected C,E,G,B -> 0,4,7,11)")
            
            if len(pcs_t) == 3 and len(pcs_7) == 4:
                 print("PASS: Triad has 3 distinct pitch classes, 7th has 4.")
            else:
                 print("WARN/FAIL: Pitch class counts do not match expectation (might be OK if doubling/omission, but checking).")
        
        # [Validation Test 3: Stop Event]
        import threading
        stop_evt = threading.Event()
        stop_evt.set()
        
        print("\n--- Testing Stop Event (Expected Immediate Cancellation) ---")
        gen_stop = generator.generate(
            input_midi_path,
            key_arg="C Major", 
            expansion_flags=flags, 
            stop_event=stop_evt,
            output_subdir="ExpansionValidation"
        )
        if len(gen_stop) == 0:
             print("PASS: Correctly cancelled generation (0 files).")
        else:
             print(f"FAIL: Generated files despite Stop Event! {len(gen_stop)}")

        # [Validation Test 1: Strict Voice Check]
        # Register a mock style with only 3 voices
        from EnsembleGenerator.style_strategies import ExternalStyleStrategy
        from EnsembleGenerator.registries import STYLE_REGISTRY
        mock_3voice_data = [
            {'voice':1, 'type':'seq', 'data':['1'], 'swing':0.0},
            {'voice':2, 'type':'seq', 'data':['1'], 'swing':0.0},
            {'voice':3, 'type':'seq', 'data':['1'], 'swing':0.0}
        ]
        # Set rename_src for filtering test
        def mock_factory_strict():
             s = ExternalStyleStrategy(mock_3voice_data)
             s.rename_src = "MockType"
             return s
             
        STYLE_REGISTRY["Mock_3Voice"] = mock_factory_strict
        
        print("\n--- Testing Strict Validation (Expected Skip) ---")
        gen_skip = generator.generate(
            input_midi_path,
            key_arg="C Major", 
            chord_filter="Diatonic_7th",
            style_filter="Mock_3Voice",
            expansion_flags=flags, 
            strict_validation=True, # STRICT ON
            output_subdir="ExpansionValidation"
        )
        if len(gen_skip) == 0:
            print("PASS: Correctly skipped 7th generation for 3-voice style with Strict=True.")
        else:
            print(f"FAIL: Generated {len(gen_skip)} files despite insufficient voices (Strict=True)!")

        print("\n--- Testing Strict Validation (OFF) (Expected Generation) ---")
        gen_allow = generator.generate(
            input_midi_path,
            key_arg="C Major", 
            chord_filter="Diatonic_7th",
            style_filter="Mock_3Voice",
            expansion_flags=flags, 
            strict_validation=False, # STRICT OFF
            output_subdir="ExpansionValidation"
        )
        if len(gen_allow) > 0:
            print(f"PASS: Generated {len(gen_allow)} files with Strict=False.")
        else:
            print("FAIL: Skipped generation even when Strict=False!")

        print("\n--- Testing Style Filtering (MockType vs Allowed=['Pad']) ---")
        # Should be skipped because "MockType" is not in allowed list
        gen_filter = generator.generate(
            input_midi_path,
            key_arg="C Major", 
            chord_filter="Diatonic_7th",
            style_filter="Mock_3Voice",
            expansion_flags=flags,
            allowed_types=['Pad'], # Exclude MockType
            strict_validation=False,
            output_subdir="ExpansionValidation"
        )
        if len(gen_filter) == 0:
             print("PASS: Correctly skipped MockType because it wasn't in allowed list.")
        else:
             print(f"FAIL: Generated files despite filtering! {gen_filter}")

        print("\n--- Testing Standard Expansion (Pad01) ---")
        generated_files = generator.generate(
            input_midi_path,
             key_arg="C Major", # Explicit key
            chord_filter="Diatonic_7th",
            style_filter=style_name,
            expansion_flags=flags, 
            output_subdir="ExpansionTest"
        )
        
        print(f"Generated {len(generated_files)} files.")
        for f in generated_files:
            print(f" - {os.path.basename(f)}")
            
        # Expectation: 7 degrees (Major Scale) * 1 Chord * 1 Style = 7 files
        if len(generated_files) == 7:
            # Check for dynamic names (at least M7 and m7 should appear for C Major)
            filenames = [os.path.basename(f) for f in generated_files]
            has_maj7 = any("M7" in fn for fn in filenames) # Replaced Maj7 with M7
            has_m7 = any("m7" in fn for fn in filenames)
            
            if has_maj7 and has_m7:
                print("PASS: Generated 7 files with Dynamic Chord Names (found M7 and m7).")
            else:
                print(f"FAIL: Files generated but qualities missing? {filenames}")
        else:
            print(f"FAIL: Generated {len(generated_files)} files (Expected 7).")

    finally:
        # Cleanup
        if os.path.exists(input_midi_path):
            os.remove(input_midi_path)
        # Clean output dir
        if os.path.exists(output_dir):
            import shutil
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    test_expand_scale_generation()
