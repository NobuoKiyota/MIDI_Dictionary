import pretty_midi
import random
import os
import pandas as pd
try:
    from .registries import register_style
    # Removed: from base_strategies import StyleStrategy
    from .utils import get_tempo_at_time
except ImportError:
    from registries import register_style
    # Removed: from base_strategies import StyleStrategy
    from utils import get_tempo_at_time

# New StyleStrategy base class definition
# New StyleStrategy base class definition
class StyleStrategy:
    def apply(self, chord_notes, bass_note, velocity_scale=1.0, midi_data=None, root_pitch=None):
        raise NotImplementedError

# --- Extended Step Logic Constants ---
INTERVAL_RULES = {
    "Major": [4, 3, 5],
    "Minor": [3, 4, 5],
    "M7": [4, 3, 4, 1],
    "m7": [3, 4, 3, 2],
    "7th": [4, 3, 3, 2],
    "dim": [3, 3, 3, 3],
    "aug": [4, 4, 4],
    "Default": [4, 3, 5],
    # Tension Rules (5-step cycle summing to 12 or handling wrap)
    # M9: R, 3, 5, 7, 9 (0, 4, 7, 11, 14). Wrap 14->12 is -2.
    "M9": [4, 3, 4, 3, -2],
    # m9: R, b3, 5, b7, 9 (0, 3, 7, 10, 14). Wrap 14->12 is -2.
    "m9": [3, 4, 3, 4, -2],
    # 9: R, 3, 5, b7, 9 (0, 4, 7, 10, 14). Wrap 14->12 is -2.
    "9": [4, 3, 3, 4, -2],
    # m11: R, b3, 5, b7, 11 (0, 3, 7, 10, 17). Wrap 17->12 is -5.
    "m11": [3, 4, 3, 7, -5],
    # m7b5(11): R, b3, b5, b7, 11 (0, 3, 6, 10, 17). Wrap 17->12 is -5.
    "m7b5(11)": [3, 3, 4, 7, -5],
    # 7(b9): R, 3, 5, b7, b9 (0, 4, 7, 10, 13). Wrap 13->12 is -1.
    "7(b9)": [4, 3, 3, 3, -1],
    # M7(11)? Usually lydian #11 (18). 
    # M7(#11): 0, 4, 7, 11, 18. Wrap 18->12 is -6.
    "M7(#11)": [4, 3, 4, 7, -6] 
}

