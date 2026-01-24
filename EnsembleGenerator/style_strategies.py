import pretty_midi
import random
import os
import pandas as pd
from registries import register_style
from base_strategies import StyleStrategy
from utils import get_tempo_at_time

@register_style("Pad")
class PadStyle(StyleStrategy):
    def apply(self, chord_notes, bass_note, velocity_scale=1.0, midi_data=None):
        notes = []
        vel = int(bass_note.velocity * velocity_scale)
        vel = max(0, min(127, vel))
        for pitch in chord_notes:
            notes.append(pretty_midi.Note(
                velocity=vel,
                pitch=pitch,
                start=bass_note.start,
                end=bass_note.end
            ))
        return notes

@register_style("Rhythm")
class RhythmStyle(StyleStrategy):
    def apply(self, chord_notes, bass_note, velocity_scale=1.0, midi_data=None):
        if bass_note.velocity < 100:
            return []
        
        notes = []
        vel = int(bass_note.velocity * velocity_scale)
        vel = max(0, min(127, vel))
        for pitch in chord_notes:
            notes.append(pretty_midi.Note(
                velocity=vel,
                pitch=pitch,
                start=bass_note.start,
                end=bass_note.end
            ))
        return notes

class BaseArpStyle(StyleStrategy):
    """
    Base class for Arpeggiators with dynamic patterns and timing.
    """
    def get_pattern(self):
        return [0, 1, 2] # Default Up
        
    def get_gate_ratio(self):
        return 1.0 # 100% Legato
        
    def get_timing_offset(self):
        return 0.0 # Seconds
    
    def get_velocity(self, base_vel, beat_position, note_index):
        return base_vel
        
    def apply(self, chord_notes, bass_note, velocity_scale=1.0, midi_data=None):
        notes = []
        base_vel = int(bass_note.velocity * velocity_scale)
        base_vel = max(0, min(127, base_vel))
        
        start = bass_note.start
        end = bass_note.end
        current_time = start
        
        pattern = self.get_pattern()
        idx = 0
        
        while current_time < end:
            # 1. Tempo Sync
            bpm = 120.0
            if midi_data:
                bpm = get_tempo_at_time(midi_data, current_time)
            
            beat_dur = 60.0 / bpm
            step_dur = beat_dur / 4.0 # 16th note
            
            # 2. Garbage Check
            remaining = end - current_time
            if remaining < step_dur * 0.5:
                break
                
            # 3. Determine Pitch using Pattern
            # Wrap pattern index
            pat_idx = idx % len(pattern)
            # Wrap chord note index
            note_idx = pattern[pat_idx] % len(chord_notes) 
            pitch = chord_notes[note_idx]
            
            # 4. Calculate Timing with Offset
            onset = current_time + self.get_timing_offset()
            if onset >= end: break # Offset pushed out of bounds
            
            # 5. Calculate Duration with Gate
            gate = self.get_gate_ratio()
            duration = step_dur * gate
            note_end = min(onset + duration, end)
            
            if note_end - onset > 0.01:
                # 6. Calculate Velocity
                vel = self.get_velocity(base_vel, idx % 4, note_idx)
                vel = max(1, min(127, int(vel)))
                
                notes.append(pretty_midi.Note(
                    velocity=vel,
                    pitch=pitch,
                    start=onset,
                    end=note_end
                ))
            
            current_time += step_dur
            idx += 1
            
        return notes

@register_style("Arp") # Legacy Simple Up (Default)
class SimpleArpStyle(BaseArpStyle):
    pass

@register_style("Arp_Trance")
class TranceArpStyle(BaseArpStyle):
    def get_pattern(self):
        # Up-Down-Up 8-step: 0 1 2 1 0 1 2 3 (requires 4 notes)
        return [0, 1, 2, 1, 0, 1, 2, 3] 
        
    def get_gate_ratio(self):
        return 0.6 # Staccato
        
    def get_velocity(self, base_vel, beat_step, note_index):
        if beat_step == 2:
            return base_vel * 1.2
        return base_vel

@register_style("Arp_LoFi")
class LoFiArpStyle(BaseArpStyle):
    def get_pattern(self):
        return [0, 2, 3, 1]
        
    def get_gate_ratio(self):
        return 0.95
        
    def get_timing_offset(self):
        return random.uniform(0.03, 0.05)
        
    def get_velocity(self, base_vel, beat_step, note_index):
        return base_vel * 0.7

@register_style("Arp_Healing")
class HealingArpStyle(BaseArpStyle):
    def get_pattern(self):
        return [0, 1, 2] 
        
    def get_gate_ratio(self):
        return 2.0 # Overlap/Pedal
        
    def get_velocity(self, base_vel, beat_step, note_index):
        return base_vel * 0.8

