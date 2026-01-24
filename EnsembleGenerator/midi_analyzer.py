import pretty_midi
import math

class NoteAnalysis:
    def __init__(self, note, is_on_beat, sub_beat_type, is_syncopated, is_mute, is_dotted, harmonic_pitch):
        self.note = note
        self.is_on_beat = is_on_beat       # True if starts on a beat (x.0)
        self.sub_beat_type = sub_beat_type # '1', 'e', '&', 'a', or 'off'
        self.is_syncopated = is_syncopated # True if crosses bar line
        self.is_mute = is_mute             # True if ghost note
        self.is_dotted = is_dotted         # True if dotted duration
        self.harmonic_pitch = harmonic_pitch 

class MidiAnalyzer:
    def __init__(self, midi_data):
        self.midi_data = midi_data
        self.beats = midi_data.get_beats()
        self.downbeats = midi_data.get_downbeats()

    def get_sub_beat_type(self, fraction):
        """
        Classifies fraction (0.0 to 1.0) into 16th grid.
        1 (0.0), e (0.25), & (0.5), a (0.75).
        Tolerance +/- 0.05
        """
        f = fraction - int(fraction) # 0.0 - 0.999
        tol = 0.05
        if f < tol or f > 1.0 - tol: return '1'
        if abs(f - 0.25) < tol: return 'e'
        if abs(f - 0.50) < tol: return '&'
        if abs(f - 0.75) < tol: return 'a'
        return 'off'

    def detect_groove(self, instrument):
        # ... (Previous Logic, kept simple) ...
        # Re-using the sub-beat logic here could be better but let's keep the existing structure if it works,
        # or simplify using the new fractions.
        # Let's keep the previous implementation logic but refined? 
        # Actually I'll copy the previous detect_groove but use get_sub_beat_type logic implicitly.
        onset_fractions = []
        for note in instrument.notes:
            # Simple linear search for beat
            idx = 0
            while idx < len(self.beats) - 1 and self.beats[idx+1] <= note.start + 0.001:
                idx += 1
            if idx < len(self.beats) - 1:
                beat_start = self.beats[idx]
                beat_duration = self.beats[idx+1] - beat_start
                if beat_duration > 0:
                    fraction = (note.start - beat_start) / beat_duration
                    onset_fractions.append(fraction)
        
        if not onset_fractions: return '8-beat'
        
        score_16 = 0
        for frac in onset_fractions:
            sb = self.get_sub_beat_type(frac)
            if sb in ['e', 'a']:
                score_16 += 1
        
        ratio = score_16 / len(onset_fractions)
        return '16-beat' if ratio > 0.15 else '8-beat'

    def is_bar_crossing(self, start, end):
        for db in self.downbeats:
            if start < db and end > db + 0.01: 
                return True
            if db > end:
                break
        return False
    
    def is_dotted_note(self, duration_in_beats, tolerance=0.1):
        targets = [0.75, 1.5, 3.0]
        for t in targets:
            if abs(duration_in_beats - t) < tolerance:
                return True
        return False

    def analyze_track(self, instrument):
        analysis_list = []
        
        # 0. Pre-calculation for Velocity Threshold
        velocities = [n.velocity for n in instrument.notes]
        avg_velocity = sum(velocities) / len(velocities) if velocities else 64
        
        # Window for Harmonic Pitch
        # Store last 3 harmonic pitches to detect stable range
        pitch_window = [] 
        
        print(f"Detected Groove: {self.detect_groove(instrument)}")
        
        for note in instrument.notes:
            start = note.start
            end = note.end
            duration_sec = end - start
            
            # Beat Calc
            idx = 0
            while idx < len(self.beats) - 1 and self.beats[idx+1] <= start + 0.001:
                idx += 1
            
            beat_dur = 0.5
            fraction = 0.0
            if idx < len(self.beats) - 1:
                beat_dur = self.beats[idx+1] - self.beats[idx]
                if beat_dur > 0:
                    fraction = (start - self.beats[idx]) / beat_dur
            
            duration_beats = duration_sec / beat_dur if beat_dur > 0 else 0
            
            # 1. Sub-beat
            sub_beat = self.get_sub_beat_type(fraction)
            on_beat = (sub_beat == '1')
            
            # 2. Syncopation
            syncopated = self.is_bar_crossing(start, end)
            
            # 3. Mute (Dynamic)
            # - Short time (< 0.02s) OR
            # - Short beat (< 0.25 beat) AND Low Velocity (< 60% of avg)
            is_mute_time = duration_sec < 0.02
            is_mute_vel = (duration_beats < 0.25) and (note.velocity < avg_velocity * 0.6)
            is_mute = is_mute_time or is_mute_vel
            
            # 4. Dotted
            is_dotted = self.is_dotted_note(duration_beats)
            
            # 5. Harmonic Pitch (Windowed)
            current_pitch = note.pitch
            harmonic_pitch = current_pitch
            
            if pitch_window:
                # Calculate window average (rounded)
                window_avg = sum(pitch_window) / len(pitch_window)
                
                # Check for octave jump relative to window average
                # If current pitch is far from average (> 7 semitones)
                dist = current_pitch - window_avg
                if abs(dist) > 7:
                    # Check if it's an octave equivalent of something in window?
                    # Or just fold towards average?
                    # Simple V1.3 logic: If note is same pitch class as Last Note, 
                    # and jump is wide, fold to Last Note's octave.
                    last_pitch = pitch_window[-1]
                    if (current_pitch % 12 == last_pitch % 12):
                        # It's an octave variant of the previous note.
                        # Force it to be the one closer to window average?
                        # Or just stick to previous note (stability).
                        # Let's use previous note for stability.
                        harmonic_pitch = last_pitch
            
            # Update Window
            pitch_window.append(harmonic_pitch)
            if len(pitch_window) > 3:
                pitch_window.pop(0)
                    
            analysis_obj = NoteAnalysis(
                note=note,
                is_on_beat=on_beat,
                sub_beat_type=sub_beat,
                is_syncopated=syncopated,
                is_mute=is_mute,
                is_dotted=is_dotted,
                harmonic_pitch=harmonic_pitch
            )
            analysis_list.append(analysis_obj)
            
        return analysis_list

    def analyze(self):
        """
        Main entry point for analysis. 
        Iterates over instruments and analyzes the first non-drum track found.
        Returns: list of NoteAnalysis objects.
        """
        for inst in self.midi_data.instruments:
            if not inst.is_drum:
                print(f"Analyzing Instrument: {inst.name} (Program {inst.program})")
                return self.analyze_track(inst)
        
        # Fallback if only drums
        if self.midi_data.instruments:
             print("Warning: Only drum tracks found. Analyzing first track.")
             return self.analyze_track(self.midi_data.instruments[0])
             
        return []