class ExternalStyleStrategy(StyleStrategy):
    """
    Unified Style Strategy defined by external Excel data (Row based).
    Supports multiple voices (layers) and extended step lengths (32+).
    """
    def __init__(self, voices_data):
        # voices_data is a list of dicts: {'voice': 1, 'type': 'seq', 'data': [...], 'swing': 0.0} ...
        # We need to organize by voice index for playback
        self.voices = {}
        for row in voices_data:
            v_idx = row['voice']
            if v_idx not in self.voices:
                self.voices[v_idx] = {'seq': [], 'gate': [], 'vel': [], 'swing': 0.0}
            
            # Store rename_src if present (once is enough)
            if row.get('rename_src') and not hasattr(self, 'rename_src'):
                self.rename_src = row['rename_src']
            
            p_type = row['type']
            if p_type == 'seq':
                self.voices[v_idx]['seq'] = row['data']
                self.voices[v_idx]['swing'] = row['swing']
            elif p_type == 'gate':
                self.voices[v_idx]['gate'] = row['data']
            elif p_type == 'vel':
                self.voices[v_idx]['vel'] = row['data']

    def _detect_chord_type(self, chord_notes, root_pitch):
        if not chord_notes or not root_pitch: return "Default"
        intervals = sorted([ (p - root_pitch) % 12 for p in chord_notes ])
        # Also include extended intervals (14, 17 etc mod 12 are 2, 5) 
        # But 'intervals' are mod 12. So 9th is 2. 11th is 5.
        s_int = set(intervals)
        
        # 5-Note Checks (Prioritize)
        # M9: 0, 4, 7, 11, 2
        if {0, 4, 7, 11, 2}.issubset(s_int): return "M9"
        # m9: 0, 3, 7, 10, 2
        if {0, 3, 7, 10, 2}.issubset(s_int): return "m9"
        # 9: 0, 4, 7, 10, 2
        if {0, 4, 7, 10, 2}.issubset(s_int): return "9"
        # 7(b9): 0, 4, 7, 10, 1
        if {0, 4, 7, 10, 1}.issubset(s_int): return "7(b9)"
        # m11 (assuming 9 omit? or just 11 present? 11 is 5 semitones)
        # m11 def: 0, 3, 7, 10, 5
        if {0, 3, 7, 10, 5}.issubset(s_int): return "m11"
        # m7b5(11): 0, 3, 6, 10, 5
        if {0, 3, 6, 10, 5}.issubset(s_int): return "m7b5(11)"

        # 4-Note Checks
        if {0, 4, 7, 11}.issubset(s_int): return "M7"
        if {0, 3, 7, 10}.issubset(s_int): return "m7"
        if {0, 4, 7, 10}.issubset(s_int): return "7th"
        if {0, 3, 6}.issubset(s_int): return "dim"
        if {0, 4, 8}.issubset(s_int): return "aug"
        if {0, 3, 7}.issubset(s_int): return "Minor"
        if {0, 4, 7}.issubset(s_int): return "Major"
        return "Default"

    def _get_pitch_from_step(self, step_val, root_pitch, chord_type):
        if root_pitch is None: return 60 
        rule = INTERVAL_RULES.get(chord_type, INTERVAL_RULES["Default"])
        current_pitch = root_pitch + 12
        steps_remaining = step_val
        idx = 0
        while steps_remaining > 0:
            interval = rule[idx % len(rule)]
            current_pitch += interval
            steps_remaining -= 1
            idx += 1
        return current_pitch

    def apply(self, chord_notes, bass_note, velocity_scale=1.0, midi_data=None, root_pitch=None):
        if not chord_notes: return []
        
        all_notes = []
        base_start = bass_note.start
        end = bass_note.end
        
        bpm = 120.0
        if midi_data:
            bpm = get_tempo_at_time(midi_data, base_start)
        
        beat_dur = 60.0 / bpm
        step_dur = beat_dur / 4.0 # 16th note
        
        global_step_offset = int(round(base_start / step_dur))
        loop_steps = int((end - base_start) / step_dur) + 2
        
        chord_type = self._detect_chord_type(chord_notes, root_pitch)

        # Iterate through VOICES
        for v_idx, voice_data in self.voices.items():
            sequence = voice_data['seq']
            gate_data = voice_data['gate']
            vel_data = voice_data['vel']
            swing_amount = voice_data['swing']
            
            # Safety check for lengths
            seq_len = len(sequence)
            if seq_len == 0: continue

            for i in range(loop_steps):
                abs_step_idx = global_step_offset + i
                grid_onset = abs_step_idx * step_dur
                
                if grid_onset < base_start - 0.01: continue
                if grid_onset >= end - 0.01: break
                
                # Sequence Lookup (Modulo Length)
                seq_idx = abs_step_idx % seq_len
                
                # Safe Access
                seq_val_str = sequence[seq_idx] if seq_idx < len(sequence) else '-1'
                
                # Gate & Vel
                # Note: Excel inputs 10 -> 1.0. We divide by 10.0 here or in loader?
                # Let's do it in Loader for consistency. Assuming data is already scaled in Loader.
                gate = gate_data[seq_idx] if seq_idx < len(gate_data) else 1.0
                vel_mult = vel_data[seq_idx] if seq_idx < len(vel_data) else 1.0
                
                timing_offset = 0.0
                if (abs_step_idx % 2) == 1: 
                    # Interpret swing as ratio of step_dur (e.g. 0.3 => 30% delay)
                    # Previous: timing_offset += swing_amount (treated as seconds, caused massive lag)
                    timing_offset += swing_amount * step_dur

                if str(seq_val_str) != '-1' and str(seq_val_str) != '':
                    if True: 
                         print(f"DEBUG: V{v_idx} Step {abs_step_idx} | Seq:'{seq_val_str}' G:{gate:.2f}")

                    val_clean = str(seq_val_str).replace('&', ',').replace('+', ',').replace(' ', ',')
                    indices = [s.strip() for s in val_clean.split(',') if s.strip()]
                    
                    strum_idx = 0
                    for idx_str in indices:
                        try:
                            idx_val = int(float(idx_str)) 
                            final_pitch = self._get_pitch_from_step(idx_val, root_pitch, chord_type)
                            
                            strum_delay = strum_idx * 0.005
                            onset = grid_onset + timing_offset + strum_delay
                            
                            if onset < end:
                                duration = step_dur * gate
                                note_end = onset + duration 
                                
                                if duration > 0.001:
                                    vel = bass_note.velocity * velocity_scale * vel_mult
                                    vel = max(1, min(127, int(vel)))
                                    
                                    all_notes.append(pretty_midi.Note(
                                        velocity=vel,
                                        pitch=final_pitch,
                                        start=onset,
                                        end=note_end
                                    ))
                            strum_idx += 1
                        except ValueError:
                            pass
                            
        return all_notes

