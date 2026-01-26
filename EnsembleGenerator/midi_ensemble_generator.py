import pretty_midi
import argparse
import os
import random
import random
import sys
import pandas as pd # New for Excel export

# Import components
# Using relative imports if running as package, or absolute for script compat
# Determining mode...
if __package__ is None or __package__ == '':
    # Script running standalone
    from constants import NOTE_NAMES, get_note_name
    from constants import MAJOR_SCALE, MINOR_SCALE, HARMONIC_MINOR_SCALE, MELODIC_MINOR_SCALE # Import scale constants
    from constants import MAJOR_7TH_QUALITIES, MINOR_7TH_QUALITIES, HARMONIC_MINOR_7TH_QUALITIES, MELODIC_MINOR_7TH_QUALITIES
    from utils import detect_key, get_tempo_at_time
    from registries import CHORD_REGISTRY, STYLE_REGISTRY
    import chord_strategies # Triggers registration
    import style_strategies # Triggers registration
    from style_strategies import load_style_catalog, ExternalStyleStrategy
    from midi_analyzer import MidiAnalyzer
    from expansion_strategies import DiatonicTriadStrategy, Diatonic7thStrategy, \
    HarmonicMinorStrategy, MelodicMinorStrategy, \
    DiatonicTensionStrategy # New

else:
    from .constants import NOTE_NAMES, get_note_name, MAJOR_SCALE, MINOR_SCALE, HARMONIC_MINOR_SCALE, MELODIC_MINOR_SCALE
    from .constants import MAJOR_7TH_QUALITIES, MINOR_7TH_QUALITIES, HARMONIC_MINOR_7TH_QUALITIES, MELODIC_MINOR_7TH_QUALITIES
    from .utils import detect_key, get_tempo_at_time
    from .registries import CHORD_REGISTRY, STYLE_REGISTRY
    from . import chord_strategies
    from . import style_strategies
    from .style_strategies import load_style_catalog, ExternalStyleStrategy
    from .midi_analyzer import MidiAnalyzer
    from .expansion_strategies import DiatonicTriadStrategy, Diatonic7thStrategy, \
    HarmonicMinorStrategy, MelodicMinorStrategy, \
    DiatonicTensionStrategy # New



# --- Presets ---
PRESETS = {
    "pop": [("Diatonic", "Pad"), ("Diatonic", "Rhythm")],
    "rock": [("Diatonic", "Rhythm"), ("Maj_Open", "Rhythm")],
    "game": [("Diatonic_Open", "Healing"), ("Diatonic_7th", "Pad")],
    "dance": [("Diatonic", "Trance"), ("Diatonic_Open", "Arp")],
    "lofi": [("Diatonic_7th", "LoFi"), ("Diatonic_Open", "Pad")]
}

def register_external_styles(registry):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(script_dir, "ensemble_styles.xlsx")
    print("Clearing Registry and reloading...")
    registry.clear() # Fix for caching issue
    external_styles = load_style_catalog(excel_path)
    
    for name, voices_data in external_styles.items():
        # Store as lambda to act as a factory
        # We need default argument to capture value in closure
        registry[name] = lambda d=voices_data: ExternalStyleStrategy(d)
        print(f"Registered External Style: {name}")

# Initialize Registry
register_external_styles(STYLE_REGISTRY)

