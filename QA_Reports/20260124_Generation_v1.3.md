# QA Report: V1.3 Beat-Quantized Generation

## 1. Task Overview
- **Objective**: Implement "Beat-Quantized" chord generation to stabilize harmony on moving bass lines.
- **User Request**: "Base generation on beats/windows to avoid chord chaos on passing notes."

## 2. Implementation Details
### Modified Files
- `scripts/midi_ensemble_generator.py`: Major refactor of `generate` loop.

### Logic Explanation
1.  **Grouping**:
    -   Uses `pretty_midi.get_beats()` to define beat intervals (e.g., 0.0-0.5s).
    -   Groups all Bass analysis results into these intervals.
2.  **Dominant Root Selection**:
    -   For each beat, selects the "Winner" bass note based on **Duration** (primary) and **Velocity** (secondary).
    -   *Result*: Short passing notes are ignored for chord calculation.
3.  **Style Application**:
    -   **Pad**: Generates **one sustained chord** per beat (filling the interval).
    -   **Rhythm/Arp**: Generates notes **matching input bass rhythm**, but forces the pitch to match the **Beat's Chord**.
    -   *Effect*: A complex funk bass line (16ths) will produce tight 16th-note backing chords that stay on "Dm7" for the whole beat, rather than flashing "Dm-F-G-Dm".

## 3. Verification Results
- **Test Script**: `scripts/check_beat_generation.py`
- **Scenario**:
    -   Input: C Major Arpeggio Bass (C, E, G, C) played as 16th notes within 1 beat.
    -   Old Logic: Would generate C Maj -> E min -> G Maj -> C Maj.
    -   New Logic: Should detect "C" as dominant (?) -> Generate C Major for all 4 notes.
- **Results**:
    ```
    Rhythm Note Count: 12 (4 chords x 3 notes)
    Chord 2 Pitches (at E bass position): [48, 52, 55] (C Major 1st Inv)
    [PASS] Harmony Stabilization: Chord 2 is C Major (not E Minor).
    ```
- **Self-Assessment**:
    - [x] Harmony stabilized per beat.
    - [x] Rhythm preserved (Style follows bass onset).
    - [!] Limitation: Input MIDI must be long enough for `pretty_midi` to detect beat grid (>1 measure recommended).

## 4. For AI Evaluation (他AI採点用プロンプト)

> **System Prompt Context**: You are an expert Audio Engineer. Evaluate this logic.
>
> **Update Summary**:
> The generator now creates an "Ensemble" by harmonizing the **Beat Center** rather than the individual note.
> - **Algorithm**: Notes grouped by Beat Grid -> Dominant Note (Longest) determines Chord -> Chord applied to all rhythmic onsets in that beat.
> - **Benefit**: Removes "Mickey-Mousing" (chord changing with every passing note) and creates a cohesive backing track.
>
> **Known Limitations**:
> - If the bass plays a genuine chord change *off-beat* (syncopation pushing the change early), this logic might quantize it late (to the next beat) or miss it if the previous note was longer.
>
> **Question**:
> Does this "Majority Vote" approach for Root selection risk missing fast harmonic rhythms in Jazz? Should "First Note of Beat" be weighted higher than "Longest Note"?
