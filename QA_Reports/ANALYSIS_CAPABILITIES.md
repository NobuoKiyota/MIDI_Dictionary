# MIDI Analysis Capabilities Report (v1.2)

This document summarizes the current analysis logic implemented in the MIDI Ensemble Generator system. It is intended for evaluation of the system's "musical understanding" capabilities.

## 1. Harmonic Analysis (和声解析)

The system analyzes the pitch content to understand the harmonic context of the Bass line.

### Key & Scale Detection (キー・スケール判定)
*   **Method**: Krumhansl-Schmuckler algorithm (simplified pitch class distribution).
*   **Capabilities**:
    *   **Major / Natural Minor**: Automatically distinguishes based on pitch profiles.
    *   **Advanced Scales**: Supports **Harmonic Minor** (Raised 7th) and **Melodic Minor** via manual designation (auto-detection defaults to Natural Minor for robustness).
*   **Usage**: Determines the reliable "Diatonic Chord" for each scale degree.

### Chord Construction (コード構成)
*   **Logic**: **Diatonic Strategy** (Functional Harmony).
    *   Maps each Bass note to its **Scale Degree** (I, ii, iii...).
    *   Constructs triads (Major, Minor, Diminished) strictly using notes available in the detected scale.
    *   *Example (A Harmonic Minor)*:
        *   Bass A -> **Am** (A-C-E)
        *   Bass E -> **E Major** (E-G#-B) *Crucial distinction from Natural Minor (Em)*.

### Octave Normalization (オクターブ跳躍の正規化)
*   **Problem**: Bass lines often jump octaves (e.g., E2 -> E3) for rhythmic effect. Naive generation would cause the chords to jump wildly.
*   **Solution**: The analyzer detects octave jumps relative to the previous note.
    *   If `Note(i)` is same pitch class as `Note(i-1)` and `|Pitch(i) - Pitch(i-1)| == 12`:
    *   **Harmonic Pitch** is normalized to the **lower** of the two.
    *   Ensures consistent chord voicing range regardless of bass octave acrobatics.

## 2. Rhythmic Analysis (リズム・アーティキュレーション解析)

The system parses the timing data to understand the "Groove" and playing technique.

### Groove Type (グルーヴ判定)
*   **Logic**: Analysis of Note Onset distribution relative to the Beat Grid.
*   **Classification**:
    *   **16-beat**: If >15% of notes fall on 16th-note subdivisions (0.25, 0.75 fractions of a beat).
    *   **8-beat**: Otherwise (notes mostly on 0.0, 0.5).
*   **Purpose**: Allows future style generators to switch between "Straight 8" and "Funky 16" patterns automatically.

### Beat Position (拍の表裏)
*   **On Beat**: Note starts exactly on the beat (x.0).
*   **Off Beat/Syncopation**: Note starts off-grid.
*   **Bar Crossing (Syncopation)**: Detects if a note's duration extends **across a Bar Line**. This is flagged as `is_syncopated`, useful for detecting tied notes and anticipations.

### Articulation (奏法ニュアンス)
*   **Mute (Ghost Note)**:
    *   **Threshold**: Duration **< 0.02s**.
    *   **Interpretation**: Identified as a percussive mute/ghost note rather than a melodic tone.
*   **Dotted Notes (付点音符)**:
    *   Detects standard dotted durations relative to current BPM.
    *   *Targets*: Dotted 8th (0.75 beats), Dotted 4th (1.5 beats), Dotted Half (3.0 beats).

## 3. Implementation Status

| Feature | Logic Implemented | Verified (Test Script) | Applied to Generation |
| :--- | :---: | :---: | :---: |
| **Key/Scale Logic** | ✅ | ✅ (`check_diatonic_full.py`) | ✅ (Chord Selection) |
| **Harmonic Minor** | ✅ | ✅ (`check_advanced_minor.py`) | ✅ (Chord Selection) |
| **Octave Norm** | ✅ | ✅ (`check_analysis.py`) | ✅ (Voicing Stability) |
| **Groove Detect** | ✅ | ✅ (`check_rhythm_analysis.py`) | ❌ (Ready for V2) |
| **Mute Detect** | ✅ | ✅ (< 0.02s verified) | ❌ (Ready for V2) |
| **Syncopation** | ✅ | ✅ | ❌ (Ready for V2) |

**Note**: "Applied to Generation" means the current output MIDI files actively change based on this analysis. Features marked ❌ are analyzed but not yet driving the generator's output style (e.g., Mute notes still generate chords currently).

## 4. Known Limitations / Future Work
*   **Dynamics**: No logic yet for `ff` vs `pp` (Velocity analysis).
*   **Pitch Bends**: Ignored.
*   **Triplet Feel**: Shuffle/Swing detection is not yet implemented (requires Swing Ratio analysis).
