"""
Unit tests for gps_music.py
"""

import math
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import gps_music
from gps_music import (
    AVAudioPlayerAudioPlayer,
    BaseAudioPlayer,
    BaseLocationProvider,
    DesktopAudioPlayer,
    GPSMusicApp,
    PythonistaAudioPlayer,
    SimulatedLocationProvider,
    coord_to_grid,
    find_audio_files,
    get_cell_palette,
    parse_args,
    setup_audio_session,
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

    def test_audio_backend_selection_desktop(self):
        app = GPSMusicApp(
            audio_dir=self.audio_dir,
            audio_backend="desktop",
        )
        self.assertIsInstance(app.audio_player, DesktopAudioPlayer)

    def test_audio_backend_selection_avplayer(self):
        with patch.object(gps_music, "HAS_OBJC_AV_AUDIO", True), \
             patch.object(gps_music, "AVAudioSession", MagicMock()):
            app = GPSMusicApp(
                audio_dir=self.audio_dir,
                audio_backend="avplayer",
            )
            self.assertIsInstance(app.audio_player, AVAudioPlayerAudioPlayer)

    def test_audio_backend_selection_sound(self):
        with patch.object(gps_music, "HAS_PYTHONISTA_SOUND", True):
            app = GPSMusicApp(
                audio_dir=self.audio_dir,
                audio_backend="sound",
            )
            self.assertIsInstance(app.audio_player, PythonistaAudioPlayer)


class TestAVAudioPlayerAudioPlayer(unittest.TestCase):
    def setUp(self):
        self.mock_session_class = MagicMock()
        self.mock_session = MagicMock()
        self.mock_session_class.sharedInstance.return_value = self.mock_session

        self.mock_player_class = MagicMock()
        self.mock_player_alloc = MagicMock()
        self.mock_player_instance = MagicMock()
        self.mock_player_class.alloc.return_value = self.mock_player_alloc
        self.mock_player_alloc.initWithContentsOfURL_error_.return_value = self.mock_player_instance
        self.mock_player_instance.play.return_value = True

        self.mock_nsurl = MagicMock(side_effect=lambda path: f"file://{path}")

    def test_setup_audio_session_success(self):
        with patch.object(gps_music, "HAS_OBJC_AV_AUDIO", True), \
             patch.object(gps_music, "AVAudioSession", self.mock_session_class):
            success = setup_audio_session()
            self.assertTrue(success)
            self.mock_session.setCategory_error_.assert_called_once_with(
                "AVAudioSessionCategoryPlayback", None
            )
            self.mock_session.setActive_error_.assert_called_once_with(True, None)

    def test_setup_audio_session_failure_returns_false(self):
        with patch.object(gps_music, "HAS_OBJC_AV_AUDIO", True), \
             patch.object(gps_music, "AVAudioSession", self.mock_session_class):
            self.mock_session.setCategory_error_.side_effect = RuntimeError("Session error")
            success = setup_audio_session()
            self.assertFalse(success)

    def test_setup_audio_session_not_available(self):
        with patch.object(gps_music, "HAS_OBJC_AV_AUDIO", False):
            success = setup_audio_session()
            self.assertFalse(success)

    def test_play_and_retention(self):
        with patch.object(gps_music, "HAS_OBJC_AV_AUDIO", True), \
             patch.object(gps_music, "AVAudioPlayer", self.mock_player_class), \
             patch.object(gps_music, "AVAudioSession", self.mock_session_class), \
             patch.object(gps_music, "nsurl", self.mock_nsurl):
            player = AVAudioPlayerAudioPlayer(max_concurrent=2, configure_session=True)
            self.mock_session.setCategory_error_.assert_called_once()

            file1 = Path("sample_1.aif")
            player.play(file1, volume=0.75)

            self.mock_nsurl.assert_called_once_with(str(file1.resolve()))
            self.mock_player_instance.setVolume_.assert_called_once_with(0.75)
            self.mock_player_instance.prepareToPlay.assert_called_once()
            self.mock_player_instance.play.assert_called_once()
            self.assertEqual(len(player._players), 1)

            # Play two more files to verify bounded deque behavior
            file2 = Path("sample_2.aif")
            file3 = Path("sample_3.aif")
            player.play(file2)
            player.play(file3)
            # max_concurrent is 2, so queue length should stay 2
            self.assertEqual(len(player._players), 2)

    def test_stop_all(self):
        with patch.object(gps_music, "HAS_OBJC_AV_AUDIO", True), \
             patch.object(gps_music, "AVAudioPlayer", self.mock_player_class), \
             patch.object(gps_music, "AVAudioSession", self.mock_session_class), \
             patch.object(gps_music, "nsurl", self.mock_nsurl):
            player = AVAudioPlayerAudioPlayer(max_concurrent=4, configure_session=False)
            instance1 = MagicMock()
            instance2 = MagicMock()
            player._players.append(instance1)
            player._players.append(instance2)

            player.stop_all()
            instance1.stop.assert_called_once()
            instance2.stop.assert_called_once()
            self.assertEqual(len(player._players), 0)


class TestCommandLineArgs(unittest.TestCase):
    def test_parse_player_argument(self):
        args = parse_args(["--player", "avplayer"])
        self.assertEqual(args.player, "avplayer")

        args = parse_args(["--player", "sound"])
        self.assertEqual(args.player, "sound")

        args = parse_args(["--player", "desktop"])
        self.assertEqual(args.player, "desktop")

        args = parse_args([])
        self.assertEqual(args.player, "auto")


if __name__ == "__main__":
    unittest.main()
