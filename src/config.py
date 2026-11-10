"""Load and save the game's configuration."""

import json
from typing import Any

import text_display


class Config:
    """Load, validate, and save the game's configuration settings."""

    DEFAULT_DATA: dict[str, Any] = {
        "clear_terminal": True,
        "text_formatting": True,
        "concatenate_dialogue": False,
        "wrap_text": True,
        "mark_visited": True,
        "last_save_file": "",
    }

    def __init__(self, display: text_display.TextDisplay) -> None:
        """Create a config manager with default settings and a display."""
        self.display = display
        self.filename = "config.json"
        self.data: dict[str, Any] = self.DEFAULT_DATA.copy()

    def load_config(self) -> dict[str, Any]:
        """Load settings from disk into this config instance."""
        create_config = False
        try:
            with open(self.filename, "r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}
            create_config = True
        except json.JSONDecodeError as error:
            self.display.text(
                self.display.format(
                    f"Error: Invalid JSON in '{self.filename}': {error}. Using defaults.",
                    ansi_format="error",
                )
            )
            data = {}
        except OSError as error:
            self.display.text(
                self.display.format(
                    f"Error: Could not read '{self.filename}': {error}. Using defaults.",
                    ansi_format="error",
                )
            )
            data = {}

        if not isinstance(data, dict):
            self.display.text(
                self.display.format(
                    f"Error: Configuration in '{self.filename}' must be a JSON object. "
                    "Using defaults.",
                    ansi_format="error",
                )
            )
            data = {}

        # Merge defaults before validating so newly added settings are available.
        config_data = self.DEFAULT_DATA.copy()
        config_data.update(data)
        for key, default_value in self.DEFAULT_DATA.items():
            if type(config_data[key]) is not type(default_value):
                self.display.text(
                    self.display.format(
                        f"Error: Invalid value for '{key}' in '{self.filename}'. "
                        "Using the default.",
                        ansi_format="error",
                    )
                )
                config_data[key] = default_value

        self.data.clear()
        self.data.update(config_data)

        if create_config:
            self.save_config()

        return self.data

    def save_config(self) -> None:
        """Save this config instance's settings to disk."""
        try:
            with open(self.filename, "w", encoding="utf-8") as file:
                json.dump(self.data, file, indent=4)
        except (OSError, TypeError, ValueError) as error:
            self.display.text(
                self.display.format(
                    f"Error: Could not save configuration to '{self.filename}': {error}",
                    ansi_format="error",
                )
            )
