import os
import pygame
import pretty_midi
import shutil

class MidiPlayer:
    def __init__(self):
        self._init_mixer()
        
    def _init_mixer(self):
        if not pygame.mixer.get_init():
            try:
                # Use strict defaults to avoid device mismatches, or let pygame decide
                # pygame.mixer.init() usually works best.
                pygame.mixer.init()
            except Exception as e:
                print(f"Failed to init pygame mixer: {e}")

    def play(self, file_path, instrument_text=None):
        if not os.path.exists(file_path):
            return

        self.stop() # Stop current if any
        
        # Ensure volume is up
        try:
             if pygame.mixer.get_init():
                 pygame.mixer.music.set_volume(1.0)
        except: pass
        
        play_path = file_path
        
        # Instrument Override Logic
        # If instrument_text is provided (and not empty), we rewrite the MIDI
        # If instrument_text is empty/None, we fallback to Piano (Prog 0) by rewriting?
        # User said: "If Instrument is written... play with that. If not, play GM001 Piano"
        # So we ALWAYS rewrite.
        
        if not instrument_text:
             program_num = 0 # Acoustic Grand Piano
             print(f"DEBUG: No instrument text provided. Defaulting to Piano (0).")
        else:
             program_num = self._map_instrument(instrument_text)
             print(f"DEBUG: Instrument Text='{instrument_text}' -> Program Num={program_num}")
             
        # Create temp file with overridden instruments
        try:
            play_path = self._create_preview_midi(file_path, program_num, instrument_text)
            print(f"DEBUG: Created preview midi at: {play_path}")
        except Exception as e:
            print(f"Error creating preview midi: {e}")
            play_path = file_path # Fallback to original
            
        try:
            # Re-init if needed (sometimes needed on Windows if device was released?)
            # Usually keep init is fine.
            if not pygame.mixer.get_init():
                self._init_mixer()
            
            print(f"DEBUG: Loading MIDI for playback: {play_path}")
            pygame.mixer.music.load(play_path)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Error playing midi: {e}")

    def stop(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            
    def is_playing(self):
        if pygame.mixer.get_init():
            return pygame.mixer.music.get_busy()
        return False

    def _create_preview_midi(self, src_path, program_number, instrument_text=None):
        pm = pretty_midi.PrettyMIDI(src_path)
        
        # Check if user requested Drums specifically
        force_drums = (instrument_text == "Standard Drum Kit")
        
        for inst in pm.instruments:
            if force_drums:
                inst.is_drum = True
                inst.program = 0 # Standard Kit usually 0 on Ch 10
                print(f"DEBUG: Forcing Drums for {inst.name}")
            elif not inst.is_drum:
                old_prog = inst.program
                inst.program = program_number
                print(f"DEBUG: Rewriting Instrument {inst.name} (Prog {old_prog}) -> Prog {inst.program}")
                
        # Save to temp
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        dest = os.path.join(temp_dir, "preview.mid")
        pm.write(dest)
        return dest

    def _map_instrument(self, text):
        from instrument_config import get_program_number
        return get_program_number(text)
