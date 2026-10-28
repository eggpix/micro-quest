
"""Game data management for Micro Quest."""

import json
from typing import Any

import text_display


class GameData:
    """Class to manage game data."""

    def __init__(self, display: text_display.TextDisplay | None = None) -> None:
        self.data: dict[str, Any] | None = None
        self.data_path: str | None = None
        self.display = display or text_display.TextDisplay(
            {"text_formatting": True, "wrap_text": False}
        )

    def update_game_data(self, new_data: dict[str, Any]) -> bool:
        """Update the current game data with new data."""
        if self.data is None:
            self.display.text(
                self.display.error("Error: No game data loaded to update.")
            )
            return False

        self.data.update(new_data)
        return True

    def load_game_file(self, file_path: str) -> bool:
        """Load game data from a JSON file."""
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
        """Save the current game data to its loaded file."""
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

    def save_game_file_as(self, file_path: str) -> bool:
        """Save the current game data as a new file without overwriting."""
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
