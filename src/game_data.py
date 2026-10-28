
"""Game data management for Micro Quest."""

import json
from typing import Any

import text_display


class GameData:
    """Load, update, and save the current game's data."""

    def __init__(self, display: text_display.TextDisplay | None = None) -> None:
        """Initialize empty game data and an optional output display."""
        self.data: dict[str, Any] | None = None
        self.data_path: str | None = None
        self.display = display or text_display.TextDisplay(
            {"text_formatting": True, "wrap_text": False}
        )

    def load_game_file(self, file_path: str) -> bool:
        """Load a JSON game file, returning whether it was valid and readable."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                new_data = json.load(file)

            if not isinstance(new_data, dict):
                self.display.text(
                    self.display.error("Error: Game data must be a JSON object.")
                )
                return False

            self.data = new_data
            self.data_path = file_path
            return True
        except FileNotFoundError:
            self.display.text(
                self.display.error(
                    f"Error: The file '{file_path}' was not found."
                )
            )
        except json.JSONDecodeError:
            self.display.text(
                self.display.error(
                    f"Error: The file '{file_path}' contains invalid JSON."
                )
            )
        except OSError as error:
            self.display.text(
                self.display.error(
                    f"Error: Could not read file '{file_path}': {error}"
                )
            )

        return False

    def save_game_file(self) -> bool:
        """Save game data to its currently loaded file."""
        if self.data is None or self.data_path is None:
            self.display.text(
                self.display.error("Error: No game data loaded to save.")
            )
            return False

        try:
            with open(self.data_path, "w", encoding="utf-8") as file:
                json.dump(self.data, file, indent=4)
            return True
        except (OSError, TypeError, ValueError) as error:
            self.display.text(
                self.display.error(f"Error: Could not save game data: {error}")
            )
            return False

    def copy_game_file(self, file_path: str) -> bool:
        """Create a new game file without overwriting an existing file."""
        if self.data is None:
            self.display.text(
                self.display.error("Error: No game data loaded to save.")
            )
            return False

        try:
            with open(file_path, "x", encoding="utf-8") as file:
                json.dump(self.data, file, indent=4)
            self.data_path = file_path
            return True
        except (OSError, TypeError, ValueError) as error:
            self.display.text(
                self.display.error(
                    f"Error: Could not create game file '{file_path}': {error}"
                )
            )
            return False
