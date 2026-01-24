# QA Report: V1.5 Refinements (Phase 2)

## 1. Task Overview
- **Objective**: Fix "Garbage Notes" in Arpeggio and ensure precise Tempo Sync.
- **User Request**: "Arpeggio generates trash notes at the end of duration. It should also follow the MIDI file's Tempo map."

## 2. Implementation Details
### Modified Files
- `scripts/midi_ensemble_generator.py`:
    -   **`get_tempo_at_time`**: Added utility to query `pretty_midi.get_tempo_changes()` correctly.
    -   **`ArpStyle.apply`**:
        -   Calculates `step_duration` based on the BPM at the exact moment of generation (Dynamic Tempo).
        -   Logic: `60 / bpm / 4` (16th note).
    -   **Garbage Exclusion**:
        -   If `remaining_time < step_duration * 0.5`, the loop breaks early.
        -   This prevents trying to squeeze a 16th note into a 10ms gap.

## 3. Verification Results
- **Test Script**: `scripts/check_v1_5_tempo.py`
- **Scenarios Checked**:
    1.  **Standard Tempo (120 BPM)**:
        -   Generated 16th note duration: `0.125s` (Matched).
    2.  **Slow Tempo (90 BPM)**:
        -   Generated duration: `0.1667s` (Matched).
    3.  **Fast Tempo (160 BPM)**:
        -   Generated duration: `0.0938s` (Matched).
    4.  **Garbage Exclusion**:
        -   Input: 0.52s duration (4 full 16ths + 0.02s tail).
        -   Output: 4 notes.
        -   Result: The 0.02s tail was correctly ignored.

## 4. Conclusion
Arpeggio generation is now robust against Tempo variations and varying note lengths. It will stay in sync with the song and sound clean at the end of phrases.
