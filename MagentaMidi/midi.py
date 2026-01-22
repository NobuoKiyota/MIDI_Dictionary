import os
import shutil
import time
import json
import threading
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, scrolledtext
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 設定ファイルのパス
CONFIG_FILE = "config.json"

class MidiWatcherHandler(FileSystemEventHandler):
    def __init__(self, log_callback, get_save_dir):
        self.log_callback = log_callback
        self.get_save_dir = get_save_dir

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".mid"):
            save_dir = self.get_save_dir()
            if not save_dir or not os.path.exists(save_dir):
                self.log_callback("【警告】保存先が無効です。コピーをスキップしました。")
                return

            # 書き込み完了を待機
            time.sleep(0.5)
            
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_name = os.path.basename(event.src_path)
            new_filename = f"Captured_{now}.mid"
            dest_path = os.path.join(save_dir, new_filename)

            try:
                shutil.copy2(event.src_path, dest_path)
                self.log_callback(f"【保存成功】{original_name} -> {new_filename}")
            except Exception as e:
                self.log_callback(f"【エラー】コピー失敗: {e}")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MIDI Temp Auto-Capturer")
        self.geometry("500x400")
        
        # 設定の読み込み
        self.config = self.load_config()
        self.save_dir = tk.StringVar(value=self.config.get("save_dir", ""))

        self.setup_ui()
        self.start_monitoring()

    def setup_ui(self):
        # 保存先設定エリア
        top_frame = tk.Frame(self, pady=10)
        top_frame.pack(fill=tk.X, padx=10)
        
        tk.Label(top_frame, text="保存先フォルダ:").pack(side=tk.LEFT)
        tk.Entry(top_frame, textvariable=self.save_dir, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="参照", command=self.browse_folder).pack(side=tk.LEFT)

        # ログ表示エリア
        tk.Label(self, text="ログ:").pack(anchor=tk.W, padx=10)
        self.log_area = scrolledtext.ScrolledText(self, height=15)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log("システム起動: 監視を開始しました。")
        self.log(f"監視対象(Temp): {os.getenv('TEMP')}")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_dir.set(folder)
            self.save_config()
            self.log(f"保存先を更新しました: {folder}")

    def log(self, message):
        timestamp = datetime.now().strftime("[%H:%M:%S] ")
        self.log_area.insert(tk.END, timestamp + message + "\n")
        self.log_area.see(tk.END)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"save_dir": self.save_dir.get()}, f)

    def start_monitoring(self):
        temp_dir = os.getenv('TEMP')
        event_handler = MidiWatcherHandler(self.log, self.save_dir.get)
        self.observer = Observer()
        self.observer.schedule(event_handler, temp_dir, recursive=False)
        self.observer.start()

    def on_closing(self):
        self.observer.stop()
        self.observer.join()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()