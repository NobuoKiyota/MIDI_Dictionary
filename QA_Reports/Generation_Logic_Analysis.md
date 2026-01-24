# Generation Logic Analysis

現在の `midi_ensemble_generator.py` は、登録された全ての「コード理論」と「演奏スタイル」の組み合わせを総当たりで生成する仕様になっています。

## 現状の出力ロジック

以下の2つのループがネスト（入れ子）しており、**[コード種類の数] × [スタイル種類の数]** 分のMIDIファイルが出力されます。

### 1. コード戦略のループ (Line 910)
```python
for chord_name, chord_cls in CHORD_REGISTRY.items():
```
ここで登録されている全てのコード理論ごとに処理が回ります。
- **Maj**: メジャー・トライアド (基本形)
- **Maj_Open**: メジャー・トライアド (オープンボイシング)
- **Diatonic**: ダイアトニック・コード (キーに合わせた和音)
- **Diatonic_7th**: ダイアトニック・セブンス
など

### 2. スタイル戦略のループ (Line 948)
```python
for style_name, style_cls in STYLE_REGISTRY.items():
```
各コード理論に対し、登録されている全ての演奏スタイルを適用してファイルを出力します。
- **Pad**: 白玉（全音符）
- **Rhythm**: バッキングリズム
- **Arp**: シンプルなアルペジオ
- **Arp_Trance / LoFi / Healing ...**: Excel等で追加された拡張アルペジオ

## 結果
例えば、コード理論が4種類、スタイルが5種類ある場合、1つの入力ファイルに対して `4 x 5 = 20ファイル` が生成されます。

## 該当コード箇所
`scripts/midi_ensemble_generator.py`

- **910行目**: `for chord_name, chord_cls in CHORD_REGISTRY.items():`
- **948行目**: `for style_name, style_cls in STYLE_REGISTRY.items():`
- **1015行目**: `output_filename = f"{original_name}_{chord_name}_{style_name}.mid"` (ファイル出力)
