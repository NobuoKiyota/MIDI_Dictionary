import os
import threading
import subprocess
import tkinter as tk
from tkinter import scrolledtext
import soundfile as sf
import librosa

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

class DemucsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Quartz Demucs (Stereo 48k Fix)")
        self.root.geometry("500x420")
        self.log_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4")
        self.log_area.pack(expand=True, fill='both', padx=10, pady=10)
        self.log_area.insert(tk.END, "--- Stereo 48k Maintenance Mode ---\n")
        
        if HAS_DND:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_drop)

    def log(self, message):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, f"{message}\n")
        self.log_area.see(tk.END)
        self.log_area.configure(state='disabled')

    def on_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        for f in files:
            path = f.strip('{}').strip('"')
            threading.Thread(target=self.run_process, args=(path,), daemon=True).start()

    def resample_and_stereo_fix(self, file_path, target_sr=48000):
        """ステレオを維持しつつ48kHzへ変換"""
        try:
            # mono=False を指定することでステレオ情報を保持
            y, sr = librosa.load(file_path, sr=None, mono=False)
            
            # リサンプリングが必要か確認
            if sr != target_sr:
                self.log(f"  └─ レート補正: {sr} -> {target_sr}Hz")
                y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
            
            # 保存 (ステレオなら y は 2次元配列になっている)
            sf.write(file_path, y.T if y.ndim > 1 else y, target_sr)
            channels = "Stereo" if y.ndim > 1 else "Mono"
            self.log(f"  └─ 保存完了 ({channels})")
            return True
        except Exception as e:
            self.log(f"  └─ 補正エラー: {e}")
            return False

    def run_process(self, file_path):
        input_dir = os.path.dirname(file_path)
        file_base = os.path.splitext(os.path.basename(file_path))[0]
        
        self.log(f"\n[JOB] {file_base}")

        # htdemucsモデルは基本ステレオ対応
        command = ["demucs", "--overlap", "0.1", "-o", input_dir, file_path]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True)
        
        for line in process.stdout:
            if "Separated" in line: self.log(f"> {line.strip()}")
        
        process.wait()

        if process.returncode == 0:
            # 分離されたファイルを巡回してステレオ＆48kチェック
            output_root = os.path.join(input_dir, "htdemucs", file_base)
            if os.path.exists(output_root):
                for stem in os.listdir(output_root):
                    if stem.endswith(".wav"):
                        self.resample_and_stereo_fix(os.path.join(output_root, stem))
            self.log(f"[SUCCESS] {file_base} 完了")
        else:
            self.log(f"[ERROR] 失敗")

if __name__ == "__main__":
    root = TkinterDnD.Tk() if HAS_DND else tk.Tk()
    app = DemucsGUI(root)
    root.mainloop()