"""Tests for creating active saves from template games."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import game_data
import main_menu
from tests.support import RecordingDisplay


class MainMenuTests(unittest.TestCase):
    def test_loading_template_creates_separate_active_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            template_path = directory / "adventure.json"
            save_path = directory / "my_save.json"
            template = {
                "title": "Adventure",
                "status": "template",
                "player": {"region": "start", "room_position": [0, 0]},
                "regions": {"start": {"rooms": {"0,0": {}}}},
            }
            template_path.write_text(json.dumps(template), encoding="utf-8")

            display = RecordingDisplay()
            manager = game_data.GameData(display)
            config = SimpleNamespace(
                data={"last_save_file": ""},
                save_config=lambda: None,
            )
            menu = main_menu.MainMenu(
                display, config, manager, lambda: None, lambda: None
            )

            with patch("builtins.input", return_value=str(save_path)):
                self.assertTrue(menu.load_game(str(template_path)))

            saved_template = json.loads(template_path.read_text(encoding="utf-8"))
            active_save = json.loads(save_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_template["status"], "template")
            self.assertEqual(active_save["status"], "active")
            self.assertEqual(manager.data_path, str(save_path))
            self.assertEqual(config.data["last_save_file"], str(save_path))

    def test_template_copy_cancel_does_not_create_save(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            template_path = Path(temporary_directory) / "adventure.json"
            template_path.write_text(
                json.dumps({"status": "template"}), encoding="utf-8"
            )
            display = RecordingDisplay()
            manager = game_data.GameData(display)
            config = SimpleNamespace(data={"last_save_file": ""})
            menu = main_menu.MainMenu(
                display, config, manager, lambda: None, lambda: None
            )
            self.assertTrue(manager.load_game_file(str(template_path)))

            with patch("builtins.input", return_value="0"):
                self.assertFalse(menu.copy_template(str(template_path)))

            self.assertEqual(manager.data["status"], "template")
            self.assertEqual(config.data["last_save_file"], "")


if __name__ == "__main__":
    unittest.main()
