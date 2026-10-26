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
    try:
        with open(filename, "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        with open(filename, "w") as file:
            json.dump(default_data, file, indent=4)
        data = default_data
    return data

def save_config(data: dict) -> None:
    """Saves the given data to config.json file."""
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)