class ExternalArpStyle(BaseArpStyle):
    """
    Arpeggiator style defined by external Excel data (Column based).
    """
    def __init__(self, data):
        self.data = data
        super().__init__()

    def apply(self, chord_notes, bass_note, velocity_scale=1.0, midi_data=None):
        if not chord_notes: return []
        
        notes = []
        base_start = bass_note.start
        end = bass_note.end
        current_time = base_start
        
        sequence = self.data['sequence']
        gate_ratios = self.data['gate_ratios']
        velocity_mults = self.data['velocity_mults']
        swing_amount = self.data['swing']
        
        step_idx = 0
        
        while current_time < end:
            # 1. Sync Tempo
            bpm = 120.0
            if midi_data:
                bpm = get_tempo_at_time(midi_data, current_time)
            
            beat_dur = 60.0 / bpm
            step_dur = beat_dur / 4.0 # 16th note
            
            # 2. Garbage Check
            remaining = end - current_time
            if remaining < step_dur * 0.5:
                break
                
            # 3. Get Pattern Step Data
            seq_val_str = sequence[step_idx % 16]
            gate = gate_ratios[step_idx % 16]
            vel_mult = velocity_mults[step_idx % 16]
            
            timing_offset = 0.0
            if (step_idx % 2) == 1: 
                timing_offset += swing_amount

            # 4. Parse Sequence & Generate
            if str(seq_val_str) != '-1' and str(seq_val_str) != '':
                val_clean = str(seq_val_str).replace('&', ',').replace('+', ',').replace(' ', ',')
                indices = [s.strip() for s in val_clean.split(',') if s.strip()]
                
                strum_idx = 0
                for idx_str in indices:
                    try:
                        idx_val = int(float(idx_str)) 
                        
                        # Octave Wrapping
                        num_notes = len(chord_notes)
                        note_idx = idx_val % num_notes
                        octave_shift = idx_val // num_notes
                        
                        base_pitch = chord_notes[note_idx]
                        final_pitch = base_pitch + (octave_shift * 12)
                        
                        strum_delay = strum_idx * 0.005
                        onset = current_time + timing_offset + strum_delay
                        
                        if onset < end:
                            duration = step_dur * gate
                            note_end = min(onset + duration, end)
                            
                            if note_end - onset > 0.01:
                                vel = bass_note.velocity * velocity_scale * vel_mult
                                vel = max(1, min(127, int(vel)))
                                
                                notes.append(pretty_midi.Note(
                                    velocity=vel,
                                    pitch=final_pitch,
                                    start=onset,
                                    end=note_end
                                ))
                        strum_idx += 1
                    except ValueError:
                        pass
            
            current_time += step_dur
            step_idx += 1
            
        return notes

def load_arp_catalog(file_path="arpeggio_patterns.xlsx"):
    if not os.path.exists(file_path):
        print(f"Warning: Arpeggio catalog not found at {file_path}")
        return {}
    
    try:
        try:
            df = pd.read_excel(file_path, sheet_name='Patterns')
        except:
            df = pd.read_excel(file_path, sheet_name=0)

        df.columns = df.columns.str.strip()
        catalog = {}
        
        for index, row in df.iterrows():
            try:
                name = row['style_name']
                if pd.isna(name): continue

                swing = float(row.get('swing', 0.0)) if not pd.isna(row.get('swing')) else 0.0
                
                sequence = []
                gate_ratios = []
                velocity_mults = []
                
                for i in range(1, 17):
                    s_key = f"s{i:02}"
                    g_key = f"g{i:02}"
                    v_key = f"v{i:02}"
                    
                    # Sequence
                    val_s = row.get(s_key, 'r')
                    s_str = str(val_s).strip().lower()
                    if s_str == 'r' or s_str == '-1' or s_str == '' or s_str == 'nan':
                        final_s = '-1'
                    else:
                        final_s = s_str
                    sequence.append(final_s)
                    
                    # Gate
                    try:
                        val_g = row.get(g_key, 10)
                        if pd.isna(val_g): val_g = 10
                        gate_ratios.append(float(val_g) / 10.0)
                    except ValueError:
                        print(f"Warning: Invalid Gate at {name} col {g_key}. Defaulting to 1.0")
                        gate_ratios.append(1.0)
                    
                    # Velocity
                    try:
                        val_v = row.get(v_key, 10)
                        if pd.isna(val_v): val_v = 10
                        velocity_mults.append(float(val_v) / 10.0)
                    except ValueError:
                        print(f"Warning: Invalid Velocity at {name} col {v_key}. Defaulting to 1.0")
                        velocity_mults.append(1.0)
                    
                catalog[name] = {
                    'sequence': sequence,
                    'gate_ratios': gate_ratios,
                    'velocity_mults': velocity_mults,
                    'swing': swing
                }
            except Exception as e:
                print(f"Error parsing row {index} ({row.get('style_name', 'Unknown')}): {e}")
                continue
                
        return catalog
    except Exception as e:
        print(f"Critical Error loading arpeggio catalog: {e}")
        return {}
