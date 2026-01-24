# AI Evaluation Request: MIDI Generation Logic Suitability

**Context**: We are building a "MIDI Ensemble Generator" that automatically creates backing tracks (Chords, Arps, Pads) from a single Bass MIDI track.
**Objective**: Evaluate if the current algorithms are musically suitable for general Pop/Rock/Game Music production, and identify logical flaws or areas for improvement.

---

## 1. Core Harmony Logic (The "Brain")

The system determines *what chord to play* based on the input Bass line.

### A. Beat-Based Quantization (v1.3)
Instead of harmonizing every single bass note (which leads to chaotic changes on passing notes), we determine harmony **per Beat**.
*   **Logic**:
    1.  Group input bass notes by Beat intervals (e.g., 0.0-0.5s).
    2.  Select the **Dominant Note** for that beat:
        *   Priority 1: Longest Duration.
        *   Priority 2: Highest Velocity.
    3.  The Chord Root is derived from this Dominant Note. All accompaniment for that beat uses this single Root.

### B. Chord Construction Strategies
Once the Root is decided, we construct the chord tones.
1.  **Strategy "Maj" (Legacy)**:
    *   **Logic**: Always generate a **Major Triad** (Root, M3, P5).
    *   *Intention*: Simple, happy feeling (or for testing).
2.  **Strategy "Diatonic" (Standard)**:
    *   **Logic**: Detect Key (e.g., C Minor). Map Root to Scale Degree. Build **Diatonic Triad** (e.g., If Root is D in C Minor -> D Diminished).
    *   *Scale Support*: Major, Natural Minor, Harmonic Minor.

### C. Chord Merging (v1.4)
*   **Logic**: If adjacent beats produce the **exact same code** (e.g., Beat 1 is C Maj, Beat 2 is C Maj), they are fused into a single "Harmonic Event".
*   *Purpose*: To allow Pads to sustain over bar lines or beats without re-triggering.

---

## 2. Voicing Patterns (The "Vertical Structure")

How notes are stacked vertically. Input Bass note is $R$ (e.g., C2).

1.  **Closed Voicing**:
    *   **Stack**: $R+12$ (Root), $3rd$, $5th$. (All within one octave).
    *   *Range*: Low-Mid (C3 range).
2.  **Open Voicing**:
    *   **Stack**: $R+12$ (Root), $5th$, $3rd+12$ (Tenth).
    *   *Range*: Spread across >1 octave. Used to avoid muddiness.

---

## 3. Style Algorithms (The "Horizontal Structure")

How notes are placed in time based on the "Harmonic Event" or "Bass Rhythm".

### A. Pad Style
*   **Source**: **Merged Events** (Long durations).
*   **Logic**: Generate a chord that starts at Event Start and ends at Event End.
*   **Musical Effect**: Long, sustained "Whole Note" feel. No rhythmic movement.
*   **Velocity**: Fixed (Derived from Bass velocity).

### B. Rhythm Style
*   **Source**: **Original Bass Notes** (Rhythmic Onsets).
*   **Logic**:
    *   For every note in the bass line:
        *   Take its timing (Start, End) and Velocity.
        *   Take the **Beat Chord** calculated in Step 1.
        *   Generate a block chord (all voices simultaneously) at that timing.
    *   *Result*: "Chord Stabs" that perfectly lock to the bass groove.

### C. Arp Style
*   **Source**: **Original Bass Notes**.
*   **Logic**:
    *   Similar to Rhythm, but instead of playing the chord as a block, it plays a **16th-note sequence**.
    *   **Pattern**: Cycles through chord tones (Root -> 3rd -> 5th -> Root...) upward loop.
    *   **Duration**: Fills the duration of the bass note with 16ths.
    *   *Result*: Automated arpeggio running while the bass note is held.

---

## 4. Evaluation Request (採点依頼)

Please evaluate these algorithms 1-10 on **"Musical Suitability"** and provide critiques.

**Question 1: The "Dominant Note" Logic**
*   *Current*: Longest note wins.
*   *Critique*: Is this safe? If a Bass plays a short "Downbeat Root" (staccato) followed by a long "Syncopated Pickup to next chord", will this logic mistakenly harmonize the Pickup?

**Question 2: Arp Generator**
*   *Current*: Simple Up-Cycle (R-3-5).
*   *Critique*: Is this too robotic? Should it reset every beat? Or respect the Beat Grid (e.g., R on strong beats)?

**Question 3: Rhythm Style (Block Chords)**
*   *Current*: Every bass note triggers a full triad.
*   *Critique*: For a fast 16th bass line (Funk), does playing full triads on every 16th note create "Mud"? Should it be thinned out?

**Question 4: Missing Elements**
*   What is the #1 most critical logic missing to make this sound like a "Pro" producer's output? (e.g., Inversions? Voice Leading?)