def load_style_catalog(file_path="ensemble_styles.xlsx"):
    if not os.path.exists(file_path):
        print(f"Warning: Style catalog not found at {file_path}")
        return {}
    
    try:
        try:
            df = pd.read_excel(file_path, sheet_name='Patterns')
        except:
            df = pd.read_excel(file_path, sheet_name=0)

        df.columns = df.columns.str.strip()
        catalog = {}
        
        # New Schema: style_name, voice, type, 01..32, swing
        # We need to iterate and group.
        
        for index, row in df.iterrows():
            try:
                name = row['style_name']
                if pd.isna(name): continue
                
                voice = int(row.get('voice', 1))
                p_type = row.get('type', 'seq')
                swing = float(row.get('swing', 0.0)) if not pd.isna(row.get('swing')) else 0.0
                rename_val = row.get('rename_src', None)
                if pd.isna(rename_val): rename_val = None
                
                # Extract 01..128 (8 bars)
                data_list = []
                # Support up to 128 steps (8 bars)
                # Robust Column Lookup: Check "01", "1", 1
                for i in range(1, 129):
                    val = None
                    found = False
                    
                    # Try keys
                    possible_keys = [f"{i:02}", str(i), i]
                    for key in possible_keys:
                         if key in df.columns:
                             val = row[key]
                             found = True
                             break
                    
                    if found:
                        # Process value based on type
                        if pd.isna(val) or val == '':
                            if p_type == 'seq': val = '-1'
                            else: val = 10 # Default for gate/vel
                        
                        if p_type == 'seq':
                            data_list.append(str(val))
                        else:
                            # Scale Gate/Vel by 10.0
                            try:
                                data_list.append(float(val) / 10.0)
                            except:
                                data_list.append(1.0)
                    else:
                        # If a column in the middle is missing, should we consistency break?
                        # Usually patterns are contiguous. If "17" is missing, we stop.
                        break 

                
                row_data = {
                    'style_name': name,
                    'voice': voice,
                    'type': p_type,
                    'data': data_list,
                    'swing': swing,
                    'rename_src': rename_val
                }
                
                if name not in catalog:
                    catalog[name] = []
                catalog[name].append(row_data)
                
            except Exception as e:
                print(f"Error parsing row {index}: {e}")
                continue
                
        return catalog
    except Exception as e:
        print(f"Critical Error loading style catalog: {e}")
        return {}
