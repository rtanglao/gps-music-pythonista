"""
Unit tests for gps_music.py
"""

import math
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from gps_music import (
    BaseAudioPlayer,
    BaseLocationProvider,
    GPSMusicApp,
    SimulatedLocationProvider,
    coord_to_grid,
    find_audio_files,
    get_cell_palette,
)


class TestFindAudioFiles(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_find_aif_files_case_insensitive(self):
        # Create various files
        (self.test_path / "one.aif").touch()
        (self.test_path / "two.AIFF").touch()
        (self.test_path / "three.aiff").touch()
        (self.test_path / "ignore.txt").touch()
        (self.test_path / "ignore.mp3").touch()

        # Nested directory
        sub = self.test_path / "sub"
        sub.mkdir()
        (sub / "nested.AIF").touch()

        files = find_audio_files(self.test_path)
        filenames = [f.name for f in files]

        self.assertEqual(len(filenames), 4)
        self.assertIn("one.aif", filenames)
        self.assertIn("two.AIFF", filenames)
        self.assertIn("three.aiff", filenames)
        self.assertIn("nested.AIF", filenames)
        self.assertNotIn("ignore.txt", filenames)
        self.assertNotIn("ignore.mp3", filenames)

    def test_missing_directory_raises(self):
        with self.assertRaises(FileNotFoundError):
            find_audio_files(self.test_path / "non_existent")


class TestCoordinateGrid(unittest.TestCase):
    def test_coord_to_grid_consistency(self):
        lat, lon = 37.774929, -122.419416
        cell1 = coord_to_grid(lat, lon, grid_size_meters=50.0)
        # Small shift (~1 meter) should stay in the same cell
        cell2 = coord_to_grid(lat + 0.000005, lon + 0.000005, grid_size_meters=50.0)
        self.assertEqual(cell1, cell2)

    def test_coord_to_grid_boundary_shift(self):
        lat, lon = 37.774929, -122.419416
        cell1 = coord_to_grid(lat, lon, grid_size_meters=50.0)
        # Larger shift (~100 meters) should change cell
        cell_shifted = coord_to_grid(lat + 0.001, lon, grid_size_meters=50.0)
        self.assertNotEqual(cell1, cell_shifted)


class TestCellPalette(unittest.TestCase):
    def setUp(self):
        self.files = [Path(f"sound_{i}.aif") for i in range(10)]

    def test_palette_determinism(self):
        cell = (100, -200)
        palette1 = get_cell_palette(self.files, cell, palette_size=3)
        palette2 = get_cell_palette(self.files, cell, palette_size=3)
        self.assertEqual(palette1, palette2)
        self.assertEqual(len(palette1), 3)

    def test_palette_size_bounds(self):
        cell = (50, 50)
        # Size larger than available files returns all files
        full_palette = get_cell_palette(self.files, cell, palette_size=20)
        self.assertEqual(len(full_palette), len(self.files))

        # Size 0 returns all files
        all_files = get_cell_palette(self.files, cell, palette_size=0)
        self.assertEqual(len(all_files), len(self.files))

    def test_empty_files_list(self):
        palette = get_cell_palette([], (0, 0), palette_size=3)
        self.assertEqual(palette, [])


class DummyLocationProvider(BaseLocationProvider):
    def __init__(self, locations):
        self.locations = list(locations)
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def get_location(self):
        if self.locations:
            return self.locations.pop(0)
        return None

    def stop(self):
        self.stopped = True


class DummyAudioPlayer(BaseAudioPlayer):
    def __init__(self):
        self.played = []
        self.stopped = False

    def play(self, file_path, volume=1.0):
        self.played.append((file_path, volume))

    def stop_all(self):
        self.stopped = True


class TestGPSMusicApp(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.audio_dir = Path(self.test_dir)
        for i in range(5):
            (self.audio_dir / f"test_{i}.aif").touch()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_tick_with_location(self):
        loc = {
            "latitude": 49.2827,
            "longitude": -123.1207,
            "horizontal_accuracy": 5.0,
        }
        loc_provider = DummyLocationProvider([loc])
        audio_player = DummyAudioPlayer()

        app = GPSMusicApp(
            audio_dir=self.audio_dir,
            interval=0.01,
            grid_size_meters=50.0,
            palette_size=3,
            volume=0.8,
            location_provider=loc_provider,
            audio_player=audio_player,
        )

        selected = app.tick()
        self.assertIsNotNone(selected)
        self.assertEqual(len(audio_player.played), 1)
        played_file, volume = audio_player.played[0]
        self.assertEqual(played_file, selected)
        self.assertEqual(volume, 0.8)

    def test_tick_when_location_none(self):
        # When GPS fix is still acquiring (None)
        loc_provider = DummyLocationProvider([None])
        audio_player = DummyAudioPlayer()

        app = GPSMusicApp(
            audio_dir=self.audio_dir,
            location_provider=loc_provider,
            audio_player=audio_player,
        )

        selected = app.tick()
        self.assertIsNotNone(selected)
        self.assertEqual(len(audio_player.played), 1)

    def test_run_loop_and_cleanup(self):
        loc = {"latitude": 49.2827, "longitude": -123.1207}
        loc_provider = DummyLocationProvider([loc, loc, loc])
        audio_player = DummyAudioPlayer()

        app = GPSMusicApp(
            audio_dir=self.audio_dir,
            interval=0.001,
            location_provider=loc_provider,
            audio_player=audio_player,
        )

        app.run(max_ticks=3)
        self.assertTrue(loc_provider.started)
        self.assertTrue(loc_provider.stopped)
        self.assertTrue(audio_player.stopped)
        self.assertEqual(len(audio_player.played), 3)


if __name__ == "__main__":
    unittest.main()
