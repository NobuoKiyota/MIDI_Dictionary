import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import threading
import sys

# Ensure script directory is in path to import generator
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from midi_ensemble_generator import EnsembleGenerator, STYLE_REGISTRY, register_external_styles

class EnsembleApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        
        self.title("MIDI Ensemble Generator")
        self.geometry("800x600") # Wider for filters
        
        self.grid_columnconfigure(0, weight=3)
        self.grid_rowconfigure(3, weight=1) # Log area expands

        # Title
        self.label_title = ctk.CTkLabel(self, text="MIDI Ensemble Generator", font=("Arial", 20, "bold"))
        self.label_title.grid(row=0, column=0, pady=10, sticky="ew")

        # Drop Area
        self.frame_drop = ctk.CTkFrame(self, height=100, fg_color="gray30")
        self.frame_drop.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.frame_drop.grid_propagate(False)
        
        self.label_drop = ctk.CTkLabel(self.frame_drop, text="Drag & Drop MIDI Files Here\n(Bass Track Only)\n\nVer 1.7.3", font=("Arial", 14))
        self.label_drop.place(relx=0.5, rely=0.5, anchor="center")
        
        # Register Drop
        self.frame_drop.drop_target_register(DND_FILES)
        self.frame_drop.dnd_bind('<<Drop>>', self.on_drop)

        # Controls
        self.frame_controls = ctk.CTkFrame(self)
        self.frame_controls.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        # Velocity Slider
        self.label_vel = ctk.CTkLabel(self.frame_controls, text="Vel Scale: 0.9")
        self.label_vel.pack(side="left", padx=5)
        
        self.slider_vel = ctk.CTkSlider(self.frame_controls, from_=0.1, to=1.5, number_of_steps=14, width=150, command=self.update_vel_label)
        self.slider_vel.set(0.9)
        self.slider_vel.pack(side="left", padx=5)

        # Timing Jitter Slider
        self.label_jitter = ctk.CTkLabel(self.frame_controls, text="Jitter: 10ms")
        self.label_jitter.pack(side="left", padx=5)
        
        self.slider_jitter = ctk.CTkSlider(self.frame_controls, from_=0.0, to=0.05, number_of_steps=50, width=150, command=self.update_jitter_label)
        self.slider_jitter.set(0.01)
        self.slider_jitter.pack(side="left", padx=5)

        # Key Selector
        self.label_key = ctk.CTkLabel(self.frame_controls, text="Key:")
        self.label_key.pack(side="left", padx=5)
        
        self.option_key = ctk.CTkOptionMenu(self.frame_controls, values=["Auto"], width=100)
        self.option_key.pack(side="left", padx=5)
        self.populate_keys()

        self.btn_run = ctk.CTkButton(self.frame_controls, text="Generate", command=self.run_generation, state="disabled", width=80)
        self.btn_run.pack(side="right", padx=10)

        # Reload Button (New)
        self.btn_reload = ctk.CTkButton(self.frame_controls, text="Reload Excel", command=self.reload_styles, width=80, fg_color="green")
        self.btn_reload.pack(side="right", padx=5)

        # Scale Expansion Settings Frame
        self.frame_expand = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_expand.grid(row=4, column=0, padx=20, pady=5, sticky="ew")
        
        self.check_triad = ctk.CTkCheckBox(self.frame_expand, text="Triad")
        self.check_triad.pack(side="left", padx=5)
        
        self.check_7th = ctk.CTkCheckBox(self.frame_expand, text="7th")
        self.check_7th.pack(side="left", padx=5)
        
        self.check_harmonic = ctk.CTkCheckBox(self.frame_expand, text="Harmonic Min")
        self.check_harmonic.pack(side="left", padx=5)
        
        self.check_melodic = ctk.CTkCheckBox(self.frame_expand, text="Melodic Min")
        self.check_melodic.pack(side="left", padx=5)
        
        # Placeholders
        self.check_tension = ctk.CTkCheckBox(self.frame_expand, text="Tension", width=80)
        self.check_tension.pack(side="left", padx=5)
        
        self.check_substitute = ctk.CTkCheckBox(self.frame_expand, text="Substitute", width=80)
        self.check_substitute.pack(side="left", padx=5)

        # Strict Validation Checkbox (Optional Voice Check)
        self.check_strict = ctk.CTkCheckBox(self.frame_expand, text="Strict Voice Check", fg_color="red")
        self.check_strict.pack(side="left", padx=10)

        # Stop State
        self.stop_event = threading.Event()

        # Style Filter Frame
        self.lbl_filter = ctk.CTkLabel(self, text="Style Filter (Include Types):")
        self.lbl_filter.grid(row=5, column=0, sticky="w", padx=20, pady=(5,0))

        self.frame_filters = ctk.CTkScrollableFrame(self, height=100, orientation="horizontal")
        self.frame_filters.grid(row=6, column=0, padx=20, pady=5, sticky="ew")
        
        self.filter_checkboxes = {} # Map 'type_name' -> checkbox widget
        
        # Log
        self.textbox_log = ctk.CTkTextbox(self, height=100)
        self.textbox_log.grid(row=7, column=0, padx=20, pady=10, sticky="nsew")
        self.grid_rowconfigure(7, weight=1)
        
        # Version Label
        self.label_ver = ctk.CTkLabel(self, text="Ver 1.8.1", font=("Arial", 10), text_color="gray")
        self.label_ver.grid(row=8, column=0, sticky="se", padx=5, pady=0)
        
        # State
        self.current_file = None
        self.generator = EnsembleGenerator()
        
        # Initial Log & Populate Filters
        self.log_styles()
        self.populate_filters()

    def populate_filters(self):
        # Clear existing
        for cb in self.filter_checkboxes.values():
            cb.destroy()
        self.filter_checkboxes = {}
        
        # Scan registry for unique rename_src
        unique_types = set()
        from midi_ensemble_generator import ExternalStyleStrategy
        
        for name, strategy_cls_or_obj in STYLE_REGISTRY.items():
            # Strategy might be class or instance or lambda
            # We need to peek at 'rename_src'. 
            # If it's a class, we might need to instantiate? No, that's heavy.
            # Usually registry has instances or lambdas?
            # Existing code: STYLE_REGISTRY[name] = ExternalStyleStrategy(...)
            
            # Let's try to get rename_src
            src_val = 'Default'
            obj = strategy_cls_or_obj
            
            # If callable (lambda or class), try to inspect? 
            # For this purpose, we assume registry stores instantiated objects OR we instantiate temp
            if callable(obj):
                try:
                    # Try calling if it's a factory
                    temp = obj()
                    src_val = getattr(temp, 'rename_src', 'Default')
                except:
                    pass
            else:
                src_val = getattr(obj, 'rename_src', 'Default')
            
            if src_val is None: src_val = 'Default'
            unique_types.add(str(src_val))
            
        # Create Checkboxes
        sorted_types = sorted(list(unique_types))
        for t in sorted_types:
            cb = ctk.CTkCheckBox(self.frame_filters, text=t, width=60)
            cb.deselect() # Default OFF (User request: "StyleFilterはデフォルトチェックオフにしておいてください")
            cb.pack(side="left", padx=5)
            self.filter_checkboxes[t] = cb

    def reload_styles(self):
        try:
            register_external_styles(STYLE_REGISTRY)
            self.log(">>> Reloaded Arpeggio Patterns from Excel.")
            self.log_styles()
            self.populate_filters()
        except Exception as e:
            self.log(f"Error reloading styles: {e}")

    def log_styles(self):
        styles = list(STYLE_REGISTRY.keys())
        self.log(f"Loaded Styles ({len(styles)}): {', '.join(styles)}")

    def populate_keys(self):
        keys = ["Auto"]
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        for n in notes:
            keys.append(f"{n} Major")
            keys.append(f"{n} Minor")
            keys.append(f"{n} Harmonic Minor")
            keys.append(f"{n} Melodic Minor")
        self.option_key.configure(values=keys)
        self.option_key.set("Auto")

    def update_vel_label(self, value):
        self.label_vel.configure(text=f"Vel Scale: {float(value):.1f}")

    def update_jitter_label(self, value):
        ms = int(float(value) * 1000)
        self.label_jitter.configure(text=f"Jitter: {ms}ms")

    def on_drop(self, event):
        file_path = event.data
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
            
        if os.path.isfile(file_path):
            self.current_file = file_path
            self.label_drop.configure(text=os.path.basename(file_path))
            self.btn_run.configure(state="normal")
            self.log(f"Loaded: {file_path}")
        else:
            self.log("Invalid file dropped.")

    def log(self, message):
        self.textbox_log.insert("end", message + "\n")
        self.textbox_log.see("end")

    def run_generation(self):
        if not self.current_file:
            return
        
        # Toggle Logic: If running, STOP.
        if self.btn_run.cget("text") == "Stop":
            self.stop_generation()
            return

        self.stop_event.clear()
        vel_scale = self.slider_vel.get()
        jitter_val = self.slider_jitter.get()
        selected_key = self.option_key.get()
        
        # Collect Expansion Flags
        expansion_flags = {
            'triad': self.check_triad.get() == 1,
            '7th': self.check_7th.get() == 1,
            'harmonic_minor': self.check_harmonic.get() == 1,
            'melodic_minor': self.check_melodic.get() == 1,
            'tension': self.check_tension.get() == 1,
            'substitute': self.check_substitute.get() == 1
        }
        
        strict_val = (self.check_strict.get() == 1)
        
        # Collect Filter Types
        if self.filter_checkboxes:
            allowed = []
            for t_name, cb in self.filter_checkboxes.items():
                if cb.get() == 1:
                    allowed.append(t_name)
        else:
            allowed = None # No filters loaded -> Allow all
        
        # Change Button to Stop
        self.btn_run.configure(text="Stop", fg_color="red", command=self.run_generation) # Command stays same, logic handles toggle
        
        self.log(f"Starting generation for {os.path.basename(self.current_file)}...")
        self.log(f"Settings: Velocity={vel_scale:.1f}, Key={selected_key}")
        self.log(f"Expansion: {expansion_flags}, StrictVoice: {strict_val}")
        self.log(f"Style Types Allowed: {allowed}")
        
        # Run in thread
        threading.Thread(target=self._generate_thread, args=(self.current_file, vel_scale, selected_key, expansion_flags, strict_val, allowed, jitter_val), daemon=True).start()

    def stop_generation(self):
        if not self.stop_event.is_set():
            self.stop_event.set()
            self.log(">>> Stopping generation... (Please wait for current file)")
            self.btn_run.configure(state="disabled") # Disable until thread finishes

    def _generate_thread(self, input_file, vel_scale, key_arg, expansion_flags, strict_val, allowed_types, jitter_val):
        try:
            generated = self.generator.generate(
                input_file, 
                velocity_scale=vel_scale, 
                key_arg=key_arg, 
                expansion_flags=expansion_flags,
                strict_validation=strict_val,
                allowed_types=allowed_types,
                timing_jitter=jitter_val,
                stop_event=self.stop_event
            )
            
            if self.stop_event.is_set():
                self.log(f"Cancelled. Generated {len(generated)} files so far.")
            else:
                self.log(f"Success! Generated {len(generated)} files.")
                
            for f in generated:
                self.log(f"- {os.path.basename(f)}")
        except Exception as e:
            self.log(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.stop_event.clear()
            self.btn_run.configure(state="normal", text="Generate", fg_color=["#3B8ED0", "#1F6AA5"], command=self.run_generation) # Reset color

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    app = EnsembleApp()
    app.mainloop()
