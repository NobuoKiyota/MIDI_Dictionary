import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pytesseract
from PIL import Image, ImageGrab
import os
import threading
import re  # 【追加】正規表現用

# 【重要】Tesseractのインストールパス
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("多言語対応OCRツール (自動整形付き)")
        self.root.geometry("600x600")
        
        self.root.bind('<Control-v>', self.paste_image_event)
        self.is_processing = False

        # --- 設定フレーム ---
        self.setting_frame = tk.Frame(root, pady=5)
        self.setting_frame.pack(side=tk.TOP, fill=tk.X, padx=10)

        tk.Label(self.setting_frame, text="読み取り言語:").pack(side=tk.LEFT)

        self.lang_options = {
            "英語 (English)": "eng",
            "日本語 (Japanese)": "jpn",
            "日本語 + 英語 (混合)": "jpn+eng", 
            "中国語 簡体字": "chi_sim",
            "中国語 繁体字": "chi_tra",
            "韓国語": "kor",
            "韓国語 + 英語": "kor+eng",
        }
        self.selected_lang_name = tk.StringVar()
        self.selected_lang_name.set("日本語 (Japanese)") # デフォルトを日本語に変更

        self.lang_combo = ttk.Combobox(
            self.setting_frame, 
            textvariable=self.selected_lang_name, 
            values=list(self.lang_options.keys()),
            state="readonly",
            width=25
        )
        self.lang_combo.pack(side=tk.LEFT, padx=5)

        # --- 操作ボタン ---
        self.top_frame = tk.Frame(root, pady=10)
        self.top_frame.pack(side=tk.TOP, fill=tk.X)

        self.btn_open = tk.Button(self.top_frame, text="画像ファイルを選択", command=self.open_image, width=18, height=2)
        self.btn_open.pack(side=tk.LEFT, padx=10)

        self.btn_paste = tk.Button(self.top_frame, text="クリップボード貼付\n(Ctrl+V)", command=self.paste_image, width=20, height=2, bg="#e0f7fa")
        self.btn_paste.pack(side=tk.LEFT, padx=5)

        self.btn_copy = tk.Button(self.top_frame, text="テキストをコピー", command=self.copy_to_clipboard, width=18, height=2, state=tk.DISABLED)
        self.btn_copy.pack(side=tk.RIGHT, padx=10)

        # --- テキストエリア ---
        self.text_frame = tk.Frame(root)
        self.text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.scrollbar = tk.Scrollbar(self.text_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_area = tk.Text(self.text_frame, height=20, font=("Consolas", 10), yscrollcommand=self.scrollbar.set)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.text_area.yview)

        # --- ステータスバー ---
        self.status_label = tk.Label(root, text="準備完了", bd=1, relief=tk.SUNKEN, anchor=tk.W, font=("Consolas", 9))
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def get_tesseract_lang_code(self):
        name = self.selected_lang_name.get()
        return self.lang_options.get(name, "eng")

    # --- 【追加】スペース除去ロジック ---
    def remove_unwanted_spaces(self, text, lang_code):
        """
        日本語・中国語・韓国語などが含まれる場合、
        文字間の不要なスペースを除去する
        """
        # 英語オンリーの場合は整形しない（英単語が繋がってしまうため）
        if lang_code == 'eng':
            return text

        # 処理ロジック:
        # 1. 「非ASCII文字(日本語等)」の 後ろ にあるスペースを削除
        #    例: "画像 " -> "画像"
        # 2. 「非ASCII文字(日本語等)」の 前 にあるスペースを削除
        #    例: " 手順" -> "手順"
        
        # パターン: [^\x00-\x7F] は「ASCII文字以外（全角文字など）」を意味します
        
        # 全角文字の後ろのスペースを削除
        text = re.sub(r'([^\x00-\x7F])\s+', r'\1', text)
        # 全角文字の前のスペースを削除
        text = re.sub(r'\s+([^\x00-\x7F])', r'\1', text)

        return text

    # --- アニメーション ---
    def animate_loading(self, step=0):
        if not self.is_processing:
            return
        bar_length = 20
        pos = step % bar_length
        anim_str = "_" * pos + "■" + "_" * (bar_length - pos - 1)
        self.status_label.config(text=f"文字起こし中... [{anim_str}]")
        self.root.after(100, lambda: self.animate_loading(step + 1))

    # --- OCR実行 ---
    def start_ocr_process(self, img, source_name):
        if self.is_processing:
            return
        self.is_processing = True
        self.text_area.delete(1.0, tk.END)
        self.btn_copy.config(state=tk.DISABLED)
        self.animate_loading()
        
        thread = threading.Thread(target=self.ocr_worker, args=(img, source_name))
        thread.daemon = True
        thread.start()

    def ocr_worker(self, img, source_name):
        try:
            lang_code = self.get_tesseract_lang_code()
            
            # OCR実行
            text = pytesseract.image_to_string(img, lang=lang_code)
            
            # 【追加】不要なスペースを除去する処理を通す
            text = self.remove_unwanted_spaces(text, lang_code)

            self.root.after(0, lambda: self.finish_ocr_success(text, source_name))
            
        except Exception as e:
            self.root.after(0, lambda: self.finish_ocr_error(str(e)))

    def finish_ocr_success(self, text, source_name):
        self.is_processing = False
        self.text_area.insert(tk.END, text)
        self.btn_copy.config(state=tk.NORMAL, bg="#dddddd")
        self.status_label.config(text=f"完了: {source_name}")

    def finish_ocr_error(self, error_msg):
        self.is_processing = False
        messagebox.showerror("OCRエラー", f"文字起こしに失敗しました。\n{error_msg}")
        self.status_label.config(text="エラーが発生しました")

    # --- ファイル/クリップボード ---
    def open_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if file_path:
            self.start_ocr_process(Image.open(file_path), os.path.basename(file_path))

    def paste_image(self):
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                self.start_ocr_process(img, "クリップボード画像")
            elif img and isinstance(img, list):
                 self.start_ocr_process(Image.open(img[0]), "クリップボード(ファイル)")
            else:
                self.status_label.config(text="クリップボードに画像がありません")
        except Exception as e:
            self.status_label.config(text=f"貼り付けエラー: {e}")

    def paste_image_event(self, event):
        self.paste_image()

    def copy_to_clipboard(self):
        content = self.text_area.get(1.0, tk.END).strip()
        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.root.update()
            self.status_label.config(text="コピーしました！")

if __name__ == "__main__":
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()