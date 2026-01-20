from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QDialogButtonBox
from PySide6.QtCore import QSize

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MIDI Dictionary - User Manual")
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        # Detailed Manual in HTML/Markdown format
        self.browser.setHtml("""
        <h1>MIDI Dictionary Manual</h1>
        <p><b>Version 1.0</b></p>
        
        <h2>概要 (Overview)</h2>
        <p>MIDI Dictionary は、大量のMIDIファイルを管理・検索・プレビューするためのツールです。<br>
        フォルダ内のMIDIをデータベース化し、音楽的な条件（キー、コード、楽器など）でフィルタリングできます。</p>
        
        <h2>基本操作 (Basic Operation)</h2>
        <h3>1. MIDIの登録 (Registration)</h3>
        <ul>
            <li>画面右上のピアノロール、または左側のリストエリアにMIDIファイルを<b>ドラッグ＆ドロップ</b>します。</li>
            <li>「Register MIDI」ダイアログが表示されます。</li>
            <li>自動推測されたメタデータ（Category, Key, Chordなど）を確認し、必要に応じて修正して<b>OK</b>を押します。</li>
            <li>ファイルは自動的にライブラリフォルダにコピー・リネームされ、リストに追加されます。</li>
        </ul>
        
        <h3>2. プレビュー (Preview)</h3>
        <ul>
            <li>リスト内のファイルをクリックすると、右上のピアノロールにノートが表示されます。</li>
            <li>ピアノロール上でマウスオーバーすると、音程名と小節数(Bar:Beat)が表示されます。</li>
            <li><b>Zoom</b>ボタン (+, -) で縦方向の拡大縮小が可能です。</li>
            <li><b>Draw MIDI</b> ボタンをDAWにドラッグ＆ドロップすると、そのMIDIを利用できます。</li>
        </ul>
        
        <h3>3. 検索・フィルタ (Search & Filter)</h3>
        <ul>
            <li><b>Search Bar</b>: ファイル名、コメントなどに含まれる文字で検索できます。</li>
            <li><b>Filter Panel</b> (画面右下):
                <ul>
                    <li><b>Category</b>: ベース、コード、リズムなどの種類で絞り込み。</li>
                    <li><b>Key (Root)</b>: キー（ルート音）で絞り込み。</li>
                    <li><b>Chord</b>: コードタイプ (Major, minor, m7, etc.) で絞り込み。</li>
                </ul>
            </li>
            <li><b>Reset Filters</b>: すべてのフィルタ解除します。</li>
        </ul>
        
        <h3>4. リスト編集 (Editing)</h3>
        <ul>
            <li>リストのセルをダブルクリックすると内容を編集できます。</li>
            <li>FileNameを変更すると、実際のファイル名も変更されます（重複時は警告あり）。</li>
            <li>KeyやChordは入力時に自動的に書式が修正される場合があります。</li>
        </ul>
        
        <h3>5. 設定 (Settings)</h3>
        <ul>
            <li><b>Always on Top</b>: ウィンドウを最前面に固定します。</li>
            <li><b>Note Colors</b>: 音程ごとのノート色をカスタマイズできます。</li>
            <li><b>Switch Layout</b> (View Menu): 左右のパネル配置を入れ替えます。</li>
        </ul>
        
        <hr>
        <p>By Antigravity</p>
        """)
        
        layout.addWidget(self.browser)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
