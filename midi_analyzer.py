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
            style_data = self._detect_style(all_notes, pm.instruments)
            result['style'] = style_data['style']
            result['style_features'] = style_data['features']
            
            # 6. Generate Comment String
            # Format: "Inst_Chord_Bars_Beat_Groove_Style"
            comment_parts = []
            
            # Chord
            if result['chord']:
                comment_parts.append(result['chord'])
            
            # Duration.User example: "4.4".
            # If duration is 4 bars and TS 4/4 -> "4.4"
            # If duration is 2 bars and TS 4/4 -> "2.4"?
            dur_str = f"{result['duration_bars']}.{ts.numerator}"
            # User request: Omit if "4.4" (Default)
            if dur_str != "4.4":
                comment_parts.append(dur_str)
            
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
            'style_features': {},
            'comment_suffix': '',
            'tempo': 120
        }
        
    def _detect_time_signature(self, pm):
        if pm.time_signature_changes:
            return pm.time_signature_changes[0]
        return pretty_midi.TimeSignature(4, 4, 0)

    def _detect_key(self, notes):
        # Krumhansl-Schmuckler Key Finding Algorithm
        if not notes:
            return {'root': 'C', 'scale': 'Major'}

        # 1. Calculate Chroma Vector (Weighted by duration)
        chroma_vector = [0] * 12
        total_duration = 0
        
        for note in notes:
            dur = note.end - note.start
            pc = note.pitch % 12
            chroma_vector[pc] += dur
            total_duration += dur
            
        if total_duration == 0:
            return {'root': 'C', 'scale': 'Major'}
            
        # Normalize
        chroma_vector = [x / total_duration for x in chroma_vector]

        # 2. Key Profiles (Krumhansl-Schmuckler)
        # Major profile
        major_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        # Minor profile
        minor_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
        
        # Normalize profiles for correlation
        major_mean = np.mean(major_profile)
        major_std = np.std(major_profile)
        major_norm = [(x - major_mean) / major_std for x in major_profile]
        
        minor_mean = np.mean(minor_profile)
        minor_std = np.std(minor_profile)
        minor_norm = [(x - minor_mean) / minor_std for x in minor_profile]
        
        # Normalize chroma
        chroma_mean = np.mean(chroma_vector)
        chroma_std = np.std(chroma_vector)
        if chroma_std == 0:
             return {'root': self.PITCH_CLASSES[chroma_vector.index(max(chroma_vector))], 'scale': 'Major'} # Fallback
             
        chroma_norm = [(x - chroma_mean) / chroma_std for x in chroma_vector]

        # 3. Calculate Correlations
        best_score = -2.0
        best_key = ("C", "Major")
        
        for i in range(12):
            # Test Major
            # Rotate chroma to match root i
            rotated_chroma = chroma_norm[i:] + chroma_norm[:i]
            corr_major = np.corrcoef(rotated_chroma, major_norm)[0][1]
            
            if corr_major > best_score:
                best_score = corr_major
                best_key = (self.PITCH_CLASSES[i], "Major")
                
            # Test Minor
            corr_minor = np.corrcoef(rotated_chroma, minor_norm)[0][1]
            
            if corr_minor > best_score:
                best_score = corr_minor
                best_key = (self.PITCH_CLASSES[i], "Minor")
                
        return {'root': best_key[0], 'scale': best_key[1]}

    def _detect_chord(self, notes, inferred_root_name):
        # Keep existing simplified Logic for now, but ensure it handles empty input
        if not notes:
             return {'chord_name': ''}
             
        # Find Bass Note (lowest pitch)
        sorted_by_pitch = sorted(notes, key=lambda n: n.pitch)
        bass_pc = sorted_by_pitch[0].pitch % 12
        bass_name = self.PITCH_CLASSES[bass_pc]
        
        pitches = set(note.pitch % 12 for note in notes)
        intervals = set((p - bass_pc) % 12 for p in pitches)
        
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
            if has_P5:
               if 2 in intervals:
                   chord_type = "sus2"
               elif 5 in intervals:
                   chord_type = "sus4"
               else:
                   chord_type = "5"
        
        if "7" in chord_type:
            if 2 in intervals: 
                chord_type = chord_type.replace("7", "9")
        
        if has_m3 and has_d5 and not has_P5:
            chord_type = "dim"
        if has_M3 and has_A5 and not has_P5:
            chord_type = "aug"

        return {'chord_name': f"{root}{chord_type}"}

    def _detect_rhythm(self, notes, tempo, ts):
        if not notes:
            return {'beat_type': '8beat', 'groove': 'Straight'}
            
        seconds_per_beat = 60.0 / tempo
        seconds_per_16th = seconds_per_beat / 4.0
        
        on_16th = 0
        
        # Groove Detection
        # Check swing ratio
        
        # Calculate offset from straight 8th grid
        # 8th note grid: 0, 0.5, 1.0, 1.5... beats
        
        swing_candidates = []
        
        for note in notes:
            start_beat = note.start / seconds_per_beat
            
            # Check 16th content
            grid_16th_pos = note.start / seconds_per_16th
            if abs(grid_16th_pos - round(grid_16th_pos)) < 0.15:
                if round(grid_16th_pos) % 2 != 0:
                    on_16th += 1
            
            # Check Swing
            # Look at notes around the "and" of the beat (x.5)
            # If they are delayed to ~x.66 -> Triplet/Swing 
            beat_fraction = start_beat % 1.0
            if 0.4 < beat_fraction < 0.8: # "Backbeat" area
                swing_candidates.append(beat_fraction)

        # Beat Type
        beat_type = "16beat" if on_16th > (len(notes) * 0.1) else "8beat"
        
        # Groove
        groove = "Straight"
        if swing_candidates:
            avg_offbeat = np.mean(swing_candidates)
            if 0.60 < avg_offbeat < 0.72: # ~2/3
                groove = "Shuffle"
            elif 0.72 <= avg_offbeat: # Hard swing or dotted
                 groove = "dot" # Dotted 8th feel
            elif 0.53 < avg_offbeat <= 0.60:
                 groove = "Swing" # Light swing
                 
        return {'beat_type': beat_type, 'groove': groove}

    def _detect_style(self, notes, instruments):
        # Result Dictionary
        features = {}
        style = []
        
        if len(notes) < 3: 
             return {'style': "Lead", 'features': {'note_count': len(notes)}}

        # Analyze Polyphony (Chords vs Single Notes)
        simultaneous = 0
        checks = 0
        for i in range(len(notes)):
            current_start = notes[i].start
            current_end = notes[i].end
            overlap_count = 0
            for j in range(len(notes)):
                if i == j: continue
                # check overlap
                if max(current_start, notes[j].start) < min(current_end, notes[j].end):
                    overlap_count += 1
            if overlap_count > 0:
                simultaneous += 1
            checks += 1
            
        poly_ratio = simultaneous / checks if checks > 0 else 0
        features['poly_ratio'] = float(f"{poly_ratio:.2f}")
        
        is_polyphonic = poly_ratio > 0.4
        
        # 1. Octave Bass
        # Check explicit octave jumps in sequence
        is_oct = self._is_octave_pattern(notes)
        features['is_octave'] = is_oct
        
        if is_oct:
            style.append("Oct")
        
        # Average Duration
        avg_dur = np.mean([n.end - n.start for n in notes]) if notes else 0
        features['avg_duration'] = float(f"{avg_dur:.2f}")

        # 2. Chord (Block Chords) / Backing
        if is_polyphonic:
            # If polyphonic and NOT Octave bass, likely "Chord" or "Pad"
            if avg_dur > 1.5: # Long notes
                style.append("Pad")
            else:
                style.append("Chord")
        
        # 3. Arpeggio
        # Monophonic but wide range?
        if not is_polyphonic:
            # Check if likely Arp
            # Consistent interval jumps?
            intervals = [abs(notes[i].pitch - notes[i+1].pitch) for i in range(len(notes)-1)]
            avg_interval = np.mean(intervals) if intervals else 0
            features['avg_interval'] = float(f"{avg_interval:.2f}")
            
            if avg_interval > 3.0: # Average interval > Minor 3rd
                style.append("Arp")
            else:
                # Small intervals -> Melody or Scale
                # Check for "Walking" (steady stream of quarters)
                is_walk = self._is_walking_bass(notes)
                features['is_walking'] = is_walk
                
                if is_walk:
                     style.append("Walking")
        
        # 4. Figuration / Riff
        # Fast notes?
        if avg_dur < 0.25 and not "Arp" in style:
             style.append("Figuration")

        final_style = "_".join(style) if style else "Melody"
        return {'style': final_style, 'features': features}

    def _is_octave_pattern(self, notes):
        if len(notes) < 4: return False
        octave_jumps = 0
        for i in range(len(notes)-1):
            if abs(notes[i].pitch - notes[i+1].pitch) == 12:
                octave_jumps += 1
        return octave_jumps > (len(notes) * 0.3)
        
    def _is_walking_bass(self, notes):
        # Continuous stream, mostly quarter notes, melodic movement
        # Calculate gap between notes
        gaps = []
        durations = []
        for i in range(len(notes)-1):
            gaps.append(notes[i+1].start - notes[i].end)
            durations.append(notes[i].end - notes[i].start)
            
        avg_gap = np.mean(gaps) if gaps else 0
        avg_dur = np.mean(durations) if durations else 0
        
        # Walking lines usually legato or slight gap, steady duration
        # Assume approx 120bpm -> quarter = 0.5s
        # But we don't know tempo here easily without passing it.
        # Check consistency of duration
        std_dur = np.std(durations) if durations else 1
        return avg_gap < 0.1 and std_dur < 0.1 and avg_dur > 0.3 and avg_dur < 0.8

