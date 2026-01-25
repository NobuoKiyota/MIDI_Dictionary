# Project Handover: Unified MIDI Ensemble Generator

## 📅 Status: Completed (2025-01-26)

MIDIアンサンブル生成システムの大規模な改修が完了しました。
従来の「Pythonコードによるスタイル定義」を廃止し、**「Excelによる完全データ駆動型生成システム」** へと移行しました。

## 🚀 主要な変更点

### 1. 統合スタイルシステム (Unified Style System)
*   **旧:** `PadStyle`, `RhythmStyle`, `TranceArpStyle` など別々のクラスで管理。
*   **新:** 全て単一の `ExternalStyleStrategy` クラスで処理。振る舞いは `ensemble_styles.xlsx` のデータで定義。
*   **メリット:** プログラムを変更することなく、Excel編集だけで新しい演奏スタイル（ドラム以外ほぼ全て）を作成可能。

### 2. 新Excelフォーマット
*   **ファイル:** `EnsembleGenerator/ensemble_styles.xlsx`
*   **マニュアル:** `Ensemble_Style_Guide.md` (詳細な記述ルールはこちらを参照)
*   **特徴:**
    *   **行指向:** 1つのスタイルを「Voice (レイヤー)」「Type (Seq/Gate/Vel)」ごとの複数行で記述。
    *   **32ステップ対応:** 2小節以上の長いパターンも記述可能。
    *   **ポリフォニー:** `voice` 番号を変えることで、複数のリズムやメロディを重ねて再生可能。

### 3. ロジックの改善
*   **Gate Clamping廃止:** ベース音（トリガー）が短くても、Excelで指定した長さ（Gate）分だけ音が伸びるようになりました（Padや開放弦の表現が可能）。
*   **インターバルロジック:** `0, 1, 2` という指定が、コードタイプ（M7, m7等）に合わせて自動的に `Root, 3rd, 5th` など適切な構成音に変換されます。
*   **Pattern Reset修正:** 音の切り替わりでパターンがリセットされず、小節グリッドに合わせて連続して演奏されます。

---

## 📂 重要ファイル構成

```text
MIDI_Dictionary/
├── EnsembleGenerator/
│   ├── ensemble_styles.xlsx      # [重要] パターン定義データベース
│   ├── midi_ensemble_generator.py # 生成のメインスクリプト
│   └── style_strategies.py        # Excel読み込み・生成ロジック(ExternalStyleStrategy)
│
├── Ensemble_Style_Guide.md       # [重要] Excel書き方マニュアル (AI指示用にも最適)
└── HANDOVER.md                   # このファイル
```

## ⚠️ 既知の注意点 / 次のステップ
*   **旧ファイルの残骸:** `arpeggio_patterns.xlsx` や `ArpStrategies.py` がもし残っていたら削除して構いません（現在は使用していません）。
*   **プリセット:** `midi_ensemble_generator.py` 内の `PRESETS` 定義は、Excel内の新しいスタイル名（Trance, Pad, Rhythmなど）に合わせて更新済みです。新しいスタイルをExcelに追加した場合は、必要に応じて `PRESETS` も編集してください。

## 🤖 AIへの依頼方法
新しいパターンを追加したい場合は、`Ensemble_Style_Guide.md` の内容をAIにコピペして渡せば、適切なExcelデータを生成してくれます。
