"""
Micro Quest is a text-based adventure game engine allowing users to create and
play their own text-based adventure stories.

In Micro Quest, each game is stored in a single JSON file containing all the
information about the game, including the story, choices, and outcomes. Players
can load these files into the Micro Quest engine to play through the adventure.
"""

import text_display
import config
import os
import json

class Game:
    """Main game class."""

    def __init__(self) -> None:
        self.game_data: dict = None
        self.config = config.load_config()

    def play_game(self) -> None:
        """Main loop for quest game."""
        if self.config["clear_terminal"]:
            text_display.clear_terminal()
        print("Game is running...")
        input("> ")

    def get_game_file(self) -> bool:
        while True:
            if self.config["clear_terminal"]:
                text_display.clear_terminal()
            print("Input the file path of your game to get started.")
            print(f"Current working directory: {os.getcwd()}")
            print("[0] Cancel")
            file_path = input("> ")
            if file_path == "0":
                return False
            else:
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        try:
                            self.game_data = json.load(file)
                            return True
                        except json.decoder.JSONDecodeError:
                            print("There's a formatting error in the quest file you requested.")
                            input("> ")
                except FileNotFoundError:
                    print("The file you requested does not exist.")
                    input("> ")

    def run(self) -> None:
        """Runs main game loop"""
        while True:
            primary_options = {"1":"Load Game", "0":"Exit"}
            primary_menu = text_display.ListMenu("Welcome to Micro Quest!", primary_options)
            selection = primary_menu.get_input(self.config["clear_terminal"])
            match selection:
                case "0":
                    return
                case "1":
                    if self.get_game_file():
                        self.play_game()
                    else:
                        continue

if __name__ == "__main__":
    game = Game()
    game.run()
