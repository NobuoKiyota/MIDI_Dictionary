import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import seaborn as sns

class LearningVisualizer(ctk.CTkToplevel):
    def __init__(self, parent, data_path):
        super().__init__(parent)
        self.title("Learning Progress Visualization")
        self.geometry("1000x800")
        self.data_path = data_path
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        self.lbl_title = ctk.CTkLabel(self, text="AI Learning Statistics", font=("Arial", 20, "bold"))
        self.lbl_title.grid(row=0, column=0, pady=10)
        
        # Content Frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        self.plot_charts()
        
    def plot_charts(self):
        if not os.path.exists(self.data_path):
            ctk.CTkLabel(self.main_frame, text="No learning data found yet.").pack(pady=20)
            return
            
        try:
            df = pd.read_excel(self.data_path)
        except Exception as e:
            ctk.CTkLabel(self.main_frame, text=f"Error loading data: {e}").pack(pady=20)
            return

        if df.empty:
            ctk.CTkLabel(self.main_frame, text="Data file is empty.").pack(pady=20)
            return
            
        # Create Figure with subplots
        fig = plt.Figure(figsize=(10, 8), dpi=100)
        # Layout: 2x2
        # 1. Correction Rate Over Time (Rolling Average)
        # 2. Cumulative Samples
        # 3. Style Distribution
        # 4. Feature Space (Scatter?) or Groove Dist
        
        # Colors
        sns.set_style("darkgrid")
        
        # 1. Accuracy Trend
        ax1 = fig.add_subplot(221)
        # Convert Timestamp
        # Assuming timestamps are strings, converting to datetime might be needed if not auto-detected
        # But simply using Index as "Time axis" (sample count) is often cleaner for "Progress"
        
        df = df.reset_index()
        df['Accuracy'] = (~df['IsUserCorrected']).astype(int)
        
        # Rolling accuracy (last 10)
        df['RollingAcc'] = df['Accuracy'].rolling(window=10, min_periods=1).mean()
        
        ax1.plot(df.index, df['RollingAcc'], color='green', linewidth=2)
        ax1.set_title("AI Accuracy Trend (Rolling Avg of 10)")
        ax1.set_xlabel("Sample Count")
        ax1.set_ylabel("Accuracy (0-1)")
        ax1.set_ylim(0, 1.1)
        
        # 2. Cumulative Database Size
        ax2 = fig.add_subplot(222)
        ax2.plot(df.index, df.index + 1, color='blue')
        ax2.fill_between(df.index, df.index + 1, color='blue', alpha=0.3)
        ax2.set_title("Total Learned Samples")
        ax2.set_ylabel("Count")
        
        # 3. Ground Truth Styles
        ax3 = fig.add_subplot(223)
        if 'GT_style' in df.columns:
            counts = df['GT_style'].value_counts()
            if not counts.empty:
                # Top 5 + Others
                if len(counts) > 7:
                    others = pd.Series([counts[7:].sum()], index=['Others'])
                    counts = pd.concat([counts[:7], others])
                
                ax3.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=90)
                ax3.set_title("Style Distribution (Ground Truth)")
        
        # 4. Correction Count Histogram (How many fields corrected?)
        ax4 = fig.add_subplot(224)
        if 'CorrectionCount' in df.columns:
            # Filter only corrected ones
            corrected = df[df['IsUserCorrected'] == True]['CorrectionCount']
            if not corrected.empty:
                ax4.hist(corrected, bins=range(1, 8), align='left', rwidth=0.8, color='orange')
                ax4.set_title("Corrections Intensity (When Incorrect)")
                ax4.set_xlabel("Number of Fields Modified")
                ax4.set_xticks(range(1, 8))
            else:
                ax4.text(0.5, 0.5, "No Corrections Yet!", ha='center')
        
        fig.tight_layout()
        
        # Embed
        canvas = FigureCanvasTkAgg(fig, master=self.main_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

if __name__ == "__main__":
    # Test
    app = ctk.CTk()
    def open_vis():
        LearningVisualizer(app, "MIDI_learning/learning_data.xlsx")
    
    ctk.CTkButton(app, text="Open Vis", command=open_vis).pack(pady=20)
    app.mainloop()
