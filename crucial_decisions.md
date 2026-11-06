# Project Decisions & State: gps-music-pythonista

This artifact records all crucial decisions made during the setup and implementation of issue [#1](https://github.com/rtanglao/gps-music-pythonista/issues/1).

---

## 1. Architectural Decisions

| Area | Decision | Rationale |
|---|---|---|
| **Location Tracking** | Use Pythonista 3's built-in `location` module (`start_updates()`, `get_location()`). | Native, battery-efficient GPS access on iOS. Ensured `location.stop_updates()` is always called in `finally` blocks. |
| **Spatial Mapping** | Quantize coordinates to 2D grid cells (`coord_to_grid()`, ~50m default). | Prevents jitter from micro-drifts and creates distinct acoustic regions as the user walks through physical space. |
| **Audio Selection** | Deterministic cell hash seeds an active subset of `.aif` files; selection every 2 seconds is random from that subset. | Provides geographical sound palettes while preserving continuous generative variation. |
| **Audio Playback** | Use Pythonista's `sound.Player` with a bounded reference deque (`collections.deque(maxlen=8)`). | Standard library on iOS; reference queue prevents garbage collection from truncating playing audio. |
| **Interval Timing** | `time.monotonic()` sleep calculation targeting exact 2.0-second steps. | Immune to system wall-clock adjustments and compensates for loop execution drift. |
| **Cross-Platform** | Automatic fallback to `SimulatedLocationProvider` and `DesktopAudioPlayer` (`afplay`). | Allows rapid local development and automated testing outside iOS. |

---

## 2. Git & GitHub State

- **Issue:** [#1: Write Pythonista 3 script to randomly play an AIF file every 2 seconds based on GPS coordinates](https://github.com/rtanglao/gps-music-pythonista/issues/1) — **Closed**.
- **Commits:**
  - `f8818ba`: Implementation of [`gps_music.py`](file:///Users/roland/Documents/GIT/gps-music-pythonista/gps_music.py), [`README.md`](file:///Users/roland/Documents/GIT/gps-music-pythonista/README.md), sample audio files, and test suite.
  - `caa6c17`: Saved [`GEMINI.md`](file:///Users/roland/Documents/GIT/gps-music-pythonista/GEMINI.md) project memory file.
- **Branch:** `main` (clean, fully synced with remote).

---

## 3. Persistent Memory Location

- **Project Rules & Context:** Stored in [`GEMINI.md`](file:///Users/roland/Documents/GIT/gps-music-pythonista/GEMINI.md) at the repository root. Antigravity will automatically load this context in future sessions.
