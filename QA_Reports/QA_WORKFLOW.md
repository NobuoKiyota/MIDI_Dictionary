# QA Workflow Definition

To ensure high quality and facilitate external AI evaluation, all major implementation steps must be documented in the `QA_Reports` directory.

## Directory Structure
`z:\MIDI_Dictionary\QA_Reports\`
- `YYYYMMDD_TaskName.md` (e.g., `20260124_RhythmAnalysis_v1.3.md`)

## Report Template
Each report must contain the following sections:

### 1. Task Overview (概要)
- **Objective**: What was implemented?
- **User Request**: Context from the user.

### 2. Implementation Details (実装詳細)
- **Key Changes**:
    - List of modified files and logic.
    - *Example*: "Updated `detect_key` to check for Mixolydian intervals."
- **Logic Explanation**:
    - Brief explanation of the algorithms used.

### 3. Verification Results (検証結果)
- **Test Script**: Name of the script run (e.g., `scripts/check_rhythm.py`).
- **Logs/Output**: Paste relevant parts of the success output.
- **Self-Assessment**:
    - [x] Logic behaves as expected.
    - [ ] Dynamic thresholds fine-tuned?

### 4. For AI Evaluation (他AI採点用プロンプト)
*A standalone text block summarizing the update for another AI to review.*

> **System Prompt Context**: You are an expert Music Theory AI. Evaluate the following logic update.
>
> **Update Summary**:
> [Insert Summary Here]
>
> **Known Limitations**:
> [Insert Limitations]
>
> **Question**:
> Does this logic correctly handle [specific case]? Are there potential edge cases with Bass-only MIDI?

## Usage
1.  Complete the Implementation task.
2.  Run Verification.
3.  **BEFORE** calling `notify_user` to finish the task, create this QA Report.
4.  Include the path to the QA Report in the `notify_user` call.
