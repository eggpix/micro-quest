"""Loads config.json file for use in the game engine."""

import json

filename = "config.json"
default_data = {
    "clear_terminal": True,
    "text_formatting": True,
    "concatenate_dialogue": False,
    "wrap_text": True,
    "last_save_file": ""
}


def load_config() -> dict:
    """Loads config.json file and returns its contents as a dictionary."""
    create_config = False
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}
        create_config = True
    except json.JSONDecodeError as error:
        print(f"Error: Invalid JSON in '{filename}': {error}. Using defaults.")
        data = {}
    except OSError as error:
        print(f"Error: Could not read '{filename}': {error}. Using defaults.")
        data = {}

    if not isinstance(data, dict):
        print(
            f"Error: Configuration in '{filename}' must be a JSON object. "
            "Using defaults."
        )
        data = {}

    config_data = default_data.copy()
    config_data.update(data)
    for key, default_value in default_data.items():
        if type(config_data[key]) is not type(default_value):
            print(
                f"Error: Invalid value for '{key}' in '{filename}'. "
                "Using the default."
            )
            config_data[key] = default_value

    if create_config:
        save_config(config_data)

    return config_data


def save_config(data: dict) -> None:
    """Saves the given data to config.json file."""
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)