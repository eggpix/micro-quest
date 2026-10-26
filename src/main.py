"""
Micro Quest is a text-based adventure game engine allowing users to create and
play their own text-based adventure stories.

In Micro Quest, each game is stored in a single JSON file containing all the
information about the game, including the story, choices, and outcomes. Players
can load these files into the Micro Quest engine to play through the adventure.
"""

import argparse
import json
import os
from pydoc import text

import config
import text_display

def main():
    parser = argparse.ArgumentParser(
        description="Micro Quest: A text-based adventure game engine."
    )
    parser.add_argument("-f", "--file", help="Quickly load a game from file path")
    args = parser.parse_args()

    game = Game()
    game.run(args.file)

class Game:
    """Main game class."""

    def __init__(self) -> None:
        self.game_data: dict | None = None
        self.config = config.load_config()
        self.display = text_display.TextDisplay(self.config)

    def play_game(self) -> None:
        """Main loop for quest game."""
        if self.config["clear_terminal"]:
            self.display.clear_terminal()
        self.display.display_title(self.game_data["title"])
        self.display.display_dialogue(self.game_data["description"], clear=False)
        input("... ")

    def open_json_file(self, file_path: str) -> dict | None:
        """Opens a JSON file and returns its contents as a dictionary."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                try:
                    data = json.load(file)
                    return data
                except json.decoder.JSONDecodeError:
                    print("There was a formatting error in the file you requested.")
                    input("... ")
                    return None
        except FileNotFoundError:
            print("The file you requested does not exist.")
            input("... ")
            return None

    def get_game_file(self) -> bool:
        while True:
            if self.config["clear_terminal"]:
                self.display.clear_terminal()
            print("Input the file path of your game to get started.")
            print(f"Current working directory: {os.getcwd()}")
            print("[0] Cancel")
            file_path = input("> ")
            if file_path == "0":
                return False
            else:
                data = self.open_json_file(file_path)
                if data is not None:
                    self.game_data = data
                    return True

    def run(self, file_path: str | None = None) -> None:
        """Runs main game loop"""
        if file_path is not None:
            data = self.open_json_file(file_path)
            if data is not None:
                self.game_data = data
                self.play_game()
        else:
            while True:
                primary_options = {"1":"Load Game", "0":"Exit"}
                primary_menu = text_display.ListMenu("Welcome to Micro Quest!", primary_options, self.display)
                selection = primary_menu.get_input()
                match selection:
                    case "0":
                        return
                    case "1":
                        if self.get_game_file():
                            self.play_game()
                        else:
                            continue

if __name__ == "__main__":
    main()
