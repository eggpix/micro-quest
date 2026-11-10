"""Tests for reading and writing game files."""

import json
import tempfile
import unittest
from pathlib import Path

import game_data
from tests.support import RecordingDisplay


class GameDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.display = RecordingDisplay()
        self.manager = game_data.GameData(self.display)
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.directory = Path(self.temp_directory.name)

    def test_loads_json_object_and_records_source_path(self) -> None:
        path = self.directory / "game.json"
        expected = {"title": "Test Game", "player": {"inventory": {}}}
        path.write_text(json.dumps(expected), encoding="utf-8")

        self.assertTrue(self.manager.load_game_file(str(path)))
        self.assertEqual(self.manager.data, expected)
        self.assertEqual(self.manager.data_path, str(path))

    def test_rejects_malformed_json_without_replacing_loaded_data(self) -> None:
        path = self.directory / "broken.json"
        path.write_text('{"title":', encoding="utf-8")
        original_data = {"title": "Already loaded"}
        self.manager.data = original_data
        self.manager.data_path = "existing.json"

        self.assertFalse(self.manager.load_game_file(str(path)))
        self.assertIs(self.manager.data, original_data)
        self.assertEqual(self.manager.data_path, "existing.json")
        self.assertTrue(any("invalid JSON" in text for text in self.display.messages))

    def test_rejects_non_object_json(self) -> None:
        path = self.directory / "list.json"
        path.write_text("[]", encoding="utf-8")

        self.assertFalse(self.manager.load_game_file(str(path)))
        self.assertIsNone(self.manager.data)
        self.assertTrue(
            any("must be a JSON object" in text for text in self.display.messages)
        )

    def test_missing_file_returns_false(self) -> None:
        path = self.directory / "missing.json"

        self.assertFalse(self.manager.load_game_file(str(path)))
        self.assertTrue(any("was not found" in text for text in self.display.messages))

    def test_saves_current_data_and_can_reload_it(self) -> None:
        path = self.directory / "save.json"
        path.write_text("{}", encoding="utf-8")
        self.assertTrue(self.manager.load_game_file(str(path)))
        self.manager.data["completed"] = True

        self.assertTrue(self.manager.save_game_file())

        reloaded = game_data.GameData(self.display)
        self.assertTrue(reloaded.load_game_file(str(path)))
        self.assertEqual(reloaded.data, {"completed": True})

    def test_save_without_loaded_data_fails_visibly(self) -> None:
        self.assertFalse(self.manager.save_game_file())
        self.assertTrue(
            any("No game data loaded" in text for text in self.display.messages)
        )

    def test_copy_refuses_to_overwrite_unless_requested(self) -> None:
        path = self.directory / "copy.json"
        path.write_text('{"existing": true}', encoding="utf-8")
        self.manager.data = {"title": "New"}

        self.assertFalse(self.manager.copy_game_file(str(path)))
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"existing": True})

        self.assertTrue(self.manager.copy_game_file(str(path), overwrite=True))
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"title": "New"})
        self.assertEqual(self.manager.data_path, str(path))

    def test_copy_without_loaded_data_fails(self) -> None:
        path = self.directory / "copy.json"

        self.assertFalse(self.manager.copy_game_file(str(path)))
        self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
