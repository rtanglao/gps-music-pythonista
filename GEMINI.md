# Project Memory & Architecture Decisions: gps-music-pythonista

This document preserves the key architectural decisions, conventions, and implementation details for `gps-music-pythonista`.

---

## 1. Project Purpose & Target Environment
- **Platform:** Pythonista 3 on iOS (iPhone/iPad).
- **Core Functionality:** Every 2 seconds, sample the device GPS coordinates and randomly play an `.aif` / `.aiff` audio file from a designated audio folder based on geographic location.
- **Off-Device Development:** Supports local development and testing on macOS/Linux with simulated GPS drift and `afplay` desktop audio playback.

---

## 2. Key Architectural Decisions

### Spatial Grid Quantization & Palette Selection
- **Grid-Based Binning:** Real-world coordinates are mapped into discrete 2D spatial cells `(grid_x, grid_y)` using `coord_to_grid(lat, lon, grid_size_meters=50.0)`.
- **Deterministic Cell Palette:** Each cell `(grid_x, grid_y)` deterministically seeds a pseudo-random hash generator via `get_cell_palette()`. This maps each physical location to a consistent sub-pool (default: 4 sounds) from the available `.aif` files.
- **Generative Playback:** While in a given cell, every 2-second tick randomly picks from that cell's active palette. Moving across cell boundaries triggers a transition to a new palette.
- **Rationale:** Ensures spatial coherence (walking through a physical space feels like moving through distinct ambient sound zones) while retaining generative variety on each 2-second tick.

### Audio Playback & Pythonista Lifecycle
- **Native Audio Player:** Uses `sound.Player` from Pythonista's standard library on iOS.
- **GC Retention Buffer:** Active player instances are retained in a bounded `collections.deque(maxlen=8)` to prevent Python's garbage collector from destroying player instances prematurely and cutting off audio.
- **Clean Termination:** When the script exits or is interrupted (`KeyboardInterrupt`), all active players are stopped.
- **Desktop Fallback:** Uses macOS `afplay` via non-blocking subprocesses when `sound` is unavailable.

### GPS Tracking & Hardware Management
- **Lifecycle Cleanliness:** Uses `location.start_updates()` on startup and guarantees `location.stop_updates()` in a `try...finally` block. This prevents keeping the iOS GPS hardware active after exit and draining battery.
- **Graceful Acquisition:** If `location.get_location()` returns `None` while acquiring satellite fix, the script falls back gracefully to general pool playback without crashing.
- **Simulation Provider:** `SimulatedLocationProvider` generates a small random-walk drift for testing off-device.

### Interval Loop Timing
- **Drift Compensation:** Uses `time.monotonic()` to compute the exact sleep duration for the next 2.0-second boundary, resetting baseline if execution lags.

---

## 3. Repository Structure & Key Files
- `gps_music.py`: The self-contained main script, executable with zero setup in Pythonista 3.
- `sample_audio/`: Synthesized `.aif` tone files (`tone_c4.aif`, `tone_e4.aif`, `tone_g4.aif`, `tone_b4.aif`, `tone_c5.aif`).
- `tests/test_gps_music.py`: Unit test suite covering file scanning, grid math, palette determinism, mock location, and loop lifecycle.
- `README.md`: User-facing documentation including iOS setup, permission notes, background audio, and CLI options.

---

## 4. History & GitHub Tracking
- **Issue #1:** "Write Pythonista 3 script to randomly play an AIF file every 2 seconds based on GPS coordinates".
- **Resolution:** Implemented and pushed to `main` in commit `f8818ba`. Issue #1 closed.
