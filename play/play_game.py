import os
import json

clear_after_menu = True
def clear_terminal() -> None:
    print("\033[2J\033[H", end="")

class ListMenu:
    """Represents a menu allowing selection from a list of items.

    Attributes:
        title (str): The title of the menu as a string. Will be displayed one
            line above the list of options.
        options (dict[str, str]): Dictionary containing each of the selectable
            options and their indices as keys.
    """

    def __init__(self, title: str, options: dict[str, str]) -> None:
        self.title = title
        self.options = options

    def show(self) -> None:
        """Clears terminal if enabled, then prints menu to terminal."""
        if clear_after_menu:
            clear_terminal()
        print(self.title)
        for key, option in self.options.items():
            print(f"[{key}] {option}")

    def get_input(self) -> str:
        """Displays menu until user inputs valid input.
        
        Returns:
            user selection as a string matching a key in the dictionary.
        """
        while True:
            self.show()
            selection = input("> ")
            selection = selection.lower().strip()
            if selection in self.options:
                return selection

class Game:
    """Main game class."""

    def __init__(self) -> None:
        self.game_data: dict = None

    def get_game_file(self) -> None:
        while True:
            clear_terminal()
            print("Input the file path of your game to get started.")
            print(f"Current working directory: {os.getcwd()}")
            print("[0] Cancel")
            file_path = input("> ")
            if file_path == "0":
                return
            else:
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        try:
                            self.game_data = json.load(file)
                            return
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
            primary_menu = ListMenu("Welcome to Micro Quest!", primary_options)
            selection = primary_menu.get_input()
            match selection:
                case "0":
                    return
                case "1":
                    self.get_game_file()

if __name__ == "__main__":
    game = Game()
    game.run()
