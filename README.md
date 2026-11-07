# gps-music-pythonista

A Python script for **Pythonista 3** on iOS that reads the device's GPS coordinates and randomly plays `.aif` / `.aiff` audio files every 2 seconds based on your physical location.

---

## Features

- **GPS-Driven Sound Selection:** The real world is mapped to a spatial grid (default: 50m cells). Each grid cell deterministically determines an active sound palette from your audio files.
- **2-Second Generative Interval:** Every 2 seconds, the script selects and plays an audio file randomly from the current location's active palette.
- **Pythonista 3 Native Integration:**
  - Uses Pythonista's native `location` module for GPS updates (`location.start_updates()`, `location.get_location()`).
  - Uses Apple's native `AVAudioPlayer` framework via `objc_util` (with fallback to `sound.Player`) for reliable, overlapping playback.
  - Automatically configures `AVAudioSession` (`AVAudioSessionCategoryPlayback`) so audio plays even when the device silent switch is enabled or when backgrounded.
  - Automatically shuts down GPS hardware on exit (`location.stop_updates()`) to preserve battery life.
- **Cross-Platform / Simulator Support:** Can also run on macOS or Linux for testing, with built-in GPS drift simulation and `afplay` playback.
- **Included Sample Audio:** Includes 5 synthesized tone `.aif` files in `sample_audio/` so you can test immediately.

---

## Quick Start on Pythonista 3 (iOS)

1. **Copy `gps_music.py` and your `.aif` files to Pythonista 3**:
   - You can git clone this repository into Pythonista using [Working Copy](https://workingcopy.app) or [StaSh](https://github.com/ywangd/stash).
   - Alternatively, create a new script in Pythonista named `gps_music.py` and copy-paste the contents of [`gps_music.py`](gps_music.py).
2. **Audio Directory**:
   - Place your `.aif` or `.aiff` files in a folder named `audio/` or `sample_audio/` in the same directory as `gps_music.py`.
3. **Run**:
   - Open `gps_music.py` in Pythonista 3.
   - Tap the **Play (▶)** button.
   - When prompted by iOS, allow Location access ("While Using the App" or "Always").
   - Watch the console output showing your current coordinates, spatial grid cell, and currently playing audio file.
4. **Stop**:
   - Tap the **Stop (■)** button in Pythonista to gracefully stop playback and deactivate GPS updates.

---

## How Location-Based Playback Works

```
        Physical World (Lat, Lon)
                   │
                   ▼
       [ Spatial Grid Quantization ]  (e.g., ~50m cells)
                   │
                   ▼
     [ Deterministic Cell Palette ]   (Sub-pool of N audio files)
                   │
                   ▼
   [ Random Selection Every 2s ]     (Plays random .aif from pool)
```

1. **Grid Cells:** The script calculates a 2D integer cell `(grid_x, grid_y)` from your latitude and longitude.
2. **Deterministic Palette:** A cryptographic hash of the cell coordinates seeds a selection of audio files (default 4 files per cell).
3. **Random Playback:** Every 2 seconds, a file is chosen at random from the active cell's palette. When you stay in one area, you hear a cohesive ambient palette. When you walk or travel into a new cell, the palette transitions to new sounds.

---

## Configuration

You can customize parameters directly at the top of [`gps_music.py`](gps_music.py) or pass command-line arguments:

| Setting | Default | Description |
|---|---|---|
| `DEFAULT_AUDIO_DIR` | `"sample_audio"` | Path to the directory containing `.aif`/`.aiff` files |
| `DEFAULT_INTERVAL` | `2.0` | Interval between plays in seconds |
| `DEFAULT_GRID_SIZE_METERS` | `50.0` | Physical size in meters for each spatial grid cell |
| `DEFAULT_PALETTE_SIZE` | `4` | Number of files assigned to each cell's active palette |
| `DEFAULT_VOLUME` | `1.0` | Playback volume (`0.0` to `1.0`) |

### Command-Line Arguments (Optional)

If running via StaSh or desktop terminal:

```bash
python3 gps_music.py --dir sample_audio --interval 2.0 --grid-size 50.0 --volume 0.8
```

Options:
- `--dir`, `-d`: Path to directory of `.aif` files.
- `--interval`, `-i`: Play interval in seconds (default: 2.0).
- `--grid-size`, `-g`: Grid cell size in meters (default: 50.0).
- `--palette-size`, `-p`: Active sound palette size per cell (default: 4).
- `--volume`, `-v`: Volume between 0.0 and 1.0 (default: 1.0).
- `--player`: Audio backend: `auto` (prefers `AVAudioPlayer` > `sound` > `desktop`), `avplayer`, `sound`, or `desktop` (default: `auto`).
- `--simulate-gps`: Force simulated GPS drift (useful off-device).
- `--max-ticks`: Automatically exit after N playback cycles.

---

## Testing & Development

Run unit tests locally:

```bash
python3 -m unittest discover -s tests
```

Run a 3-cycle test on macOS / desktop:

```bash
python3 gps_music.py --max-ticks 3
```

---

## iOS Permissions & Tips

- **Location Permissions:** When running for the first time, iOS will display a prompt asking for permission to use your location. Grant permission so Pythonista can access the device GPS.
- **Background Audio:** To keep music playing while your device screen is locked or while switching apps, ensure Pythonista's background audio option is enabled in iOS Settings > Pythonista.