class EnsembleGenerator:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Initialize expansion strategies once
        self.triad_strat = DiatonicTriadStrategy()
        self.seventh_strat = Diatonic7thStrategy()
        self.harmonic_strat = HarmonicMinorStrategy()
        self.melodic_strat = MelodicMinorStrategy()
        self.tension_strat = DiatonicTensionStrategy() # New

    def load_midi(self, file_path):
        try:
            return pretty_midi.PrettyMIDI(file_path)
        except Exception as e:
            print(f"Error loading MIDI: {e}")
            return None

    def humanize(self, notes, timing_jitter=0.01, duration_scale=0.95):
        for note in notes:
            jitter = random.uniform(-timing_jitter, timing_jitter)
            note.start = max(0, note.start + jitter)
            duration = note.end - note.start
            note.end = note.start + (duration * duration_scale)

    def group_by_beat(self, analysis_list, beats):
        """
        Group analysis objects by beat intervals.
        Returns: list of dictionary {'start', 'end', 'notes': [AnalysisObjects]}
        """
        if not analysis_list: return []
        
        groups = []
        start_time = analysis_list[0].note.start
        end_time = analysis_list[-1].note.end
        
        idx = 0
        while idx < len(beats) - 1 and beats[idx+1] <= start_time:
            idx += 1
            
        current_beat_idx = idx
        
        while current_beat_idx < len(beats) - 1:
            beat_start = beats[current_beat_idx]
            beat_end = beats[current_beat_idx + 1]
            
            if beat_start > end_time + 1.0: break
                
            notes_in_beat = []
            for ana in analysis_list:
                s = ana.note.start
                cond = (s >= beat_start - 0.001 and s < beat_end - 0.001)
                if cond:
                    notes_in_beat.append(ana)
            
            groups.append({
                'start': beat_start,
                'end': beat_end,
                'notes': notes_in_beat
            })
            
            current_beat_idx += 1
            
        return groups

    def get_dominant_root(self, notes_in_beat, beat_start):
        if not notes_in_beat: return None
        avg_vel = sum(n.note.velocity for n in notes_in_beat) / len(notes_in_beat)
        
        candidates = []
        for ana in notes_in_beat:
            note = ana.note
            score = 0
            if abs(note.start - beat_start) < 0.05:
                score += 1000
            if note.velocity > avg_vel * 1.2:
                score += 500
            elif note.velocity < avg_vel * 0.8:
                score -= 100
            score += (note.end - note.start)
            candidates.append((score, ana))
            
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def get_best_voicing(self, chord_notes, prev_centroid):
        if not prev_centroid:
            return chord_notes, sum(chord_notes)/len(chord_notes)
            
        c_sorted = sorted(chord_notes)
        if len(c_sorted) < 3: return chord_notes, sum(chord_notes)/len(chord_notes)
        
        n0, n1, n2 = c_sorted[0], c_sorted[1], c_sorted[2]
        inversions = [
            [n0, n1, n2],       # Root
            [n1, n2, n0+12],    # 1st Inv
            [n2, n0+12, n1+12]  # 2nd Inv
        ]
        
        final_candidates = []
        for inv in inversions:
            for octave in [-1, 0, 1]:
                shifted = [p + (octave * 12) for p in inv]
                centroid = sum(shifted) / len(shifted)
                dist = abs(centroid - prev_centroid)
                final_candidates.append((dist, shifted, centroid))
                
        final_candidates.sort(key=lambda x: x[0])
        return final_candidates[0][1], final_candidates[0][2]

    def merge_events(self, beat_events):
        if not beat_events: return []
        merged = []
        current = beat_events[0].copy()
        current['notes'] = current['notes'][:] 
        
        for i in range(1, len(beat_events)):
            next_evt = beat_events[i]
            if next_evt['chord_notes'] == current['chord_notes']:
                current['end'] = next_evt['end']
                current['notes'].extend(next_evt['notes'])
            else:
                merged.append(current)
                current = next_evt.copy()
                current['notes'] = current['notes'][:]
        
        merged.append(current)
        return merged

    def generate(self, input_path, velocity_scale=0.9, key_arg=None, chord_filter=None, style_filter=None, preset_name=None, output_subdir=None, expansion_flags=None, strict_validation=False, allowed_types=None, timing_jitter=0.01, stop_event=None):
        midi_data = self.load_midi(input_path)
        if not midi_data: return []
        
        original_name = os.path.splitext(os.path.basename(input_path))[0]
        generated_files = []
        metadata_list = [] # For Auto-Registration Report
        
        # --- Resolve Filters ---
        target_combinations = [] 
        if preset_name and preset_name in PRESETS:
            target_combinations = PRESETS[preset_name]
            if not output_subdir:
                output_subdir = preset_name.capitalize()
            print(f"Using Preset: {preset_name}")
        else:
            if chord_filter:
                target_chords = [c.strip() for c in chord_filter.split(',')]
            else:
                target_chords = list(CHORD_REGISTRY.keys())
                
            if style_filter:
                target_styles = [s.strip() for s in style_filter.split(',')]
            else:
                target_styles = list(STYLE_REGISTRY.keys())
                
            for c in target_chords:
                for s in target_styles:
                    target_combinations.append((c, s))
            
            if not output_subdir:
                output_subdir = "BEST" if (len(target_chords) == 1 and len(target_styles) == 1) else "Generated"

        input_dir = os.path.dirname(input_path)
        final_output_dir = os.path.join(input_dir, output_subdir)
        if not os.path.exists(final_output_dir):
            os.makedirs(final_output_dir)

        # --- Analysis ---
        key_info = None
        if key_arg and key_arg != "Auto":
            parts = key_arg.split()
            if len(parts) >= 2:
                root_str = parts[0]
                type_str = ' '.join(parts[1:])
                if root_str in NOTE_NAMES:
                    key_info = (NOTE_NAMES.index(root_str), type_str)
        
        if not key_info:
            key_info = detect_key(midi_data)
            print(f"Auto-detected Key: {get_note_name(key_info[0])} {key_info[1]}")
        else:
            print(f"Using Key: {get_note_name(key_info[0])} {key_info[1]}")

        if not hasattr(self, 'analyzer'):
             self.analyzer = MidiAnalyzer(midi_data)
        
        analysis = self.analyzer.analyze()
        
        # FIX for missing last beat:
        # pretty_midi.get_beats() sometimes omits the final timestamp if it aligns exactly with end.
        beats = list(self.analyzer.beats)
        if analysis and beats:
             end_time = analysis[-1].note.end
             if beats[-1] < end_time - 0.01:
                 # Estimate beat duration
                 beat_dur = 0.5
                 if len(beats) > 1:
                     beat_dur = beats[-1] - beats[-2]
                 
                 # Append beats until we cover end_time
                 next_beat = beats[-1] + beat_dur
                 while next_beat <= end_time + 0.01:
                     beats.append(next_beat)
                     next_beat += beat_dur

        beat_groups = self.group_by_beat(analysis, beats)

        # --- Generation ---
        required_chords = set(c for c, s in target_combinations)
        beat_events_cache = {} 
        
        for chord_name in required_chords:
            if chord_name not in CHORD_REGISTRY:
                print(f"Warning: Chord '{chord_name}' not found.")
                continue
                
            chord_cls = CHORD_REGISTRY[chord_name]
            chord_strategy = chord_cls()
            
            beat_events = []
            prev_centroid = None 
            
            prev_centroid = None 
            
            # --- Scale Expansion Mode (Modular) ---
            # expansion_iterations will now hold: (degree_idx, target_root, dynamic_chord_name_override)
            # We iterate differently. We need to collect ALL tasks from enabled strategies.
            
            expansion_tasks = []
            
            if expansion_flags:
                # expansion_flags is dict: {'triad': Bool, '7th': Bool, ...}
                
                if expansion_flags.get('triad'):
                    expansion_tasks.extend(self.triad_strat.get_iterations(key_info))
                if expansion_flags.get('7th'):
                    expansion_tasks.extend(self.seventh_strat.get_iterations(key_info))
                if expansion_flags.get('harmonic_minor'):
                    expansion_tasks.extend(self.harmonic_strat.get_iterations(key_info))
                if expansion_flags.get('melodic_minor'):
                    expansion_tasks.extend(self.melodic_strat.get_iterations(key_info))
                if expansion_flags.get('tension'):
                    expansion_tasks.extend(self.tension_strat.get_iterations(key_info))
            
            if not expansion_tasks:
                 # Default Mode: Single pass (dummy task)
                 expansion_tasks.append({'degree': -1, 'root_offset': None, 'chord_name': None})
            
            for task in expansion_tasks:
                # Check for Stop Event
                if stop_event and stop_event.is_set():
                    print("Generation cancelled by user.")
                    return generated_files

                degree_idx = task.get('degree')
                root_offset = task.get('root_offset')
                dynamic_name = task.get('chord_name')
                
                target_root_override = None
                if root_offset is not None:
                    target_root_override = key_info[0] + root_offset

                # Reset beat events for each expansion iteration
                current_loop_beat_events = []
                prev_centroid = None # Reset voicing context
                
                for group in beat_groups:
                    notes = group['notes']
                    if not notes: continue
                    
                    dominant = self.get_dominant_root(notes, group['start'])
                    if not dominant: continue
    
                    if target_root_override is not None:
                        # Override root pitch for Scale Expansion
                        base_octave_val = (dominant.harmonic_pitch // 12) * 12
                        final_root_pitch = base_octave_val + (target_root_override % 12)
                    else:
                        final_root_pitch = dominant.harmonic_pitch
                    
                    root_pitch = final_root_pitch

                    if task.get('chord_intervals'):
                        # Use explicit intervals from Expansion Strategy
                        raw_chord = []
                        for semi in task['chord_intervals']:
                            p = final_root_pitch + semi
                            raw_chord.append(p)
                    else:
                        # Default Strategy Lookup
                        raw_chord = chord_strategy.get_notes(final_root_pitch, key_info)
                    
                    if len(raw_chord) == 3:
                        voiced_chord, new_centroid = self.get_best_voicing(raw_chord, prev_centroid)
                        prev_centroid = new_centroid
                    else:
                        voiced_chord = raw_chord
                    
                    vel = dominant.note.velocity
                    current_loop_beat_events.append({
                        'start': group['start'],
                        'end': group['end'],
                        'chord_notes': voiced_chord,
                        'notes': notes, 
                        'velocity': vel,
                        'root_pitch': root_pitch # Added for extended step logic
                    })
                
                current_merged_events = self.merge_events(current_loop_beat_events)
                
                # Cache Key: 
                # If standard: chord_name
                # If expanded: chord_name + dynamic_name (to avoid collision)
                
                cache_key = chord_name
                if dynamic_name:
                    # e.g. Diatonic_7th_CMaj7
                    # We append dynamic name to differentiate in cache
                    # Or we can append degree if we want distinct files for same chord (e.g. I and V might both be Maj, but we want separate files?)
                    # Yes, keep degree for ordering but use dynamic name for readability
                    cache_key = f"{chord_name}_{degree_idx}_{dynamic_name}"
                    
                beat_events_cache[cache_key] = (current_loop_beat_events, current_merged_events)

        for chord_name, style_name in target_combinations:
            # [TEMPORARY] User requested to only generate Diatonic_7th mixed with Arpeggio styles (Excel or Internal)
            # We exclude non-arp styles like Pad and Rhythm.
            if chord_name != "Diatonic_7th":
                continue
            if style_name in ["Pad", "Rhythm"]:
                continue

            # Handling Expanded Keys in Cache
            
            matching_cache_keys = []
            if expansion_flags:
                 for ck in beat_events_cache.keys():
                     if ck.startswith(f"{chord_name}_"):
                         matching_cache_keys.append(ck)
            else:
                 if chord_name in beat_events_cache:
                     matching_cache_keys.append(chord_name)

            
            for cache_key in matching_cache_keys:
                # Check Stop Event inside inner loop too
                if stop_event and stop_event.is_set():
                    print("Generation cancelled by user.")
                    return generated_files

                if style_name not in STYLE_REGISTRY: 
                    print(f"Warning: Style '{style_name}' not found.")
                    continue
                
                beat_events, merged_events = beat_events_cache[cache_key]
                style_cls = STYLE_REGISTRY[style_name]
                
                try:
                    style_strategy = style_cls()
                except TypeError:
                    if not hasattr(style_strategy, 'apply'):
                        continue
                        
                # [FILTERING] Check Allowed Types (rename_src based)
                # If allowed_types is provided, we check style_strategy.rename_src
                if allowed_types is not None:
                    # Resolve src type
                    src_type = getattr(style_strategy, 'rename_src', 'Default')
                    if src_type is None: src_type = 'Default'
                    if str(src_type) not in allowed_types:
                        # print(f"Skipping {style_name}: Type '{src_type}' not in allowed list.")
                        continue

                # [VALIDATION] Check Voice Count (Optional Strict Mode)
                if strict_validation:
                    # Determine required voices
                    required_voices = 3 # Default (Triad)
                    task_type = task.get('type', '7th') # Default to higher req if unknown? Or check chord name
                    
                    # If standard mode (no expansion flags), task has dummy type but chord_name usually has info
                    if not expansion_flags and "7th" in chord_name:
                        required_voices = 4
                    elif task_type in ['7th', 'HarmonicMinor', 'MelodicMinor']:
                        required_voices = 4
                    elif task_type == 'Triad':
                        required_voices = 3
                    
                    # Check if ExternalStyleStrategy (has .voices dict)
                    if isinstance(style_strategy, ExternalStyleStrategy):
                        voice_count = len(style_strategy.voices)
                        if voice_count < required_voices:
                            display_name = dynamic_name if dynamic_name else chord_name
                            print(f"Skipping {display_name}_{style_name}: Insufficient voices ({voice_count} < {required_voices}) for {task_type}")
                            continue

                new_midi = pretty_midi.PrettyMIDI()
                program = pretty_midi.instrument_name_to_program('Acoustic Grand Piano')
                new_inst = pretty_midi.Instrument(program=program)
                
                if style_name == "Pad":
                    source_events = merged_events
                    use_bass_rhythm = False
                else:
                    source_events = beat_events
                    use_bass_rhythm = True
                
                for event in source_events:
                    start = event['start']
                    end = event['end']
                    chord_notes = event['chord_notes']
                    chord_notes = event['chord_notes']
                    velocity_base = event['velocity']
                    root_pitch = event.get('root_pitch', None) # Get root pitch
                    
                    if use_bass_rhythm:
                        for ana in event['notes']:
                            note = ana.note
                            thinning_active = (style_name == "Rhythm")
                            current_chord = chord_notes
                            if thinning_active:
                                duration = note.end - note.start
                                is_fast = duration < 0.25
                                is_strong = ana.sub_beat_type == '1'
                                if is_fast and not is_strong and len(current_chord) >= 3:
                                    sorted_c = sorted(current_chord)
                                    current_chord = [sorted_c[0], sorted_c[1]]
                            
                            generated = style_strategy.apply(current_chord, note, velocity_scale, midi_data, root_pitch=root_pitch)
                            new_inst.notes.extend(generated)
                    else:
                        dummy_note = pretty_midi.Note(
                            velocity=int(velocity_base),
                            pitch=60, 
                            start=start,
                            end=end
                        )
                        generated = style_strategy.apply(chord_notes, dummy_note, velocity_scale, midi_data, root_pitch=root_pitch)
                        new_inst.notes.extend(generated)
                
                self.humanize(new_inst.notes, timing_jitter=timing_jitter)
                new_midi.instruments.append(new_inst)
                
                # Output Filename Modification for Expansion
                suffix = ""
                chord_name_for_file = chord_name
                
                if expansion_flags:
                    # Extract info from cache_key
                    # Format: {chord_name}_{degree_idx}_{dynamic_name}
                    prefix = f"{chord_name}_"
                    if cache_key.startswith(prefix):
                        remainder = cache_key[len(prefix):]
                        # remainder e.g. "1_CM7"
                        if "_" in remainder:
                             d_idx_str, d_name = remainder.split("_", 1)
                             chord_name_for_file = d_name
                             # Suffix: Keep it empty as requested ("An1_CM7_Style")
                             suffix = "" 
                
                if hasattr(style_strategy, 'rename_src') and style_strategy.rename_src:
                    # Replace 'Bass' with the new value
                    base_name_for_output = original_name.replace("Bass", str(style_strategy.rename_src))
                else:
                    base_name_for_output = original_name

                output_filename = f"{base_name_for_output}_{chord_name_for_file}_{style_name}{suffix}.mid"
                output_path = os.path.join(final_output_dir, output_filename)
                
                try:
                    new_midi.write(output_path)
                    generated_files.append(output_path)
                    print(f"Generated: {output_path}")
                except PermissionError:
                    print(f"Error: Could not write to {output_path}. File might be open in another program (DAW, Player). Skipping.")
                except Exception as e:
                    print(f"Error writing output file {output_path}: {e}")
                
                # --- Metadata Collection ---
                try:
                    # Calculate Bars (Approximate)
                    tempo = get_tempo_at_time(midi_data, 0)
                    duration = new_midi.get_end_time()
                    bars = max(1, int(round(duration / (60.0 / tempo) / 4.0)))
                    
                    root_name = "C"
                    if key_info:
                        root_name = get_note_name(key_info[0])
                    
                    group_val = getattr(style_strategy, 'rename_src', '')
                    if not group_val: group_val = ''
                    
                    meta = {
                        'FileName': output_filename,
                        'FilePath': os.path.abspath(output_path),
                        'Category': output_subdir if output_subdir else "Ensemble",
                        'Instruments': style_name,
                        'Bar': bars,
                        'Chord': chord_name_for_file,
                        'Root': root_name,
                        'Group': str(group_val),
                        'Comment': "Generated by Ver 1.8.1",
                        '_SourceFile': os.path.basename(input_path)
                    }
                    metadata_list.append(meta)
                except Exception as meta_e:
                    print(f"Metadata Warning: {meta_e}")
        # --- Export Auto-Registration Excel ---
        if metadata_list:
            try:
                import pandas as pd
                df = pd.DataFrame(metadata_list)
                # Ensure column order matches MasterLibraly if possible
                cols = ['FileName', 'FilePath', 'Category', 'Instruments', 'Bar', 'Chord', 'Root', 'Group', 'Comment', '_SourceFile']
                # reorder only if columns exist
                final_cols = [c for c in cols if c in df.columns]
                df = df[final_cols]
                
                export_path = os.path.join(final_output_dir, "_Import_Source.xlsx")
                df.to_excel(export_path, index=False)
                print(f"Exported Registration Source: {export_path}")
            except Exception as e:
                print(f"Error exporting Excel report: {e}")

        return generated_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("--velocity_scale", type=float, default=0.9)
    parser.add_argument("--key", default="Auto", help="Key (e.g. 'C Major')")
    parser.add_argument("--chord", default=None, help="Comma-separated chord strategies (e.g. 'Diatonic,Major')")
    parser.add_argument("--style", default=None, help="Comma-separated style strategies (e.g. 'Pad,Arp')")
    parser.add_argument("--preset", default=None, help="Preset name (pop, rock, game, dance, lofi)")
    parser.add_argument("--output", default=None, help="Output subdirectory name")
    parser.add_argument("--expand_scale", action="store_true", help="[EXPERIMENTAL] Generate all scale degrees from input")
    
    args = parser.parse_args()
    
    gen = EnsembleGenerator()
    gen.generate(
        args.input_file, 
        velocity_scale=args.velocity_scale, 
        key_arg=args.key,
        chord_filter=args.chord,
        style_filter=args.style,
        preset_name=args.preset,
        output_subdir=args.output,
        expand_scale=args.expand_scale
    )
