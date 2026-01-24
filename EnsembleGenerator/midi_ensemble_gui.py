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
        self.geometry("600x500") # Slightly taller for extra controls
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1) # Log area expands

        # Title
        self.label_title = ctk.CTkLabel(self, text="MIDI Ensemble Generator", font=("Arial", 20, "bold"))
        self.label_title.grid(row=0, column=0, pady=10, sticky="ew")

        # Drop Area
        self.frame_drop = ctk.CTkFrame(self, height=100, fg_color="gray30")
        self.frame_drop.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.frame_drop.grid_propagate(False)
        
        self.label_drop = ctk.CTkLabel(self.frame_drop, text="Drag & Drop MIDI Files Here\n(Bass Track Only)\n\nVer 1.7.2", font=("Arial", 14))
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

        # Log
        self.textbox_log = ctk.CTkTextbox(self)
        self.textbox_log.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        
        # Version Label
        self.label_ver = ctk.CTkLabel(self, text="Ver 1.7.2", font=("Arial", 10), text_color="gray")
        self.label_ver.grid(row=4, column=0, sticky="se", padx=5, pady=0)
        
        # State
        self.current_file = None
        self.generator = EnsembleGenerator()
        
        # Initial Log
        self.log_styles()

    def reload_styles(self):
        try:
            register_external_styles(STYLE_REGISTRY)
            self.log(">>> Reloaded Arpeggio Patterns from Excel.")
            self.log_styles()
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
        
        vel_scale = self.slider_vel.get()
        selected_key = self.option_key.get()
        
        self.btn_run.configure(state="disabled")
        self.log(f"Starting generation for {os.path.basename(self.current_file)}...")
        self.log(f"Settings: Velocity={vel_scale:.1f}, Key={selected_key}")
        
        # Run in thread
        threading.Thread(target=self._generate_thread, args=(self.current_file, vel_scale, selected_key), daemon=True).start()

    def _generate_thread(self, input_file, vel_scale, key_arg):
        try:
            generated = self.generator.generate(input_file, velocity_scale=vel_scale, key_arg=key_arg)
            self.log(f"Success! Generated {len(generated)} files.")
            for f in generated:
                self.log(f"- {os.path.basename(f)}")
        except Exception as e:
            self.log(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.btn_run.configure(state="normal")

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    app = EnsembleApp()
    app.mainloop()
