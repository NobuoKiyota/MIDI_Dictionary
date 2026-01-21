import pretty_midi
import numpy as np
import collections

class MidiAnalyzer:
    def __init__(self):
        self.PITCH_CLASSES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    def analyze(self, file_path):
        try:
            pm = pretty_midi.PrettyMIDI(file_path)
            
            # Combine all instruments for general analysis, or pick the first active one?
            # Usually these are single track MIDIs, but let's aggregate notes.
            all_notes = []
            for instrument in pm.instruments:
                if not instrument.is_drum:
                    all_notes.extend(instrument.notes)
            
            if not all_notes:
                return self._empty_result()
                
            all_notes.sort(key=lambda x: x.start)
            
            # 1. Base Metrics
            result = {}
            
            # Time Signature (Infer from MIDI or default 4/4)
            ts = self._detect_time_signature(pm)
            result['time_signature'] = f"{ts.numerator}/{ts.denominator}"
            result['time_signature_obj'] = ts
            
            # Tempo
            tempo_changes = pm.get_tempo_changes()
            if len(tempo_changes[0]) > 0:
                 tempo = tempo_changes[1][0]
            else:
                try:
                    tempo = pm.estimate_tempo()
                    if not tempo: raise ValueError("No tempo")
                except:
                    tempo = 120.0
            
            result['tempo'] = int(tempo)
            
            # Duration in bar
            beat_length = 60.0 / result['tempo']
            bar_length = beat_length * ts.numerator # Assuming denominator 4 roughly for duration calc
            total_time = all_notes[-1].end
            duration_bars = max(1, round(total_time / bar_length))
            result['duration_bars'] = float(f"{duration_bars:.1f}") 
            # Reformat to match user example "4.4"? 
            # User said "4.4". If it meant 4/4 4 bars, maybe "Bars.TS"? 
            # But let's stick to "Bars" for now, or just integer if cleaner.
            # Actually, let's just use the int duration_bars.
            result['duration_bars'] = int(duration_bars)

            # 2. Key & Root Detection
            key_info = self._detect_key(all_notes)
            result['root'] = key_info['root']
            result['scale'] = key_info['scale'] # Major/Minor
            
            # 3. Chord Detection
            chord_info = self._detect_chord(all_notes, key_info['root'])
            result['chord'] = chord_info['chord_name']
            result['chord_detail'] = chord_info # Store full info if needed

            # 4. Rhythm/Groove Detection
            rhythm_info = self._detect_rhythm(all_notes, result['tempo'], ts)
            result['beat_type'] = rhythm_info['beat_type'] # 8beat, 16beat
            result['groove'] = rhythm_info['groove'] # Straight, Swing, Dotted
            
            # 5. Style Detection
            style = self._detect_style(all_notes, pm.instruments)
            result['style'] = style
            
            # 6. Generate Comment String
            # Format: "Inst_Chord_Bars_Beat_Groove_Style"
            comment_parts = []
            
            # Chord
            if result['chord']:
                comment_parts.append(result['chord'])
            
            # Duration.User example: "4.4".
            # If duration is 4 bars and TS 4/4 -> "4.4"
            # If duration is 2 bars and TS 4/4 -> "2.4"?
            comment_parts.append(f"{result['duration_bars']}.{ts.numerator}")
            
            # Beat
            comment_parts.append(result['beat_type'])
            
            # Groove
            if result['groove'] and result['groove'] != "Straight":
                 comment_parts.append(result['groove'])
                 
            # Style
            if result['style']:
                comment_parts.append(result['style'])
                
            result['comment_suffix'] = "_".join(comment_parts)
            
            return result
            
        except Exception as e:
            print(f"Analysis Error: {e}")
            return self._empty_result()

    def _empty_result(self):
        return {
            'time_signature': '4/4',
            'duration_bars': 4,
            'root': 'C',
            'chord': '',
            'beat_type': '8beat',
            'groove': '',
            'style': '',
            'comment_suffix': '',
            'tempo': 120
        }
        
    def _detect_time_signature(self, pm):
        if pm.time_signature_changes:
            return pm.time_signature_changes[0]
        return pretty_midi.TimeSignature(4, 4, 0)

    def _detect_key(self, notes):
        # Krumhansl-Schmuckler algorithm simplified or just weighted pitch count
        # Simple weighted count: Duration * Velocity
        scores = collections.defaultdict(float)
        
        for note in notes:
            # Weighted by duration
            duration = note.end - note.start
            pc = note.pitch % 12
            scores[pc] += duration
            
        if not scores:
            return {'root': 'C', 'scale': 'Major'}
            
        # Find max
        root_pc = max(scores, key=scores.get)
        root_name = self.PITCH_CLASSES[root_pc]
        
        # Determine Major/Minor?
        # Check for Minor 3rd vs Major 3rd
        m3 = scores.get((root_pc + 3) % 12, 0)
        M3 = scores.get((root_pc + 4) % 12, 0)
        
        scale = "Major" if M3 >= m3 else "minor"
        
        return {'root': root_name, 'scale': scale}

    def _detect_chord(self, notes, inferred_root_name):
        # Flatten all pitches
        pitches = set(note.pitch % 12 for note in notes)
        
        # Simple interval matching against the Inferred Root?
        # Or find the bass note first?
        if not notes:
             return {'chord_name': ''}
             
        # Find Bass Note (lowest pitch)
        sorted_by_pitch = sorted(notes, key=lambda n: n.pitch)
        bass_pc = sorted_by_pitch[0].pitch % 12
        bass_name = self.PITCH_CLASSES[bass_pc]
        
        # Calculate intervals from bass
        intervals = set((p - bass_pc) % 12 for p in pitches)
        
        # Definitions (Simplified)
        chord_type = ""
        
        # 3rds
        has_m3 = 3 in intervals
        has_M3 = 4 in intervals
        
        # 5ths
        has_P5 = 7 in intervals
        has_d5 = 6 in intervals
        has_A5 = 8 in intervals
        
        # 7ths
        has_m7 = 10 in intervals
        has_M7 = 11 in intervals
        
        # Logic
        root = bass_name
        
        # Triad
        if has_M3:
            chord_type = "" # Major
            if has_m7:
                chord_type = "7"
            elif has_M7:
                chord_type = "M7"
        elif has_m3:
            chord_type = "m"
            if has_m7:
                chord_type = "m7"
            elif has_M7:
                chord_type = "mM7"
        else:
            # Power chord or Suspended?
            if has_P5:
               if 2 in intervals: # sus2
                   chord_type = "sus2"
               elif 5 in intervals: # sus4
                   chord_type = "sus4"
               else:
                   chord_type = "5" # Power
        
        # Extensions (9, 11, 13) - simplified checking high intervals not mod 12 if possible,
        # but here we only have PC.
        # Check standard tensions if 7th exists
        if "7" in chord_type:
            if 2 in intervals: # 9th
                chord_type = chord_type.replace("7", "9")
        
        # Diminished / Augmented
        if has_m3 and has_d5:
            chord_type = "dim"
        if has_M3 and has_A5:
            chord_type = "aug"

        return {'chord_name': f"{root}{chord_type}"}

    def _detect_rhythm(self, notes, tempo, ts):
        if not notes:
            return {'beat_type': '8beat', 'groove': 'Straight'}
            
        # Calculate approximate grid
        seconds_per_beat = 60.0 / tempo
        seconds_per_16th = seconds_per_beat / 4.0
        
        # Analyze start times modulo 16th note grid
        on_8th = 0
        on_16th = 0
        
        # Triplet / Groove Counters
        # Only count notes that are OFF-BEAT for groove detection bias
        # to avoid "Shuffle" false positives on straight quarter notes.
        is_triplet = 0
        groove_relevant_notes = 1
        
        for note in notes:
            start = note.start
            
            # Check 16th grid
            grid_pos = start / seconds_per_16th
            grid_idx = round(grid_pos)
            
            # Beat Grid position (0, 1, 2...)
            beat_pos = start / seconds_per_beat
            dist_from_beat = abs(beat_pos - round(beat_pos))
            is_on_beat = dist_from_beat < 0.1
            
            if not is_on_beat:
                groove_relevant_notes += 1
                
                # Check Triplet (1/3 of beat)
                # 3 notes per beat. 
                # positions: 0, 0.33, 0.66
                triplet_pos = start / (seconds_per_beat / 3.0)
                triplet_dev = abs(triplet_pos - round(triplet_pos))
                
                if triplet_dev < 0.1: 
                    is_triplet += 1

            # Beat Type Rhythm Check (Use all notes)
            # Check if it aligns with 16th grid (odd indices)
            # Even indices: 0 (beat), 2 (8th), 4 (beat), 6 (8th)...
            if grid_idx % 2 != 0:
                on_16th += 1
            else:
                on_8th += 1
                
        # Beat Type
        # If we have significant 16th note content
        beat_type = "16beat" if on_16th > (len(notes) * 0.05) else "8beat"
        
        # Groove
        groove = "Straight"
        
        # Swing Detection
        if groove_relevant_notes > 0:
            if (is_triplet / groove_relevant_notes) > 0.5:
                 groove = "Shuffle" 
        
        # Dotted Detection
        dotted_count = 0
        for note in notes:
            dur = note.end - note.start
            beats = dur / seconds_per_beat
            rem = beats % 1.0
            
            # Dotted 8th (0.75)
            if 0.70 < rem < 0.80: 
                dotted_count += 1
            # Dotted Quarter (1.5)
            if 0.45 < (beats % 1.0) < 0.55 and beats > 1.0:
                 dotted_count += 1
                
        if dotted_count > len(notes) * 0.15: 
            groove = "dot" 
            
        return {'beat_type': beat_type, 'groove': groove}

    def _detect_style(self, notes, instruments):
        # Logic to guess performance style
        style = []
        
        # 1. Octave Bass
        # Check if notes alternate consistently by Octave
        if self._is_octave_pattern(notes):
            style.append("Oct")
            
        # 2. Arpeggio vs Block
        # Check overlaps
        simultaneous_notes = 0
        total_checks = 0
        for i in range(len(notes)-1):
            if notes[i].end > notes[i+1].start + 0.05: # Overlap
                simultaneous_notes += 1
            total_checks += 1
            
        if total_checks > 0:
            overlap_ratio = simultaneous_notes / total_checks
            if overlap_ratio > 0.6:
                style.append("Chord") # Block chords
            elif overlap_ratio < 0.2:
                 # Check if intervals are wide -> Arp
                 style.append("Arp") # Likely Arpeggio
                 
        # 3. Figuration (Busy, fast moving melodic line?)
        # High note density
        avg_duration = np.mean([n.end - n.start for n in notes]) if notes else 0
        if avg_duration < 0.2: # Very short notes
            style.append("Figuration")
            
        return "_".join(style) if style else ""

    def _is_octave_pattern(self, notes):
        if len(notes) < 4: return False
        
        octave_jumps = 0
        for i in range(len(notes)-1):
            interval = abs(notes[i].pitch - notes[i+1].pitch)
            if interval == 12:
                octave_jumps += 1
                
        return octave_jumps > (len(notes) * 0.4)
